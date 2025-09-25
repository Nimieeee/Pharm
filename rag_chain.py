# rag_chain.py

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq  # <- Groq wrapper for LangChain

def build_rag_chain(vectorstore, llm=None, model="llama-3.1-8b-instant"):
    retriever = vectorstore.as_retriever()
    
    # fallback: if no llm passed, use Groq
    if llm is None:
        llm = ChatGroq(
            model=model,
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")  # make sure env var is set
        )
    
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

Context:
{context}

Question:
{question}

Answer:"""

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template
    )

    # Return just the retriever + prompt — not bound to any LLM
    return {"retriever": retriever, "prompt": prompt}
