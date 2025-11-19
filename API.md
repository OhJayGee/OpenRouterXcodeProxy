# API Documentation

Complete API reference for the OpenRouter Proxy for Xcode 26 Beta.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /v1/models](#get-v1models)
  - [POST /v1/chat/completions](#post-v1chatcompletions)
- [Data Formats](#data-formats)
- [Error Handling](#error-handling)
- [Response Transformations](#response-transformations)
- [Examples](#examples)

## Overview

The OpenRouter Proxy provides an OpenAI-compatible API that proxies requests to OpenRouter. All requests and responses are transformed to maintain compatibility with Xcode 26 Beta's AI integration.

## Base URL

```
http://localhost:8080
```

Or your configured host and port if different.

## Authentication

All API requests require an OpenRouter API key passed via the `Authorization` header.

### Format

```
Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE
```

### Getting an API Key

1. Visit [openrouter.ai](https://openrouter.ai/)
2. Sign up or log in
3. Navigate to [API Keys](https://openrouter.ai/keys)
4. Generate a new API key

## Endpoints

### GET /v1/models

Retrieves a list of available models in OpenAI-compatible format.

#### Request

```http
GET /v1/models HTTP/1.1
Host: localhost:8080
Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE
```

#### Request Parameters

None

#### Response

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "anthropic/claude-3.7-sonnet",
      "object": "model",
      "created": 1234567890,
      "owned_by": "anthropic"
    },
    {
      "id": "openai/gpt-4-turbo",
      "object": "model",
      "created": 1234567891,
      "owned_by": "openai"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always "list" |
| `data` | array | Array of model objects |
| `data[].id` | string | Model identifier (format: `provider/model-name`) |
| `data[].object` | string | Always "model" |
| `data[].created` | integer | Unix timestamp of model creation |
| `data[].owned_by` | string | Model provider (extracted from ID prefix) |

#### Model Filtering

Models can be filtered by creating a `filter-models.txt` file or setting the `MODEL_FILTER_FILE` environment variable. The filter supports:

- **Exact matches**: `anthropic/claude-3.7-sonnet`
- **Wildcard patterns**: `anthropic/*`, `openai/gpt-4*`, `*claude*`

**Example filter-models.txt:**

```text
# Specific models
anthropic/claude-3.7-sonnet
deepseek/deepseek-r1-0528:free

# Wildcard patterns
anthropic/claude-*4*
google/gemini-2.5*
openai/*
```

#### Example Request

```bash
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE"
```

#### Example Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "anthropic/claude-3.7-sonnet",
      "object": "model",
      "created": 1704067200,
      "owned_by": "anthropic"
    },
    {
      "id": "anthropic/claude-3.7-sonnet:thinking",
      "object": "model",
      "created": 1704067200,
      "owned_by": "anthropic"
    },
    {
      "id": "openai/gpt-4-turbo",
      "object": "model",
      "created": 1704067200,
      "owned_by": "openai"
    }
  ]
}
```

---

### POST /v1/chat/completions

Creates a chat completion using the specified model.

#### Request

```http
POST /v1/chat/completions HTTP/1.1
Host: localhost:8080
Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE
Content-Type: application/json

{
  "model": "anthropic/claude-3.7-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "stream": false
}
```

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model ID (e.g., "anthropic/claude-3.7-sonnet") |
| `messages` | array | Yes | Array of message objects |
| `messages[].role` | string | Yes | Message role: "system", "user", or "assistant" |
| `messages[].content` | string | Yes | Message content |
| `stream` | boolean | No | Enable streaming (default: false) |
| `temperature` | float | No | Sampling temperature (0.0-2.0, default: 1.0) |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `top_p` | float | No | Nucleus sampling parameter (0.0-1.0) |
| `frequency_penalty` | float | No | Frequency penalty (-2.0 to 2.0) |
| `presence_penalty` | float | No | Presence penalty (-2.0 to 2.0) |
| `stop` | string or array | No | Stop sequences |

#### Response (Non-streaming)

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "id": "gen-1234567890abcdef",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "anthropic/claude-3.7-sonnet",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### Response Fields (Non-streaming)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique completion ID |
| `object` | string | Always "chat.completion" |
| `created` | integer | Unix timestamp |
| `model` | string | Model used for completion |
| `choices` | array | Array of completion choices |
| `choices[].index` | integer | Choice index |
| `choices[].message` | object | The generated message |
| `choices[].message.role` | string | Always "assistant" |
| `choices[].message.content` | string | Generated text |
| `choices[].finish_reason` | string | Why generation stopped: "stop", "length", etc. |
| `usage` | object | Token usage information |
| `usage.prompt_tokens` | integer | Tokens in the prompt |
| `usage.completion_tokens` | integer | Tokens in the completion |
| `usage.total_tokens` | integer | Total tokens used |

#### Response (Streaming)

**Status Code:** `200 OK`

**Content-Type:** `text/event-stream`

**Response Format:** Server-Sent Events (SSE)

```
data: {"id":"gen-123","object":"chat.completion.chunk","created":1234567890,"model":"anthropic/claude-3.7-sonnet","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"gen-123","object":"chat.completion.chunk","created":1234567890,"model":"anthropic/claude-3.7-sonnet","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"gen-123","object":"chat.completion.chunk","created":1234567890,"model":"anthropic/claude-3.7-sonnet","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"gen-123","object":"chat.completion.chunk","created":1234567890,"model":"anthropic/claude-3.7-sonnet","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

#### Streaming Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique completion ID (same across chunks) |
| `object` | string | Always "chat.completion.chunk" |
| `created` | integer | Unix timestamp |
| `model` | string | Model used |
| `choices[].delta` | object | Incremental content |
| `choices[].delta.role` | string | Role (in first chunk only) |
| `choices[].delta.content` | string | Incremental text content |
| `choices[].finish_reason` | string | Null until final chunk, then reason |

#### Example Request (Non-streaming)

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful coding assistant."
      },
      {
        "role": "user",
        "content": "Write a hello world function in Python."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

#### Example Request (Streaming)

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-or-v1-YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
      {
        "role": "user",
        "content": "Count from 1 to 5."
      }
    ],
    "stream": true
  }'
```

---

## Data Formats

### Message Object

```json
{
  "role": "user",
  "content": "Your message here"
}
```

**Roles:**
- `system`: System-level instructions
- `user`: User input
- `assistant`: Assistant responses

### Choice Object

```json
{
  "index": 0,
  "message": {
    "role": "assistant",
    "content": "Response text"
  },
  "finish_reason": "stop",
  "logprobs": null
}
```

**Finish Reasons:**
- `stop`: Natural completion
- `length`: Max tokens reached
- `content_filter`: Content filtered
- `tool_calls`: Tool/function called (not currently supported)

### Usage Object

```json
{
  "prompt_tokens": 10,
  "completion_tokens": 20,
  "total_tokens": 30
}
```

---

## Error Handling

The proxy transforms OpenRouter errors into OpenAI-compatible error responses.

### Error Response Format

Instead of traditional HTTP error codes with error objects, the proxy returns `200 OK` with the error embedded in a chat completion response:

```json
{
  "id": "gen-1234567890-error",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "anthropic/claude-3.7-sonnet",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Model unavailable: Error message details here",
        "refusal": null
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 10,
    "total_tokens": 20
  }
}
```

This format ensures Xcode can display errors gracefully instead of crashing.

### Common Errors

#### Authentication Errors

**Symptom:** "Invalid API key" or "Unauthorized"

**Solution:** Check your OpenRouter API key is correct and properly formatted with "Bearer " prefix.

#### Model Not Found

**Symptom:** "Model not found" or "Model unavailable"

**Solution:** Verify the model ID is correct and the model is available on OpenRouter.

#### Rate Limiting

**Symptom:** "Rate limit exceeded"

**Solution:** Reduce request frequency or upgrade your OpenRouter plan.

#### Invalid Request

**Symptom:** "Invalid request" or validation errors

**Solution:** Check request body format and required fields.

---

## Response Transformations

The proxy performs several transformations to ensure OpenAI compatibility:

### Removed Fields

OpenRouter-specific fields are removed from responses:

- `provider` (top-level)
- `native_finish_reason` (in choices)
- `reasoning` (in message)
- `reasoning_details` (in message)
- `prompt_tokens_details` (in usage)

### Filtered Messages

In streaming mode, the following messages are filtered out:

- Lines containing ": OPENROUTER PROCESSING"

### Field Additions

- `owned_by`: Extracted from model ID prefix (e.g., "anthropic" from "anthropic/claude-3.7-sonnet")

---

## Examples

### Complete Python Example (Non-streaming)

```python
import requests
import json

url = "http://localhost:8080/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-or-v1-YOUR_API_KEY_HERE",
    "Content-Type": "application/json"
}

data = {
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful coding assistant."
        },
        {
            "role": "user",
            "content": "Explain recursion in one sentence."
        }
    ],
    "temperature": 0.7,
    "max_tokens": 100
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(result["choices"][0]["message"]["content"])
```

### Complete Python Example (Streaming)

```python
import requests
import json

url = "http://localhost:8080/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-or-v1-YOUR_API_KEY_HERE",
    "Content-Type": "application/json"
}

data = {
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
        {
            "role": "user",
            "content": "Write a haiku about coding."
        }
    ],
    "stream": True
}

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines(decode_unicode=True):
    if line and line.startswith("data: "):
        data_str = line[6:]  # Remove "data: " prefix
        if data_str == "[DONE]":
            break

        chunk = json.loads(data_str)
        delta = chunk["choices"][0]["delta"]

        if "content" in delta:
            print(delta["content"], end="", flush=True)

print()  # New line at the end
```

### JavaScript/Node.js Example

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-or-v1-YOUR_API_KEY_HERE',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'anthropic/claude-3.7-sonnet',
    messages: [
      {
        role: 'user',
        content: 'Hello, how are you?'
      }
    ]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

### Swift Example (for Xcode integration)

Xcode handles API calls automatically when configured as a model provider. However, for manual integration:

```swift
struct ChatRequest: Codable {
    let model: String
    let messages: [Message]
    let stream: Bool = false
}

struct Message: Codable {
    let role: String
    let content: String
}

struct ChatResponse: Codable {
    let choices: [Choice]

    struct Choice: Codable {
        let message: Message
    }
}

func sendChatRequest(message: String) async throws -> String {
    let url = URL(string: "http://localhost:8080/v1/chat/completions")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("Bearer sk-or-v1-YOUR_API_KEY_HERE", forHTTPHeaderField: "Authorization")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let chatRequest = ChatRequest(
        model: "anthropic/claude-3.7-sonnet",
        messages: [Message(role: "user", content: message)]
    )

    request.httpBody = try JSONEncoder().encode(chatRequest)

    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(ChatResponse.self, from: data)

    return response.choices[0].message.content
}
```

---

## Rate Limits

Rate limits are determined by OpenRouter and your account tier. The proxy does not impose additional rate limits.

Check OpenRouter's [pricing page](https://openrouter.ai/docs#limits) for current rate limit information.

---

## Best Practices

1. **Always use streaming for long responses** to provide better user experience
2. **Set appropriate `max_tokens`** to control costs and response length
3. **Use system messages** to set model behavior and context
4. **Handle errors gracefully** - check for error messages in response content
5. **Monitor token usage** via the `usage` field to track costs
6. **Enable model filtering** to reduce Xcode's model list load time
7. **Use specific model versions** when consistency is important

---

## Support

For issues with:
- **The proxy**: [GitHub Issues](https://github.com/OhJayGee/OpenRouterXcodeProxy/issues)
- **OpenRouter API**: [OpenRouter Discord](https://discord.gg/openrouter)
- **Xcode integration**: [Apple Developer Forums](https://developer.apple.com/forums/)
