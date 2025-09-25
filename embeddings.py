from langchain.embeddings import HuggingFaceEmbeddings

def get_embeddings():
    """
    Returns a HuggingFace sentence-transformers embedding model
    for use in the RAG pipeline.
    """
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    return HuggingFaceEmbeddings(model_name=model_name)
