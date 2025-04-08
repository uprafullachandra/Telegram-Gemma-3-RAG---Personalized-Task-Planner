import requests
import json

def generate_text(prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Generate text using Ollama's local Gemma 3:1b model"""
    # Ollama API endpoint for local models
    url = "http://localhost:11434/api/generate"
    
    # Prepare the request payload
    payload = {
        "model": "gemma3:1b",  # Using local Gemma 3:1b model
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    }
    
    try:
        # Make the request to Ollama
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Extract the generated text from the response
        result = response.json()
        return result.get("response", "No response generated")
    
    except requests.exceptions.RequestException as e:
        print(f"Error generating text: {e}")
        return f"Error: Could not generate response. Make sure Ollama is running with 'ollama run gemma3:1b'."

# Quick test
if __name__ == "__main__":
    test_prompt = "What is the capital of France?"
    print(f"Testing Gemma with prompt: {test_prompt}")
    response = generate_text(test_prompt)
    print(f"Response: {response}")