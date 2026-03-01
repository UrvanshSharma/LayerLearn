import ollama

def explain_text(text, user_prompt="Explain this simply"):

    prompt = f"""
You are a study assistant.

Instruction: {user_prompt}

Text:
{text}
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]