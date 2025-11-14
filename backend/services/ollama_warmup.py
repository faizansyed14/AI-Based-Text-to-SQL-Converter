"""Warmup script to preload Ollama model for faster first response"""
import os
import requests
import time

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = "llama3.2:1b"

def warmup_model():
    """Preload the model to avoid cold start delays"""
    try:
        print(f"Warming up {MODEL_NAME}...")
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": "SELECT",
            "stream": False,
            "options": {
                "num_predict": 10  # Very short to just load the model
            }
        }
        start = time.time()
        response = requests.post(url, json=payload, timeout=10)
        elapsed = time.time() - start
        if response.status_code == 200:
            print(f"Model warmed up in {elapsed:.2f}s")
            return True
        return False
    except Exception as e:
        print(f"Warmup failed: {e}")
        return False

if __name__ == "__main__":
    warmup_model()

