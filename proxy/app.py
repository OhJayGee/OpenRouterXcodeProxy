import requests
import json
import os
import re
import fnmatch
import time
import signal
import sys
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
        # Forward all headers except Host and Content-Length (let requests recalculate)
        headers = dict(request.headers)
        if 'Host' in headers:
            del headers['Host']
        if 'Content-Length' in headers:
            del headers['Content-Length']
        
        # Set correct Host for OpenRouter API
        target_host = "openrouter.ai"
        headers['Host'] = target_host
        
        url = f"{OPENROUTER_API_URL}/api/v1/chat/completions"
        body = request.json
        
        # Debug: Check if body is too large or has issues
        print(f"Request body size: {len(str(body))} characters")
        print(f"Model in request: {body.get('model', 'MISSING')}")
        
        log_request(url, headers, "POST", body)
        
        # Set stream=True to handle streaming responses  
        stream = body.get('stream', False)
        
        # Disable SSL verification if environment variable is set
        verify_ssl = os.environ.get('DISABLE_SSL_VERIFY') != 'true'
        response = requests.post(url, headers=headers, json=body, stream=stream, verify=verify_ssl)
        
        # Handle OpenRouter errors by formatting them as chat completion responses
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', f'HTTP {response.status_code} error')
                
                # Format error to match exact working response format
                error_response = {
                    "choices": [{
                        "finish_reason": "stop",
                        "index": 0,
                        "logprobs": None,
                        "message": {
                            "content": f"Model unavailable: {error_message}",
                            "refusal": None,
                            "role": "assistant"
                        }
                    }],
                    "created": int(time.time()),
                    "id": f"gen-{int(time.time())}-error",
                    "model": body.get('model', 'unknown'),
                    "object": "chat.completion",
                    "usage": {
                        "completion_tokens": 10,
                        "prompt_tokens": 10,
                        "total_tokens": 20
                    }
                }
                
                print(f"Returning formatted error response: {error_message}")
                print("Full error response JSON:")
                print(json.dumps(error_response, indent=2))
                
                # If original request was streaming, return streaming format
                original_stream = stream
                if original_stream:
                    # Format as streaming chunk for SSE
                    chunk_response = {
                        "id": f"gen-{int(time.time())}-error",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": body.get('model', 'unknown'),
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": f"Model unavailable: {error_message}"
                            },
                            "finish_reason": "stop",
                            "logprobs": None
                        }]
                    }
                    
                    def generate_error_stream():
                        yield f"data: {json.dumps(chunk_response)}\n"
                        yield f"data: [DONE]\n"
                    
                    return Response(generate_error_stream(), 
                                    status=200,
                                    content_type='text/event-stream')
                else:
                    return jsonify(error_response), 200
                
            except:
                # Fallback if we can't parse the error
                pass
        
        response.raise_for_status()
        
        # Log the raw response from OpenRouter
        print(f"--- OpenRouter Response Status: {response.status_code} ---")
        print(f"Response Headers: {dict(response.headers)}")
        print("--- End of OpenRouter Response Log ---\n")
        
        if stream:
            def generate():
                for line in response.iter_lines(decode_unicode=True):
                    # Skip "OPENROUTER PROCESSING" messages, it breaks Xcode Intelligence
                    if line and ": OPENROUTER PROCESSING" not in line:
                        # Filter out OpenRouter-specific fields from streaming responses
                        if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                            try:
                                data_content = line[6:]  # Remove 'data: ' prefix
                                chunk = json.loads(data_content)
                                
                                # Remove OpenRouter-specific top-level fields
                                chunk.pop('provider', None)
                                
                                # Clean up usage object in streaming chunks
                                if 'usage' in chunk:
                                    usage = chunk['usage']
                                    usage.pop('prompt_tokens_details', None)
                                
                                # Clean up choices in streaming chunks
                                if 'choices' in chunk:
                                    for choice in chunk['choices']:
                                        choice.pop('native_finish_reason', None)
                                        
                                        # Clean up delta message object
                                        if 'delta' in choice:
                                            delta = choice['delta']
                                            delta.pop('reasoning', None)
                                            delta.pop('reasoning_details', None)
                                
                                # Reconstruct the line
                                yield f"data: {json.dumps(chunk)}\n"
                            except (json.JSONDecodeError, KeyError):
                                # If parsing fails, pass through unchanged
                                yield f"{line}\n"
                        else:
                            yield f"{line}\n"

            return Response(stream_with_context(generate()), 
                            status=response.status_code,
                            content_type=response.headers.get('Content-Type', 'text/event-stream'))
        else:
            openrouter_response = response.json()
            
            # Log raw OpenRouter response for debugging
            print("Raw OpenRouter Response (non-streaming):")
            print(json.dumps(openrouter_response, indent=2))
            print("--- End of Raw Response ---\n")
            
            # Transform OpenRouter response to OpenAI-compatible format
            # Remove OpenRouter-specific fields that might confuse Xcode
            if 'choices' in openrouter_response:
                for choice in openrouter_response['choices']:
                    # Remove OpenRouter-specific fields from choices
                    choice.pop('native_finish_reason', None)
                    
                    # Clean up message object
                    if 'message' in choice:
                        message = choice['message']
                        # Remove OpenRouter-specific message fields
                        message.pop('reasoning', None)
                        message.pop('reasoning_details', None)
            
            # Remove OpenRouter-specific top-level fields
            openrouter_response.pop('provider', None)
            
            # Clean up usage object to remove OpenRouter-specific fields
            if 'usage' in openrouter_response:
                usage = openrouter_response['usage']
                usage.pop('prompt_tokens_details', None)
            
            # Log filtered response being sent to Xcode
            print("Filtered Response being sent to Xcode:")
            print(json.dumps(openrouter_response, indent=2))
            print("--- End of Filtered Response ---\n")
            
            return openrouter_response, response.status_code
    
    except Exception as e:
        print(f"ERROR in chat_completions: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

import os

# ...

def signal_handler(sig, frame):
    print('\n\nShutting down OpenRouter proxy gracefully...')
    print('Goodbye!')
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    from waitress import serve
    port = int(os.environ.get('PORT', 8080))
    
    print(f"Starting OpenRouter proxy on port {port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        serve(app, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print('\n\nShutting down OpenRouter proxy gracefully...')
        print('Goodbye!')
        sys.exit(0)
