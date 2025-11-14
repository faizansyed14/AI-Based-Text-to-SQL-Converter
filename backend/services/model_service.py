"""Service for handling different LLM models (OpenAI and Ollama)"""
import os
import json
import requests
import logging
from typing import List, Optional
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Supported models (llama3.2:1b is best for SQL generation tasks)
SUPPORTED_MODELS = {
    "gpt-4o-mini": {"provider": "openai", "name": "gpt-4o-mini"},
    "llama3.2:1b": {"provider": "ollama", "name": "llama3.2:1b"},
}

def generate_with_openai(messages: List[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Generate SQL query using OpenAI"""
    try:
        logger.info("🔵 [GPT-4o-mini] Making API call to OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content.strip()
        logger.info("✅ [GPT-4o-mini] Response received from OpenAI")
        return result
    except Exception as e:
        logger.error(f"❌ [GPT-4o-mini] OpenAI error: {str(e)}")
        raise Exception(f"OpenAI error: {str(e)}")

def generate_with_ollama(model_name: str, messages: List[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Generate SQL query using Ollama (Llama/Qwen models)"""
    try:
        logger.info(f"🟢 [Ollama/{model_name}] Making API call to Ollama service at {OLLAMA_BASE_URL}...")
        url = f"{OLLAMA_BASE_URL}/api/chat"
        
        # Convert messages format for Ollama
        ollama_messages = []
        for msg in messages:
            role = msg["role"]
            # Ollama supports system, user, and assistant roles
            ollama_messages.append({
                "role": role,
                "content": msg["content"]
            })
        
        payload = {
            "model": model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "top_k": 40,
                "num_ctx": 2048,  # Reduced context for faster processing
                "repeat_penalty": 1.1,
                "numa": True  # Enable NUMA optimization
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)  # Increased timeout for complex queries
        response.raise_for_status()
        
        result = response.json()
        content = result.get("message", {}).get("content", "").strip()
        logger.info(f"✅ [Ollama/{model_name}] Response received from Ollama")
        return content
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ [Ollama/{model_name}] Connection error: {str(e)}")
        raise Exception(f"Ollama connection error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ [Ollama/{model_name}] Error: {str(e)}")
        raise Exception(f"Ollama error: {str(e)}")

def check_ollama_available() -> bool:
    """Check if Ollama service is available"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def check_model_available(model_name: str) -> bool:
    """Check if a specific model is available in Ollama"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            return model_name in model_names
        return False
    except:
        return False

def ensure_ollama_model(model_name: str) -> bool:
    """Ensure the specified model is available in Ollama"""
    try:
        # Check if model exists
        if check_model_available(model_name):
            return True
        
        # Pull the model if it doesn't exist
        url = f"{OLLAMA_BASE_URL}/api/pull"
        payload = {"name": model_name}
        response = requests.post(url, json=payload, timeout=600, stream=True)
        response.raise_for_status()
        
        # Stream the response to show progress
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if data.get("status") == "success":
                        return True
                except:
                    pass
        return True
    except Exception as e:
        print(f"Warning: Could not ensure Ollama model {model_name}: {e}")
        return False

def generate_sql_with_model(model: str, messages: List[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Generate SQL query using the specified model"""
    if model not in SUPPORTED_MODELS:
        raise Exception(f"Unsupported model: {model}. Supported models: {', '.join(SUPPORTED_MODELS.keys())}")
    
    model_config = SUPPORTED_MODELS[model]
    provider = model_config["provider"]
    model_name = model_config["name"]
    
    logger.info(f"📊 Model Selection: Requested={model}, Provider={provider}, Model={model_name}")
    
    if provider == "openai":
        logger.info("🔵 Using OpenAI GPT-4o-mini")
        return generate_with_openai(messages, temperature, max_tokens)
    elif provider == "ollama":
        logger.info(f"🟢 Using Ollama {model_name}")
        if not check_ollama_available():
            raise Exception("Ollama service is not available. Please ensure Ollama is running.")
        return generate_with_ollama(model_name, messages, temperature, max_tokens)
    else:
        raise Exception(f"Unknown provider for model: {model}")

