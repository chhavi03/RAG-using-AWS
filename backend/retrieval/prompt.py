"""
prompt.py
Builds the LLM prompt from a list of chunk metadata dicts returned by retriever.py.
"""


def build_prompt(chunks: list[dict], question: str) -> str:
    """
    Formats each retrieved chunk with its source reference so the LLM can cite it,
    then appends the user question.
    """
    context_lines = []
    for i, chunk in enumerate(chunks, start=1):
        label = (
            f"[Source {i} | {chunk['doc_name']} | Page {chunk['page']}]"
        )
        context_lines.append(f"{label}\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_lines)

    return f"""You are a helpful document assistant.
Answer the question ONLY based on the provided context below.
If the answer is not contained in the context, say "I don't have enough information to answer that."

At the very end of your response, provide exactly 3 short suggested follow-up questions that the user could ask next to learn more.
Format them exactly like this:
SUGGESTED_QUESTIONS:
- [Question 1]
- [Question 2]
- [Question 3]

Context:
{context}

Question:
{question}

Answer:"""
