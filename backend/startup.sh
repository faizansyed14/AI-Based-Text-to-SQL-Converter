#!/bin/sh
# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in 1 2 3 4 5 6 7 8 9 10; do
    if wget --quiet --tries=1 --spider http://ollama:11434/api/tags 2>/dev/null || curl -f http://ollama:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Attempt $i: Ollama not ready yet, waiting..."
    sleep 2
done

# Ensure Ollama models are available
echo "Ensuring Ollama models are available..."
python -c "
import requests
import time
import sys

ollama_url = 'http://ollama:11434'
models_to_install = ['llama3.2:1b']

for model_name in models_to_install:
    print(f'Checking model {model_name}...')
    try:
        # Check if model exists
        response = requests.get(f'{ollama_url}/api/tags', timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            if model_name in model_names:
                print(f'Model {model_name} already exists')
                continue
    except Exception as e:
        print(f'Error checking models: {e}')

    # Pull the model
    print(f'Pulling model {model_name}...')
    try:
        response = requests.post(
            f'{ollama_url}/api/pull',
            json={'name': model_name},
            timeout=600,
            stream=True
        )
        response.raise_for_status()
        
        # Stream the response
        for line in response.iter_lines():
            if line:
                try:
                    data = line.decode('utf-8')
                    if 'status' in data or 'completed' in data.lower():
                        print(data)
                except:
                    pass
        
        print(f'Model {model_name} pulled successfully!')
    except Exception as e:
        print(f'Warning: Could not pull model {model_name}: {e}')
        print('Continuing anyway...')
"

# Warmup the model for faster first response
echo "Warming up Ollama model..."
python -c "
import requests
import time
ollama_url = 'http://ollama:11434'
try:
    print('Preloading llama3.2:1b model...')
    response = requests.post(
        f'{ollama_url}/api/generate',
        json={'model': 'llama3.2:1b', 'prompt': 'SELECT', 'stream': False, 'options': {'num_predict': 5}},
        timeout=15
    )
    if response.status_code == 200:
        print('Model preloaded successfully!')
    else:
        print('Model preload skipped (will load on first request)')
except Exception as e:
    print(f'Model preload skipped: {e}')
"

# Start the FastAPI server
echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

