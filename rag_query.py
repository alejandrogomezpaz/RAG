'''
Query Pipeline:
1.1) pre-filtering deterministic lookup bypass
1.2) misc pre-filtering
2) Query embedding (choose: Exact query, Hypothetical Document Embedding, Multi-Query Union)
3.1) Top-k-search
3.2) re-ranking top-k
3.3) similarity lower bound threshold refusal trigger
4) Build context + system prompt for LLM input
'''
import sys, math
sys.path.append(r"/Users/alejandrogomez-paz/Desktop/RAG/local_LLM") #make this the emebedded LLM once on hardware
from rad_ai import query

from sentence_transformers import CrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PERSIST_DIR = "./index"                                   # must match File 1
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True})

vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

def exact_query(q):
    '''returns query; here so i rememeber this basic method'''

    return q

def HyDE_query(q):
    '''HyDE: instead of embedding the raw question, ask the LLM to draft a hypothetical answer passage,
    then embed and retrieve on that. The fake answer sits closer in vector space to real answer chunks than a short
    question does, improving recall. Trade-off: adds one LLM call and can drift if the model hallucinates off-topic. '''

    return query((f"Write a short factual passage that would answer:\n{q}"))

def MQU(q, num):
    ''' Multi-Query Union: use the LLM to paraphrase the question into several variants, retrieve top-k for each (plus the original),
    and union the results (deduped). Covers vocabulary mismatch by hitting the index from multiple phrasings,
    so relevant chunks a single wording would miss get pulled in. Trade-off: more searches + one LLM call;
    re-ranking afterward trims the wider candidate set back down. 
    '''

    out = query(f"Rewrite the question in {num} different ways, one per line:\n{q}")
    variants = [v.strip("-• ").strip() for v in out.splitlines() if v.strip()]
    return [q] + variants[:num]

def query_embedding(q, strategy="exact", num=3):
    '''Step 2 dispatch: route the query through the chosen embedding strategy.
    Always returns a list[str] so downstream top-k search can iterate uniformly.'''
    if strategy == "exact":
        return [exact_query(q)]
    elif strategy == "hyde":
        return [HyDE_query(q)]        # wrap single string in a list
    elif strategy == "mqu":
        return MQU(q, num)            # already a list
    else:
        raise ValueError(f"unknown strategy: {strategy}")

def top_k_search(queries, vectorized_db, k1):
    ''' finds the k1 most semantically similar chunks for each query variant, unions them,
        and keeps the best similarity per chunk (dedup). needed because mqu/hyde can hand us
        multiple phrasings -- exact just passes a 1-element list so this still works'''
    best = {}   # (filename, chunk_index) -> (doc, similarity)
    for q in queries:
        for doc, dist in vectorized_db.similarity_search_with_score(q, k=k1):
            sim = 1.0 - dist
            key = (doc.metadata.get("filename"), doc.metadata.get("chunk_index"))
            if key not in best or sim > best[key][1]:
                best[key] = (doc, sim)   # keep the higher-scoring hit for this chunk

    return sorted(best.values(), key=lambda x: x[1], reverse=True)[:k1]

REFUSAL_THRESHOLD = 0.2
RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")   # load once, module level

def rerank_top_k(q, top_chunks, k1, k2):
    '''takes the k1 most similar chunks and reranks to k2 chunks using a higher-cost,
        higher-accuracy similarity search where k2 < k1 (~20 -> 3-5)'''
    candidates = top_chunks[:k1]
    scores = RERANKER.predict([(q, doc.page_content) for doc, _ in candidates])
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [(doc, float(s)) for (doc, _), s in ranked[:k2]]

def build_context(retrieved_chunks):
    '''formats the surviving chunks into one text block for the prompt. each chunk is tagged
       with its source file + chunk index so the LLM has an exact label to cite from --
       [filename #index] matches the citation format the system prompt asks for'''
    
    context_blocks = []
    for doc, i in retrieved_chunks:
        filename = doc.metadata.get('filename')
        chunk_index = doc.metadata.get('chunk_index')
        composite_tag = f'[filename: {filename}, chunk_index: {chunk_index}]'
        context_blocks.append(f'{composite_tag}\n{doc.page_content}')

    context = "\n\n".join(context_blocks)

    return context

def retrieve(q, strat, num, k1, k2):

    embedded_query = query_embedding(q, strategy = str(strat), num = num)
    top_k_chunks = top_k_search(embedded_query, vectorstore, k1)
    retrieved_chunks = rerank_top_k(q, top_k_chunks, k1, k2)
    
    if not retrieved_chunks:
        return "You may only answer: 'I cannot answer this question'"

    top_score = 1 / (1 + math.exp(-retrieved_chunks[0][1]))  
    if top_score < REFUSAL_THRESHOLD:
        refusal_prompt = "You may only answer: 'I cannot answer this question'"
        return refusal_prompt

    else:
        context = build_context(retrieved_chunks)
        system_prompt = f"""You answer strictly from the provided context chunks. Rules:
            Use only facts in the context. Never add outside knowledge.
            If the context doesn't answer the question, say: "Not found in the provided sources."
            Cite the source after each claim exactly as bracketed in the context, example: [filename: report.pdf, chunk_index: 3]
            Be concise. No preamble, no repetition of the question. Chunks: {context}"""
        return system_prompt
    