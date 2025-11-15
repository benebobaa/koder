# DeepSeek Provider Guide

## Overview

DeepSeek is a cutting-edge AI model provider that offers powerful reasoning capabilities and cost-effective solutions for code assistance. Koder provides full integration with DeepSeek's models, including the advanced DeepSeek Reasoner for complex problem-solving.

## DeepSeek Models

### Available Models

#### DeepSeek Chat
- **Model Name**: `deepseek-chat`
- **Context Window**: 128K tokens
- **Max Output**: 8K tokens
- **Best For**: General-purpose conversations, code generation, explanations
- **Cost**: Most cost-effective option

#### DeepSeek Reasoner
- **Model Name**: `deepseek-reasoner`
- **Context Window**: 128K tokens
- **Max Output**: 8K tokens
- **Best For**: Complex reasoning, problem-solving, architectural decisions
- **Cost**: Slightly higher but provides superior reasoning capabilities

### Model Capabilities

| Feature | DeepSeek Chat | DeepSeek Reasoner |
|---------|---------------|-------------------|
| Code Generation | ✅ Excellent | ✅ Excellent |
| Code Explanation | ✅ Good | ✅ Superior |
| Complex Reasoning | ✅ Good | ✅ Exceptional |
| Architecture Design | ✅ Good | ✅ Superior |
| Debugging | ✅ Good | ✅ Excellent |
| Cost Efficiency | ✅ Exceptional | ✅ Good |
| Response Speed | ✅ Fast | ✅ Moderate |

## Configuration

### 1. Get API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key for configuration

### 2. Configure Environment

Add to your `.env` file:

```bash
# DeepSeek API Configuration
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# Default model (optional)
DEEPSEEK_MODEL=deepseek-chat

# Provider selection
LLM_PROVIDER=deepseek
```

### 3. Verify Configuration

```bash
# Test DeepSeek configuration
uv run koder --provider deepseek info

# Should show:
# Provider: deepseek
# Model: deepseek-chat
# API Key: ✓ Configured
# Status: ✓ Connected
```

## Usage Examples

### Basic Usage

```bash
# Start chat with DeepSeek
uv run koder --provider deepseek chat start

# Use specific model
uv run koder --provider deepseek --model deepseek-reasoner chat start

# Run task with DeepSeek
uv run koder --provider deepseek task run "analyze this codebase"
```

### Model Selection Examples

#### For Conversational Tasks
```bash
uv run koder --provider deepseek --model deepseek-chat chat start
```
Best for:
- Quick code explanations
- Simple debugging
- Code generation
- General assistance

#### For Complex Problem-Solving
```bash
uv run koder --provider deepseek --model deepseek-reasoner task run "design microservice architecture"
```
Best for:
- Complex architectural decisions
- Advanced debugging
- System design
- Algorithm optimization

## DeepSeek vs Other Providers

### When to Choose DeepSeek

**Choose DeepSeek Chat when:**
- You need cost-effective code assistance
- Response speed is important
- Tasks are straightforward to moderately complex
- You're working on general coding tasks

**Choose DeepSeek Reasoner when:**
- You need advanced reasoning capabilities
- Tasks involve complex problem-solving
- You need detailed explanations of logic
- Architectural decisions are required

### Comparison with Other Providers

| Aspect | DeepSeek Chat | DeepSeek Reasoner | Claude Sonnet | GPT-4 |
|--------|---------------|-------------------|---------------|-------|
| Cost | 💰 Lowest | 💰 Low | 💰💰 Medium | 💰💰💰 High |
| Speed | ⚡ Fast | ⚡ Moderate | ⚡ Fast | ⚡ Moderate |
| Reasoning | 🧠 Good | 🧠🧠 Superior | 🧠🧠 Excellent | 🧠🧠 Excellent |
| Code Quality | 💻 Excellent | 💻💻 Superior | 💻💻 Excellent | 💻💻 Excellent |
| Context Window | 📚 128K | 📚 128K | 📚 200K | 📚 128K |

## Advanced Configuration

### Custom Model Parameters

```bash
# In .env file
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TOP_P=0.95
DEEPSEEK_FREQUENCY_PENALTY=0.0
DEEPSEEK_PRESENCE_PENALTY=0.0
```

### Runtime Parameter Override

```bash
# Override temperature for creative tasks
uv run koder --provider deepseek --temperature 0.9 task run "generate creative solution"

# Lower temperature for analytical tasks
uv run koder --provider deepseek --temperature 0.2 task run "debug critical issue"
```

## Use Case Examples

### 1. Code Generation

```bash
# Using DeepSeek Chat for quick code generation
uv run koder --provider deepseek --model deepseek-chat chat start

You: Create a Python function to validate email addresses

🤖 Assistant: I'll create a comprehensive email validation function:
```python
import re
from typing import Optional

def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address format and structure.

    Args:
        email: Email address to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"

    # Basic pattern check
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"

    # Additional checks
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"

    local, domain = email.split('@')
    if len(local) > 64 or len(domain) > 253:
        return False, "Email components exceed length limits"

    return True, None
```
```

### 2. Complex Reasoning

```bash
# Using DeepSeek Reasoner for complex architectural decisions
uv run koder --provider deepseek --model deepseek-reasoner task run "design scalable notification system"

🤖 Assistant: I'll design a comprehensive, scalable notification system by analyzing requirements and creating a detailed architecture.

## Analysis Phase
Let me break down the requirements for a scalable notification system:

**Core Requirements:**
1. Multi-channel support (email, SMS, push, in-app)
2. High throughput and low latency
3. Reliability and delivery guarantees
4. User preferences and scheduling
5. Analytics and monitoring
6. Cost optimization

**Technical Considerations:**
- Message queue durability
- Database partitioning strategies
- Rate limiting per provider
- Retry mechanisms with exponential backoff
- Real-time delivery tracking

## Proposed Architecture

### 1. Message Flow Architecture
```
User Request → API Gateway → Notification Service → Message Queue → Workers → External Providers
```

### 2. Component Breakdown
[Detailed architectural components...]

This comprehensive design ensures scalability, reliability, and maintainability...
```

### 3. Debugging Complex Issues

```bash
# Using DeepSeek Reasoner for advanced debugging
uv run koder --provider deepseek --model deepseek-reasoner task run "debug memory leak in production"

🤖 Assistant: I'll help you debug this memory leak systematically.

## Problem Analysis
Memory leaks in production require careful investigation. Let me outline a comprehensive debugging strategy:

### Step 1: Symptom Analysis
- Memory usage patterns over time
- Correlation with specific user actions
- Impact on system performance

### Step 2: Investigation Plan
1. **Memory Profiling**: Use memory_profiler and objgraph
2. **GC Analysis**: Monitor garbage collection patterns
3. **Resource Tracking**: Identify unreleased resources
4. **Code Review**: Focus on common leak patterns

### Step 3: Common Causes to Investigate
- Event listeners not removed
- Circular references
- Unclosed database connections
- Large object caches
- Thread-local storage issues

[Detailed debugging steps and solutions...]
```

## Performance Optimization

### Optimizing DeepSeek Usage

1. **Choose the Right Model**
   - Use `deepseek-chat` for 80% of tasks
   - Use `deepseek-reasoner` for complex reasoning only

2. **Optimize Prompts**
   ```bash
   # Good: Specific and focused
   "Create a Python function to validate JSON input with custom error messages"

   # Avoid: Vague and broad
   "Help me with Python"
   ```

3. **Manage Context Window**
   ```bash
   # For large codebases, use focused analysis
   uv run koder --provider deepseek task run "analyze only the authentication module files"
   ```

### Cost Management

```bash
# Monitor usage
uv run koder --provider deepseek --stats info

# Set usage limits in configuration
DEEPSEEK_DAILY_LIMIT=1000  # requests per day
DEEPSEEK_COST_LIMIT=10.0   # dollars per day
```

## Troubleshooting

### Common Issues

#### API Connection Problems
```bash
# Check API key validity
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     https://api.deepseek.com/v1/models

# Verify network connectivity
uv run koder --provider deepseek --debug info
```

#### Model Selection Issues
```bash
# List available models
uv run koder --provider deepseek --list-models

# Test different models
uv run koder --provider deepseek --model deepseek-chat task run "test"
uv run koder --provider deepseek --model deepseek-reasoner task run "test"
```

#### Performance Issues
```bash
# Check response times
uv run koder --provider deepseek --timing task run "simple task"

# Adjust temperature for faster responses
uv run koder --provider deepseek --temperature 0.1 task run "analytical task"
```

### Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check DEEPSEEK_API_KEY in .env |
| `429 Rate Limited` | Too many requests | Implement rate limiting or reduce frequency |
| `Context Length Exceeded` | Input too long | Break down task into smaller parts |
| `Model Not Found` | Incorrect model name | Use `deepseek-chat` or `deepseek-reasoner` |

## Best Practices

### 1. Model Selection Guidelines

```python
# Decision matrix for model selection
def choose_deepseek_model(task_complexity, task_type, budget_constraint):
    if budget_constraint == "high":
        return "deepseek-chat"
    elif task_complexity == "high" and task_type in ["architecture", "debugging"]:
        return "deepseek-reasoner"
    else:
        return "deepseek-chat"
```

### 2. Prompt Engineering for DeepSeek

**Effective Prompts:**
- Be specific about expected output format
- Provide context for complex problems
- Use examples for better understanding
- Request step-by-step reasoning for complex tasks

**Example Structure:**
```
Context: [Provide relevant background]
Task: [Clearly state what you want]
Format: [Specify output format]
Constraints: [List any limitations]
Example: [Provide example if helpful]
```

### 3. Cost Optimization Strategies

- Use `deepseek-chat` for prototyping
- Switch to `deepseek-reasoner` only for final solutions
- Implement caching for repeated queries
- Batch related requests together

## Integration Examples

### 1. Automated Code Review Pipeline

```bash
# Use DeepSeek for automated code reviews
uv run koder --provider deepseek --model deepseek-reasoner task run \
  "review pull request #123 for security vulnerabilities and performance issues"
```

### 2. Documentation Generation

```bash
# Generate comprehensive documentation
uv run koder --provider deepseek --model deepseek-chat task run \
  "generate API documentation for endpoints in src/api/"
```

### 3. Test Case Generation

```bash
# Create comprehensive test suites
uv run koder --provider deepseek --model deepseek-reasoner task run \
  "generate unit tests for authentication service with edge cases"
```

## Future Enhancements

DeepSeek integration in Koder continues to evolve with:

- **Fine-tuned models** for specific programming languages
- **Function calling** capabilities for structured outputs
- **Streaming responses** for real-time interactions
- **Custom model training** for project-specific needs

The DeepSeek provider offers a powerful, cost-effective alternative to traditional AI providers, with particularly strong capabilities in code-related tasks and complex reasoning scenarios.