# Gemini Provider Guide

## Overview

Google Gemini is a powerful multimodal AI model family that excels at text understanding, code generation, and complex reasoning tasks. Koder provides seamless integration with Google's Gemini models, including the high-performance Gemini 1.5 Pro and the efficient Gemini 1.5 Flash.

## Gemini Models

### Available Models

#### Gemini 1.5 Pro
- **Model Name**: `gemini-1.5-pro`
- **Context Window**: 2M tokens
- **Max Output**: 8K tokens
- **Best For**: Complex reasoning, code analysis, large-scale documentation
- **Cost**: Premium tier with advanced capabilities

#### Gemini 1.5 Flash
- **Model Name**: `gemini-1.5-flash`
- **Context Window**: 1M tokens
- **Max Output**: 8K tokens
- **Best For**: Fast responses, code generation, standard assistance
- **Cost**: Cost-effective with excellent performance

#### Gemini Pro Vision
- **Model Name**: `gemini-pro-vision`
- **Context Window**: 16K tokens
- **Max Output**: 4K tokens
- **Best For**: Multimodal tasks, image analysis, visual reasoning
- **Cost**: Specialized for vision tasks

### Model Capabilities

| Feature | Gemini 1.5 Pro | Gemini 1.5 Flash | Gemini Pro Vision |
|---------|----------------|------------------|-------------------|
| Code Generation | ✅ Exceptional | ✅ Excellent | ✅ Good |
| Complex Reasoning | ✅ Exceptional | ✅ Good | ✅ Moderate |
| Large Context | ✅ 2M tokens | ✅ 1M tokens | ❌ Limited |
| Multimodal | ❌ Text only | ❌ Text only | ✅ Images + Text |
| Response Speed | ⚡ Moderate | ⚡⚡ Very Fast | ⚡ Moderate |
| Cost Efficiency | 💰💰💰 High | 💰💰 Medium | 💰💰 Medium |

## Configuration

### 1. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Navigate to "Get API Key" section
4. Create a new API key
5. Copy the key for configuration

### 2. Configure Environment

Add to your `.env` file:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Required: Specify your preferred model
GEMINI_MODEL=gemini-1.5-pro

# Provider selection
LLM_PROVIDER=gemini
```

**Important**: Gemini requires explicit model selection. You must specify one of:
- `gemini-1.5-pro` for advanced capabilities
- `gemini-1.5-flash` for faster responses
- `gemini-pro-vision` for multimodal tasks

### 3. Verify Configuration

```bash
# Test Gemini configuration
uv run koder --provider gemini --model gemini-1.5-pro info

# Should show:
# Provider: gemini
# Model: gemini-1.5-pro
# API Key: ✓ Configured
# Status: ✓ Connected
```

## Usage Examples

### Basic Usage

```bash
# Start chat with Gemini 1.5 Pro
uv run koder --provider gemini --model gemini-1.5-pro chat start

# Use faster Gemini 1.5 Flash
uv run koder --provider gemini --model gemini-1.5-flash chat start

# Run task with Gemini
uv run koder --provider gemini --model gemini-1.5-pro task run "analyze this codebase"
```

### Model Selection Examples

#### For Complex Analysis and Reasoning
```bash
uv run koder --provider gemini --model gemini-1.5-pro task run "design microservice architecture"
```
Best for:
- Large-scale code analysis
- Complex architectural decisions
- Comprehensive documentation generation
- Advanced debugging scenarios

#### For Fast Code Generation
```bash
uv run koder --provider gemini --model gemini-1.5-flash chat start
```
Best for:
- Quick code generation
- Simple debugging tasks
- Code explanations
- Standard programming assistance

#### For Multimodal Tasks
```bash
uv run koder --provider gemini --model gemini-pro-vision task run "analyze this screenshot"
```
Best for:
- Image-based code analysis
- UI/UX design feedback
- Diagram understanding
- Visual problem-solving

## Gemini vs Other Providers

### When to Choose Gemini

**Choose Gemini 1.5 Pro when:**
- You need massive context window (2M tokens)
- Complex reasoning and analysis are required
- Quality is more important than speed
- You're working with large codebases

**Choose Gemini 1.5 Flash when:**
- Response speed is critical
- You need cost-effective solutions
- Tasks are moderately complex
- You want high performance at lower cost

**Choose Gemini Pro Vision when:**
- You need to analyze images or diagrams
- Multimodal understanding is required
- Visual context is important
- UI/UX analysis is needed

### Comparison with Other Providers

| Aspect | Gemini 1.5 Pro | Gemini 1.5 Flash | Claude Sonnet | GPT-4 |
|--------|----------------|------------------|---------------|-------|
| Context Window | 📚📚📚 2M | 📚📚 1M | 📚📚 200K | 📚 128K |
| Reasoning | 🧠🧠🧠 Exceptional | 🧠🧠 Excellent | 🧠🧠🧠 Exceptional | 🧠🧠🧠 Exceptional |
| Code Quality | 💻💻 Exceptional | 💻💻 Excellent | 💻💻 Exceptional | 💻💻 Exceptional |
| Speed | ⚡ Moderate | ⚡⚡⚡ Very Fast | ⚡ Fast | ⚡ Moderate |
| Cost | 💰💰💰 High | 💰💰 Medium | 💰💰 Medium | 💰💰💰 High |
| Multimodal | ❌ No | ❌ No | ❌ No | ✅ Vision |

## Advanced Configuration

### Custom Model Parameters

```bash
# In .env file
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4096
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
```

### Runtime Parameter Override

```bash
# Override temperature for creative tasks
uv run koder --provider gemini --model gemini-1.5-pro --temperature 0.9 task run "generate creative solution"

# Lower temperature for analytical tasks
uv run koder --provider gemini --model gemini-1.5-pro --temperature 0.2 task run "debug critical issue"
```

## Use Case Examples

### 1. Large-Scale Code Analysis

```bash
# Using Gemini 1.5 Pro for massive codebase analysis
uv run koder --provider gemini --model gemini-1.5-pro task run "analyze entire codebase for security vulnerabilities"

🤖 Assistant: I'll perform a comprehensive security analysis of your entire codebase using Gemini's 2M token context window.

## Security Analysis Framework

### 1. Authentication & Authorization Analysis
- JWT implementation review
- Session management patterns
- Role-based access control (RBAC)
- API authentication mechanisms

### 2. Data Protection & Validation
- Input sanitization patterns
- SQL injection prevention
- XSS protection mechanisms
- Data encryption at rest and in transit

### 3. Infrastructure Security
- Dependency vulnerability scanning
- Configuration security review
- Network security patterns
- Container and deployment security

[Comprehensive analysis continues with specific code examples and recommendations...]
```

### 2. Fast Code Generation

```bash
# Using Gemini 1.5 Flash for rapid development
uv run koder --provider gemini --model gemini-1.5-flash chat start

You: Create a FastAPI endpoint for user registration with validation

🤖 Assistant: I'll create a complete FastAPI user registration endpoint with proper validation:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re
from datetime import datetime

app = FastAPI()

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v

@app.post("/api/v1/users/register")
async def register_user(user_data: UserRegistration):
    """Register a new user with validation."""
    try:
        # Check if user already exists
        if await user_exists(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        if await username_exists(user_data.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = await create_user(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hashed_password
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
```

This implementation provides secure user registration with comprehensive validation...
```

### 3. Multimodal Analysis

```bash
# Using Gemini Pro Vision for visual code analysis
uv run koder --provider gemini --model gemini-pro-vision task run "analyze this architecture diagram"

🤖 Assistant: I'll analyze the architecture diagram you've provided.

## Architecture Analysis

### Visual Overview
The diagram shows a microservices architecture with the following components:

**Frontend Layer:**
- React SPA
- Mobile App (iOS/Android)
- Admin Dashboard

**API Gateway:**
- Load balancer with SSL termination
- Rate limiting and authentication
- Request routing

**Microservices:**
- User Service (Node.js)
- Product Service (Python/FastAPI)
- Order Service (Java/Spring Boot)
- Payment Service (Go)

**Data Layer:**
- PostgreSQL for relational data
- Redis for caching
- MongoDB for document storage

### Recommendations

1. **Security Improvements:**
   - Implement API key rotation
   - Add JWT token refresh mechanism
   - Consider service mesh for inter-service communication

2. **Scalability Enhancements:**
   - Auto-scaling for API gateway
   - Database connection pooling
   - Implement circuit breakers

3. **Monitoring & Observability:**
   - Add distributed tracing
   - Implement centralized logging
   - Health check endpoints for all services

[Detailed architectural recommendations continue...]
```

## Performance Optimization

### Optimizing Gemini Usage

1. **Choose the Right Model**
   - Use `gemini-1.5-flash` for 70% of tasks
   - Use `gemini-1.5-pro` for large context analysis
   - Use `gemini-pro-vision` for multimodal tasks only

2. **Leverage Large Context Window**
   ```bash
   # Gemini 1.5 Pro can handle entire files
   uv run koder --provider gemini --model gemini-1.5-pro task run "analyze entire microservice codebase"

   # Don't split large files - Gemini can handle them
   uv run koder --provider gemini --model gemini-1.5-pro task run "review this 50,000 line code file"
   ```

3. **Optimize Prompt Structure**
   ```bash
   # Good: Provide comprehensive context
   "Analyze this entire repository for performance bottlenecks. Consider database queries, API calls, and algorithmic complexity."

   # Better: Leverage large context effectively
   "Here's the entire codebase. Identify performance issues, suggest optimizations, and provide specific code improvements with examples."
   ```

### Cost Management

```bash
# Monitor usage
uv run koder --provider gemini --stats info

# Optimize for cost-effective usage
uv run koder --provider gemini --model gemini-1.5-flash task run "simple code generation"

# Reserve premium model for complex tasks
uv run koder --provider gemini --model gemini-1.5-pro task run "comprehensive system redesign"
```

## Troubleshooting

### Common Issues

#### API Connection Problems
```bash
# Check API key validity
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=$GEMINI_API_KEY"

# Verify network connectivity
uv run koder --provider gemini --debug info
```

#### Model Configuration Issues
```bash
# Test different models
uv run koder --provider gemini --model gemini-1.5-pro task run "test"
uv run koder --provider gemini --model gemini-1.5-flash task run "test"

# Verify model is specified
echo "GEMINI_MODEL=$GEMINI_MODEL"
```

#### Context Window Issues
```bash
# Gemini handles large context well, but check limits
uv run koder --provider gemini --model gemini-1.5-pro task run "analyze file context size"

# For extremely large inputs, consider chunking
uv run koder --provider gemini --model gemini-1.5-pro task run "analyze this in chunks: [file1, file2, file3]"
```

### Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | Invalid API key | Check GEMINI_API_KEY in .env |
| `429 Resource Exhausted` | Rate limit exceeded | Implement request throttling |
| `400 Invalid Argument` | Model not specified | Set GEMINI_MODEL in configuration |
| `Context Length Exceeded` | Input too long for model | Use Gemini 1.5 Pro or chunk input |

## Best Practices

### 1. Model Selection Guidelines

```python
def choose_gemini_model(task_type, context_size, speed_requirement):
    """Decision matrix for Gemini model selection."""
    if task_type == "multimodal":
        return "gemini-pro-vision"
    elif context_size > 1000000:  # > 1M tokens
        return "gemini-1.5-pro"
    elif speed_requirement == "critical":
        return "gemini-1.5-flash"
    elif task_type in ["complex_analysis", "architecture_design"]:
        return "gemini-1.5-pro"
    else:
        return "gemini-1.5-flash"
```

### 2. Prompt Engineering for Gemini

**Effective Strategies:**
- Leverage the massive context window for comprehensive context
- Use structured prompts for complex analysis
- Provide examples for better understanding
- Request step-by-step reasoning for complex problems

**Example Structure:**
```
Context: [Provide extensive background and code]
Task: [Clearly state the objective]
Scope: [Define analysis boundaries]
Format: [Specify desired output format]
Constraints: [List any limitations or preferences]
```

### 3. Advanced Usage Patterns

**Large-Scale Analysis:**
```bash
# Gemini can handle entire projects at once
uv run koder --provider gemini --model gemini-1.5-pro task run "comprehensively analyze this entire monorepo"
```

**Iterative Refinement:**
```bash
# Start with broad analysis, then dive deeper
uv run koder --provider gemini --model gemini-1.5-pro task run "identify main issues"
uv run koder --provider gemini --model gemini-1.5-pro task run "deep dive into issue #1"
```

## Integration Examples

### 1. Enterprise Code Review

```bash
# Comprehensive code review with Gemini 1.5 Pro
uv run koder --provider gemini --model gemini-1.5-pro task run \
  "perform enterprise-level code review focusing on security, performance, maintainability, and compliance"
```

### 2. Documentation Generation

```bash
# Generate comprehensive API documentation
uv run koder --provider gemini --model gemini-1.5-pro task run \
  "create complete API documentation including examples, error handling, and best practices for all endpoints"
```

### 3. System Architecture Analysis

```bash
# Analyze and improve system architecture
uv run koder --provider gemini --model gemini-1.5-pro task run \
  "review system architecture for scalability, reliability, and security. Provide improvement recommendations"
```

## Future Enhancements

Gemini integration in Koder continues to evolve with:

- **Enhanced multimodal capabilities** for code diagram analysis
- **Streaming responses** for real-time interactions
- **Fine-tuned models** for specific programming domains
- **Advanced reasoning chains** for complex problem-solving

The Gemini provider offers unique advantages with its massive context window and strong reasoning capabilities, making it particularly valuable for large-scale code analysis and complex architectural tasks.