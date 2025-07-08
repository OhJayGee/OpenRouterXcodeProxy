import requests
import json
import os
import re
import fnmatch
from flask import Flask, request, jsonify, Response, stream_with_context

app = Flask(__name__)
OPENROUTER_API_URL = "https://openrouter.ai"

def log_request(url, headers, method, body=None):
    """Log request details for debugging"""
    print(f"\n--- Sending {method} request to {url} ---")
    print("Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    if body:
        print("Body:")
        print(json.dumps(body, indent=2))
    print("--- End of request ---\n")

@app.route('/v1/models', methods=['GET'])
def get_models():
    """Return models in OpenAI format, optionally filtered by filter-models.txt"""
    try:
        # Forward all headers except Host
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        
        # Set correct Host for OpenRouter API
        target_host = "openrouter.ai"
        headers['Host'] = target_host
        
        # Log and send request
        url = f"{OPENROUTER_API_URL}/api/v1/models"
        log_request(url, headers, "GET")
        
        # Disable SSL verification if environment variable is set
        verify_ssl = os.environ.get('DISABLE_SSL_VERIFY') != 'true'
        response = requests.get(url, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        openrouter_data = response.json()
        
        # Load allowed models from filter file
        allowed_models = set()
        filter_path = os.environ.get('MODEL_FILTER_FILE')

        if filter_path is None:
            # If env var is not set, check for default file
            if os.path.exists('filter-models.txt'):
                filter_path = 'filter-models.txt'
        
        if filter_path:
            print(f"Attempting to use model filter file: {filter_path}")
            if os.path.exists(filter_path):
                print(f"Filter file found at {filter_path}.")
                try:
                    with open(filter_path, 'r') as f:
                        for line in f:
                            model_id = line.strip()
                            if model_id:  # Skip empty lines
                                allowed_models.add(model_id) 
                    print(f"Loaded {len(allowed_models)} models from filter file.")
                except Exception as e:
                    print(f"Error reading model filter file at {filter_path}: {e}")
            else:                
                print(f"Filter file NOT found at {filter_path}.")       
        
        # Filter models if we have entries
        if allowed_models: 
            print("Applying model filter.")
            # Convert wildcard patterns to regex patterns
            regex_patterns = [fnmatch.translate(pattern) for pattern in allowed_models]
            openrouter_data["data"] = [
                model for model in openrouter_data["data"]
                if any(re.match(pattern, model["id"]) for pattern in regex_patterns)
            ]
        
        # Transform to OpenAI format
        openai_models = {
            "object": "list",
            "data": [
                {
                    "id": model["id"],
                    "object": "model",
                    "created": model["created"],
                    "owned_by": model["id"].split("/")[0]  # Extract provider prefix
                } 
                for model in openrouter_data["data"]
            ]
        }
        return jsonify(openai_models)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Proxy chat completions to OpenRouter"""
    try:
        # Forward all headers except Host
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        
        # Set correct Host for OpenRouter API
        target_host = "openrouter.ai"
        headers['Host'] = target_host
        
        url = f"{OPENROUTER_API_URL}/api/v1/chat/completions"
        body = request.json
        log_request(url, headers, "POST", body)
        
        # Set stream=True to handle streaming responses
        stream = body.get('stream', False)
        
        # Disable SSL verification if environment variable is set
        verify_ssl = os.environ.get('DISABLE_SSL_VERIFY') != 'true'
        response = requests.post(url, headers=headers, json=body, stream=stream, verify=verify_ssl)
        response.raise_for_status()
        
        if stream:
            def generate():
                for line in response.iter_lines(decode_unicode=True):
                    # Skip "OPENROUTER PROCESSING" messages, it breaks Xcode Intelligence
                    if line and ": OPENROUTER PROCESSING" not in line:
                        yield f"{line}\n"

            return Response(stream_with_context(generate()), 
                            status=response.status_code,
                            content_type=response.headers.get('Content-Type', 'text/event-stream'))
        else:
            return response.json(), response.status_code
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os

# ...

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 8080))
    serve(app, host='0.0.0.0', port=port)
