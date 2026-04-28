import requests

def ask_llm(question: str, context: str) -> str:
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-large",
            headers={},
            json={
                "inputs": f"Answer the question based on context.\n\nContext:\n{context}\n\nQuestion:\n{question}"
            },
            timeout=60
        )

        result = response.json()

        if isinstance(result, list):
            return result[0]["generated_text"]

        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"