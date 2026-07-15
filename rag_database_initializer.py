'''
Must run this file ONCE and must be ONLINE also add your PDF Files Folder directory below named SUPPLEMENTARY_FILE_PATH


Instantiation Pipeline:
1) Full-body validated base corpus 
2) User can choose to add local, specific pdf files
2) all pdfs are cleaned and added with metadata stored for citations
3) Chunking is performed such that semantic structrue is maintained without duplicate data
4) Chunks are embedded into vectorized database with metadata stored
'''

SUPPLEMENTARY_FILE_PATH = str('copy the name of your folder directory here; make sure all fiels are PDFs :) enjoy! ')


pip install langchain-huggingface sentence-transformers
pip install chromadb


import os, re, sys
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pypdf import PdfReader


def pdf_cleaner(file_path):
    """Take a folder path, return {filename: full_cleaned_text} for every PDF in it."""
    
    docs = {}
    for name in os.listdir(file_path):
        if not name.lower().endswith(".pdf"):
            continue
        reader = PdfReader(os.path.join(file_path, name))
        text = ""
        for page in reader.pages:
            raw = page.extract_text() or ""
            raw = re.sub(r"-\n", "", raw)
            text += re.sub(r"\s+", " ", raw).strip() + " "
        docs[name] = text.strip()
    return docs
    
def add_documents(old_documents, new_documents):
    """Merge new {filename: text} into the existing dict, skipping duplicates."""
    combined = dict(old_documents)
    for filename, text in new_documents.items():
        if filename in combined:
            print(f"skipping (already present): {filename}")
            continue
        combined[filename] = text
    return combined

def semantic_chunker(documents):
    """documents: {filename: text} -> list of chunk Documents."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    text_splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=70.0)

    all_chunks = []
    for filename, text in documents.items():
        chunks = text_splitter.create_documents(
            [text],
            metadatas=[{"filename": filename}])
        for chunk_index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = chunk_index
        all_chunks.extend(chunks)
    return all_chunks

def chunk_embedder(all_chunks, persist_dir="./index"):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        all_chunks,
        embeddings,
        persist_directory=persist_dir)   # written to disk so you don't re-embed
    return vectorstore



BASE_FILE_PATH = "./corpus_v3"

base_corpus = pdf_cleaner(BASE_FILE_PATH)
#list_of_documents = add_documents(base_corpus, pdf_cleaner(SUPPLEMENTARY_FILE_PATH)) delete # at beginning of this line if usign suppplementary folder
#chunks = semantic_chunker(list_of_documents) #delete # at beginning of this line if usign suppplementary folder
chunks = semantic_chunker(base_corpus) #delete this line if supplenmentary folder exists
vectorized_database = chunk_embedder(chunks)