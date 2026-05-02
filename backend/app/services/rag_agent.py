import os
from dotenv import load_dotenv
from openai import OpenAI

from app.services.vector_store import similarity_search_with_score
from app.services.embeddings import model

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 🔒 Guardrail Prompt
STRICT_PROMPT = """
You are a strict document-based question answering system.

RULES:
1. Answer ONLY using the provided context
2. Do NOT use outside knowledge
3. If the answer is not present in the context, respond EXACTLY:
   "I cannot answer from the provided documents."
4. Be concise and factual

Context:
{context}

Question:
{question}

Answer:
"""


# 🔒 Post-validation
def is_answer_supported(answer, contexts):
    answer_words = set(answer.lower().split())

    for ctx in contexts:
        ctx_words = set(ctx.lower().split())
        overlap = answer_words.intersection(ctx_words)

        if len(overlap) / (len(answer_words) + 1) > 0.2:
            return True

    return False


def generate_answer(question, selected_files=None):
    try:
        # 🔹 Retrieve (with optional file filter)
        results = similarity_search_with_score(
            question,
            get_embedding_fn=lambda q: model.encode(q),
            k=3,
            filter_files=selected_files
        )

        print("\n🔍 RAW RESULTS:", results)

        # 🔒 Threshold
        SIMILARITY_THRESHOLD = 0.3

        filtered_results = [
            r for r in results if r[1] >= SIMILARITY_THRESHOLD
        ]

        print("✅ FILTERED RESULTS:", filtered_results)

        # 🔁 Fallback if nothing passes threshold
        if not filtered_results and results:
            filtered_results = [results[0]]

        if not filtered_results:
            return {
                "answer": "I cannot answer from the provided documents.",
                "sources": []
            }

        # 🔹 Extract context + sources
        contexts = [r[0]["page_content"] for r in filtered_results]

        sources = list(set([
            r[0]["metadata"].get("source", "unknown")
            for r in filtered_results
        ]))

        combined_context = "\n\n".join(contexts)

        # 🔹 Prompt
        prompt = STRICT_PROMPT.format(
            context=combined_context,
            question=question
        )

        # 🔹 LLM call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()

        print("💬 LLM ANSWER:", answer)

        # 🔒 Validate answer
        if not is_answer_supported(answer, contexts):
            return {
                "answer": "I cannot answer from the provided documents.",
                "sources": []
            }

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {
            "answer": "Error processing request.",
            "error": str(e),
            "sources": []
        }