# State-of-the-art Retrieval Augmented Generation (RAG) for the RAD-AI Embedded product.


Instructions:

1) in your terminal install these dependencies by running 
"pip install langchain-huggingface langchain-community langchain-experimental sentence-transformers chromadb pypdf"

2) change the SUPPLEMENTARY_FILE_PATH variable to your folder in 'rag_database_initializer'
3) run the rag_database_initializer.py file ONCE, and ONLINE
    this will take a while, but this is a one-time set up; otherwise this runs offline
4) That's it! Enjoy!



RAG Pipeline:
Vectorized Database Instantiation (done once):
1) Full-body validated base corpus 
2) User can choose to add local, specific pdf files
2) all pdfs are cleaned and added with metadata stored for citations
3) Chunking is performed such that semantic structrue is maintained without duplicate data
4) Chunks are embedded into vectorized database with metadata stored


Query Pipeline (done every query):
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
embedding respects semantic strcutre during chunking


query embedding type is flexible determined by RAD-AI embedded hardware constraints
reranking step allows for better ranking due to full-attention block rather than prue emedding cosine similarity
introduced refusal lower bound


benchmarks support the new RAG is a higher accuracy, higher quality, lower token and latency version.