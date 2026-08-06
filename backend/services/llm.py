import os
from groq import Groq
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path, encoding="utf-8")

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

def answer_question(
    question: str,
    context: str,
) -> str:

        prompt = f"""
    You are an expert legal contract assistant.

    Rules:
    1. Answer only from the provided contract.
    2. Do not invent clauses.
    3. Quote the relevant clause numbers when possible.
    4. If multiple clauses are relevant, explain how they relate.
    5. If the answer is not present, say so.

    Contract Context:
    {context}

    Question:
    {question}  
    """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise legal analyst. Always respond in 2-3 plain English sentences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.3
        )

        return response.choices[0].message.content