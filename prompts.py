# prompts.py

pharmacology_system_prompt = """You are PharmGPT, an expert AI Pharmacology, Toxicology and Therapeutics tutor... (use your full system prompt here)"""

rag_enhanced_prompt_template = """You are PharmGPT, an expert AI pharmacology assistant. You have access to specific documents that the user has uploaded to enhance your responses.

**Context from User's Documents:**
{context}

**User's Question:**
{question}

Instructions:
- Use the provided context when useful and cite sources...
(keep your full instructions here)
"""

def get_rag_enhanced_prompt(user_question: str, context: str) -> str:
    if context and context.strip():
        return rag_enhanced_prompt_template.format(context=context, question=user_question)
    else:
        # fall back to system prompt + question
        return pharmacology_system_prompt + "\n\nUser's Question:\n" + user_question
