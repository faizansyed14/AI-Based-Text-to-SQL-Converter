"""Service for handling different LLM models (OpenAI GPT models only)"""
import os
import logging
from typing import List
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supported GPT models for SQL generation
# Recommended order: gpt-4o-mini (fastest, cost-effective) > gpt-4o (balanced) > gpt-4-turbo (more accurate) > gpt-4 (most accurate, slower)
SUPPORTED_MODELS = {
    "gpt-4o-mini": {"provider": "openai", "name": "gpt-4o-mini", "description": "Fastest & Most Cost-Effective"},
    "gpt-4o": {"provider": "openai", "name": "gpt-4o", "description": "Balanced Speed & Accuracy"},
    "gpt-4-turbo": {"provider": "openai", "name": "gpt-4-turbo", "description": "High Accuracy"},
    "gpt-4": {"provider": "openai", "name": "gpt-4", "description": "Most Accurate (Slower)"},
}

def generate_with_openai(model_name: str, messages: List[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Generate SQL query using OpenAI GPT models"""
    try:
        logger.info(f"🔵 [{model_name}] Making API call to OpenAI...")
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"✅ [{model_name}] Response received from OpenAI")
        return result
    except Exception as e:
        logger.error(f"❌ [{model_name}] OpenAI error: {str(e)}")
        raise Exception(f"OpenAI error: {str(e)}")


def generate_sql_with_model(model: str, messages: List[dict], temperature: float = 0.3, max_tokens: int = 500) -> str:
    """Generate SQL query using the specified GPT model"""
    if model not in SUPPORTED_MODELS:
        raise Exception(f"Unsupported model: {model}. Supported models: {', '.join(SUPPORTED_MODELS.keys())}")
    
    model_config = SUPPORTED_MODELS[model]
    provider = model_config["provider"]
    model_name = model_config["name"]
    description = model_config.get("description", "")
    
    logger.info(f"📊 Model Selection: Requested={model}, Provider={provider}, Model={model_name} ({description})")
    
    if provider == "openai":
        logger.info(f"🔵 Using OpenAI {model_name}")
        return generate_with_openai(model_name, messages, temperature, max_tokens)
    else:
        raise Exception(f"Unknown provider for model: {model}")

