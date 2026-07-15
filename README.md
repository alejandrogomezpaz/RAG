# State-of-the-art Retrieval Augmented Generation (RAG) for the RAD-AI Embedded product.


Instructions:
In the rag_code.iphynb file:
1) run the first code chunk to install libraries
2) write the name of the folder of local PDF-only documents you would like to add
 to the FILE_PATH variable in the second code chunk
3) run the second code chunk
4) Thats it!



RAG Pipeline:
Instantiation:
1) Full-body validated base corpus 
2) User can choose to add local, specific pdf files
2) all pdfs are cleaned and added with metadata stored for citations
3) Chunking is performed such that semantic structrue is maintained without duplicate data
4) Chunks are embedded into vectorized database with metadata stored

Query Pipeline:
1.1) pre-filtering deterministic lookup bypass
1.2) misc pre-filtering
2) Query embedding (choose: Exact query, Hypothetical Document Embedding, Multi-Query Union)
3.1) Top-k-search
3.2) re-ranking top-k
3.3) similarity lower bound threshold refusal trigger
4) Build context + system prompt for LLM input



Improvements from prototype RAG:
corpus contains more, relevant documents
pipeline allows for user to add local docs seamlessly

prefiltering is performed
query embedding type is flexible determined by RAD-AI embedded hardware
reranking step allows for better ranking due to full-attention block
introduced refusal lower bound

benchmarks support the new RAG is a higher accuracy, higher quality, lower token and latency version.