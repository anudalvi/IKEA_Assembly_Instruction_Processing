import asyncio
import ollama
import base64
import os

async def test_qwen_vision():
    # Attempt to find an image in data/markdown_files
    # For now, let's just try to see if it responds to text at all with these options.
    model = "qwen3.5:2b"
    print(f"Testing model: {model}")
    
    # Try with current restrictive options
    print("\n--- Testing with current RESTRICTIVE options ---")
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": "What is in this image? Wait, I didn't send one yet, but do you respond?"}],
            options={
                "temperature": 0.1,
                "top_p": 0.1,
                "top_k": 10,
                "num_predict": 2048
            },
            format="json"
        )
        print(f"Response: '{response.message.content}'")
    except Exception as e:
        print(f"Error: {e}")

    # Try with relaxed options
    print("\n--- Testing with RELAXED options ---")
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": "What is in this image? Wait, I didn't send one yet, but do you respond?"}],
            options={
                "temperature": 0.7,
                # No top_p/top_k
            }
            # No format="json"
        )
        print(f"Response: '{response.message.content}'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_qwen_vision())
