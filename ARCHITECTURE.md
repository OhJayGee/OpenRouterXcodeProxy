# Architecture Documentation

This document describes the architecture, design decisions, and implementation details of the OpenRouter Proxy for Xcode 26 Beta.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Components](#components)
- [Data Flow](#data-flow)
- [API Transformation](#api-transformation)
- [Design Decisions](#design-decisions)
- [Security Considerations](#security-considerations)
- [Performance](#performance)
- [Deployment Architecture](#deployment-architecture)
- [Future Enhancements](#future-enhancements)

## Overview

### Purpose

The OpenRouter Proxy serves as a compatibility layer between Xcode 26 Beta's AI integration (which expects OpenAI-compatible APIs) and OpenRouter's API (which has a slightly different format). The proxy enables Xcode users to access OpenRouter's extensive catalog of AI models.

### Key Goals

1. **Compatibility**: Ensure seamless integration with Xcode 26 Beta
2. **Transparency**: Minimal overhead in request/response handling
3. **Simplicity**: Easy to deploy and configure
4. **Reliability**: Robust error handling and graceful degradation
5. **Observability**: Comprehensive logging for debugging

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Xcode 26 Beta                           │
│                    (OpenAI-compatible API)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            │ OpenAI Format
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenRouter Proxy                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   Flask     │→ │  Request     │→ │    Response        │    │
│  │   Routes    │  │  Transform   │  │    Transform       │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│         │                  │                    ▲               │
│         │                  │                    │               │
│         ▼                  ▼                    │               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   Model     │  │   Logger     │  │   Error Handler    │    │
│  │   Filter    │  │              │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            │ OpenRouter Format
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OpenRouter API                             │
│                 (https://openrouter.ai)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Flask Application                       │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    HTTP Layer                             │ │
│  │  - Route handlers (/v1/models, /v1/chat/completions)     │ │
│  │  - Request parsing                                        │ │
│  │  - Response formatting                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  Business Logic Layer                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │ │
│  │  │   Model     │  │  Request    │  │   Response      │  │ │
│  │  │   Filter    │  │  Proxy      │  │   Transform     │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                Infrastructure Layer                       │ │
│  │  - Logging (stdout)                                       │ │
│  │  - Error handling                                         │ │
│  │  - Configuration (environment variables)                  │ │
│  │  - HTTP client (requests library)                         │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Flask Application (`app.py`)

**Responsibility**: Main application entry point and HTTP server

**Key Functions**:
- Route definitions
- Request/response handling
- Application lifecycle management

**Dependencies**:
- Flask 3.0.0
- Waitress (WSGI server)

### 2. Models Endpoint Handler

**Endpoint**: `GET /v1/models`

**Responsibility**: Fetch and transform model list

**Process**:
1. Receive request from Xcode
2. Forward headers to OpenRouter (with Host update)
3. Fetch models from OpenRouter API
4. Apply model filtering (if configured)
5. Transform to OpenAI format
6. Return transformed response

**Key Features**:
- Wildcard pattern matching for model filtering
- Regex-based filtering using `fnmatch`
- Extraction of `owned_by` from model ID

### 3. Chat Completions Endpoint Handler

**Endpoint**: `POST /v1/chat/completions`

**Responsibility**: Proxy chat requests and transform responses

**Process**:
1. Receive chat request from Xcode
2. Forward to OpenRouter API
3. Handle streaming/non-streaming responses
4. Filter OpenRouter-specific fields
5. Transform errors to OpenAI format
6. Return transformed response

**Key Features**:
- Streaming support with Server-Sent Events (SSE)
- Error transformation for Xcode compatibility
- Filtering of "OPENROUTER PROCESSING" messages
- Removal of OpenRouter-specific fields

### 4. Model Filter

**Responsibility**: Filter models based on whitelist

**Implementation**:
```python
# Load filter patterns
allowed_models = set()  # From file or env var

# Convert to regex
regex_patterns = [fnmatch.translate(pattern) for pattern in allowed_models]

# Filter models
filtered_models = [
    model for model in all_models
    if any(re.match(pattern, model["id"]) for pattern in regex_patterns)
]
```

**Supported Patterns**:
- Exact: `anthropic/claude-3.7-sonnet`
- Wildcard prefix: `anthropic/*`
- Wildcard suffix: `*/gpt-4*`
- Wildcard middle: `*claude*4*`

### 5. Request Logger

**Responsibility**: Log requests and responses for debugging

**Implementation**:
- Logs to stdout (captured by Docker/systemd)
- Structured logging format
- Includes headers, body, and response data

**Log Levels**:
- Request details
- Response status
- Error tracebacks

### 6. Error Handler

**Responsibility**: Transform errors to OpenAI-compatible format

**Strategy**:
- Catch OpenRouter errors (4xx, 5xx)
- Format as valid chat completion response
- Include error message in content field
- Return 200 OK (for Xcode compatibility)

**Example Transformation**:
```python
# OpenRouter error
{
    "error": {
        "message": "Model not found",
        "code": 404
    }
}

# Transformed to OpenAI format
{
    "choices": [{
        "message": {
            "content": "Model unavailable: Model not found"
        },
        "finish_reason": "stop"
    }],
    "object": "chat.completion"
}
```

## Data Flow

### Models Endpoint Flow

```
1. Xcode Request
   GET /v1/models
   Authorization: Bearer sk-or-v1-...
        │
        ▼
2. Proxy Receives
   - Extract headers
   - Update Host header
        │
        ▼
3. Forward to OpenRouter
   GET https://openrouter.ai/api/v1/models
        │
        ▼
4. OpenRouter Response
   {
     "data": [
       {"id": "anthropic/claude-3.7-sonnet", ...},
       {"id": "openai/gpt-4", ...},
       ... (200+ models)
     ]
   }
        │
        ▼
5. Apply Model Filter
   - Load filter-models.txt
   - Match with wildcards
   - Reduce to ~8-10 models
        │
        ▼
6. Transform to OpenAI Format
   {
     "object": "list",
     "data": [
       {
         "id": "anthropic/claude-3.7-sonnet",
         "object": "model",
         "created": 1234567890,
         "owned_by": "anthropic"
       }
     ]
   }
        │
        ▼
7. Return to Xcode
   200 OK
```

### Chat Completions Flow (Non-streaming)

```
1. Xcode Request
   POST /v1/chat/completions
   {
     "model": "anthropic/claude-3.7-sonnet",
     "messages": [{"role": "user", "content": "Hello"}]
   }
        │
        ▼
2. Proxy Receives
   - Extract headers and body
   - Update Host header
   - Log request details
        │
        ▼
3. Forward to OpenRouter
   POST https://openrouter.ai/api/v1/chat/completions
        │
        ▼
4. OpenRouter Response
   {
     "id": "gen-...",
     "choices": [{
       "message": {"content": "Hello!"},
       "native_finish_reason": "end_turn"  ← OpenRouter-specific
     }],
     "provider": "Anthropic"  ← OpenRouter-specific
   }
        │
        ▼
5. Transform Response
   - Remove "provider" field
   - Remove "native_finish_reason"
   - Remove "reasoning" fields
   - Clean usage object
        │
        ▼
6. Return to Xcode
   {
     "id": "gen-...",
     "choices": [{
       "message": {"content": "Hello!"},
       "finish_reason": "stop"
     }]
   }
```

### Chat Completions Flow (Streaming)

```
1. Xcode Request
   POST /v1/chat/completions
   {"stream": true, ...}
        │
        ▼
2. Proxy Opens Stream
   - Sets stream=True in requests
   - Prepares SSE response
        │
        ▼
3. OpenRouter Streams Chunks
   data: {"choices": [{"delta": {"content": "H"}}]}
   data: {"choices": [{"delta": {"content": "e"}}]}
   data: {"choices": [{"delta": {"content": "llo"}}]}
        │
        ▼
4. Proxy Filters Each Chunk
   - Skip "OPENROUTER PROCESSING" messages
   - Remove OpenRouter-specific fields
   - Pass through cleaned chunks
        │
        ▼
5. Stream to Xcode
   data: {"choices": [{"delta": {"content": "H"}}]}
   data: {"choices": [{"delta": {"content": "e"}}]}
   data: {"choices": [{"delta": {"content": "llo"}}]}
   data: [DONE]
```

## API Transformation

### Field Mapping

#### Models Response

| OpenRouter Field | OpenAI Field | Transformation |
|-----------------|--------------|----------------|
| `id` | `id` | Direct copy |
| `created` | `created` | Direct copy |
| - | `object` | Hardcoded: "model" |
| `id` (prefix) | `owned_by` | Extract before "/" |

#### Chat Completions Response

| OpenRouter Field | OpenAI Field | Transformation |
|-----------------|--------------|----------------|
| `id` | `id` | Direct copy |
| `created` | `created` | Direct copy |
| `model` | `model` | Direct copy |
| `choices` | `choices` | Filtered (see below) |
| `usage` | `usage` | Filtered (see below) |
| `provider` | - | **Removed** |

#### Choices Filtering

**Removed Fields**:
- `native_finish_reason` (replaced by standard `finish_reason`)
- `message.reasoning` (OpenRouter-specific)
- `message.reasoning_details` (OpenRouter-specific)

#### Usage Filtering

**Removed Fields**:
- `prompt_tokens_details` (OpenRouter-specific)

### Streaming Transformations

**Filtered Messages**:
- Lines containing `: OPENROUTER PROCESSING`

**Field Transformations** (same as non-streaming):
- Remove `provider`
- Remove `native_finish_reason`
- Remove reasoning fields

## Design Decisions

### 1. Flask as Web Framework

**Rationale**:
- Lightweight and simple
- Well-documented
- Easy to deploy
- Suitable for proxy use case

**Alternatives Considered**:
- FastAPI: More complex, async not needed
- Django: Too heavy for this use case

### 2. Waitress as WSGI Server

**Rationale**:
- Production-ready
- Cross-platform (works on Windows)
- No dependencies on system libraries
- Easy to configure

**Alternatives Considered**:
- Gunicorn: Unix-only
- uWSGI: More complex configuration

### 3. Synchronous Request Handling

**Rationale**:
- Simple implementation
- Adequate performance for proxy use case
- Easier to debug and maintain

**Alternatives Considered**:
- Async/await: Added complexity without significant benefit
- Threading: Not needed for single-user scenario

### 4. Error Format Transformation

**Decision**: Return 200 OK with error in content field

**Rationale**:
- Xcode displays errors gracefully
- Prevents UI crashes
- User sees helpful error messages

**Alternative**:
- Return proper HTTP error codes: Causes Xcode to crash or show generic errors

### 5. Model Filtering Approach

**Decision**: File-based whitelist with wildcard support

**Rationale**:
- Easy to configure without code changes
- Wildcard support provides flexibility
- Reduces Xcode load time significantly

**Alternatives Considered**:
- API-based filtering: More complex
- No filtering: Xcode struggles with 200+ models

### 6. Logging to Stdout

**Decision**: All logs go to stdout/stderr

**Rationale**:
- Docker-friendly (captured by container logs)
- Systemd-friendly (captured by journald)
- Follows 12-factor app principles

**Alternatives Considered**:
- File-based logging: Harder to manage in containers
- Structured logging (JSON): Overkill for this use case

## Security Considerations

### 1. API Key Handling

**Approach**:
- Pass-through authentication
- Never store or log API keys
- Forward Authorization header as-is

**Security**:
- No API key exposure in logs
- No local storage of credentials
- Client responsible for key security

### 2. SSL/TLS

**Default**: SSL verification enabled

**Optional Disable**:
- Via `DISABLE_SSL_VERIFY=true`
- For debugging only (Proxyman, Charles)
- Warning in documentation

**Rationale**:
- Security by default
- Opt-in for debugging scenarios

### 3. Input Validation

**Approach**:
- Minimal validation (proxy pattern)
- Rely on OpenRouter API validation
- Validate only critical paths

**Rationale**:
- Avoid duplication of validation logic
- Let upstream API handle validation
- Reduce maintenance burden

### 4. Error Information Disclosure

**Approach**:
- Pass OpenRouter errors to client
- No internal stack traces in responses
- Log detailed errors server-side only

**Rationale**:
- Client needs error details to fix issues
- No sensitive internal information leaked

## Performance

### Latency

**Components**:
```
Total Latency = Network(Xcode→Proxy) + Processing + Network(Proxy→OpenRouter) + OpenRouter Processing + Network(OpenRouter→Proxy) + Processing + Network(Proxy→Xcode)
```

**Typical Values**:
- Local proxy overhead: <10ms
- Network to OpenRouter: 50-200ms (depending on location)
- OpenRouter processing: Variable (model-dependent)

**Optimization**:
- Minimal processing in proxy
- Streaming support for long responses
- No caching (pass-through design)

### Memory

**Usage**:
- Base: ~50MB (Flask + dependencies)
- Per request: ~1-5MB (buffered responses)
- Streaming: Minimal additional memory

**Limits**:
- No built-in request size limits
- Relies on Flask defaults
- Docker can set memory limits

### Scalability

**Current Design**:
- Single-threaded
- Designed for single-user (local Xcode)
- Synchronous request handling

**Scaling Options** (if needed):
- Gunicorn with multiple workers
- Nginx as reverse proxy
- Load balancer for multiple instances

## Deployment Architecture

### Docker Deployment

```
┌─────────────────────────────────────┐
│         Docker Container            │
│                                     │
│  ┌──────────────────────────────┐  │
│  │    Waitress WSGI Server      │  │
│  │         (Port 8080)          │  │
│  │            │                 │  │
│  │            ▼                 │  │
│  │    Flask Application         │  │
│  │       (app.py)               │  │
│  └──────────────────────────────┘  │
│                                     │
│  Volume Mounts:                     │
│  - filter-models.txt (optional)     │
│                                     │
│  Environment Variables:             │
│  - PORT=8080                        │
│  - DISABLE_SSL_VERIFY=false         │
│  - MODEL_FILTER_FILE=/path         │
└─────────────────────────────────────┘
         │
         ▼
   Host Network
   (Port 8080)
```

### Standalone Executable

```
┌─────────────────────────────────────┐
│      PyInstaller Bundle             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │    Embedded Python           │  │
│  │    + Dependencies            │  │
│  │    + app.py                  │  │
│  └──────────────────────────────┘  │
│                                     │
│  External Files:                    │
│  - filter-models.txt (optional)     │
└─────────────────────────────────────┘
```

### Docker Compose

```
┌───────────────────────────────────────────┐
│        Docker Compose Network             │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │   OpenRouter Proxy Container        │ │
│  │   - Port mapping: 8080:8080         │ │
│  │   - Auto-restart: unless-stopped    │ │
│  │   - Volume: ./filter-models.txt     │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  Environment from:                        │
│  - .env file (optional)                   │
│  - docker-compose.yml                     │
└───────────────────────────────────────────┘
```

## Future Enhancements

### Potential Improvements

1. **Caching Layer**
   - Cache model list responses
   - Reduce API calls to OpenRouter
   - Configurable TTL

2. **Rate Limiting**
   - Protect against abuse
   - Configurable limits per endpoint
   - Integration with OpenRouter limits

3. **Metrics and Monitoring**
   - Prometheus metrics endpoint
   - Request/response timing
   - Error rate tracking
   - Model usage statistics

4. **Health Check Endpoint**
   - `/health` or `/healthz`
   - Check OpenRouter connectivity
   - Report service status

5. **Configuration UI**
   - Web interface for configuration
   - Model filter management
   - Request/response inspection
   - Logs viewer

6. **Multiple Provider Support**
   - Support other AI providers
   - Unified interface
   - Provider selection via header or config

7. **Request/Response Hooks**
   - Pre-request hooks (modify before sending)
   - Post-response hooks (modify after receiving)
   - Custom transformations

8. **Advanced Filtering**
   - Filter by model capabilities
   - Filter by cost
   - Filter by performance metrics
   - Dynamic filtering based on usage

9. **Authentication Layer**
   - Optional auth for proxy access
   - API key management
   - Usage tracking per key

10. **Structured Logging**
    - JSON log format
    - Log aggregation support
    - Correlation IDs

## Maintenance and Operations

### Logging

**Locations**:
- Docker: `docker-compose logs -f`
- Standalone: stdout/stderr
- Systemd: `journalctl -u openrouter-proxy`

**Log Levels**:
- All logs currently at INFO level
- Errors include stack traces

### Monitoring

**Key Metrics to Monitor**:
- Request rate
- Error rate
- Response time
- Memory usage
- CPU usage

**Tools**:
- Docker stats: `docker stats`
- System monitoring: `htop`, `top`
- Log analysis: `grep`, `jq`

### Troubleshooting

**Common Issues**:
1. Connection refused → Check if proxy is running
2. Authentication errors → Verify API key
3. SSL errors → Check DISABLE_SSL_VERIFY setting
4. Model list errors → Check filter file syntax

**Debug Mode**:
```python
# Enable Flask debug mode (development only)
if __name__ == '__main__':
    app.run(debug=True)
```

## Conclusion

The OpenRouter Proxy is designed as a simple, reliable compatibility layer with minimal overhead. Its architecture prioritizes:

- **Simplicity**: Easy to understand and maintain
- **Reliability**: Robust error handling
- **Transparency**: Minimal transformation
- **Observability**: Comprehensive logging

The design makes intentional trade-offs (e.g., synchronous over async) to maintain simplicity while meeting the primary use case: enabling Xcode 26 Beta to work with OpenRouter models.
