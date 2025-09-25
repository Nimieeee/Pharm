# rag_chain.py
from typing import Any
try:
    from langchain.chains import ConversationalRetrievalChain
except Exception:
    ConversationalRetrievalChain = None

def build_rag_chain(retriever, llm, return_source_documents: bool = True) -> Any:
    if ConversationalRetrievalChain is None:
        raise ImportError("ConversationalRetrievalChain not available in this LangChain install.")
    return ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, return_source_documents=return_source_documents)
