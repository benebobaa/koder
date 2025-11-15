# Web Search Tool

The web search tool enables koder to access current information from the internet, making it invaluable for queries about recent events, latest documentation, or information beyond the LLM's training data.

## Overview

Koder supports three configurable web search backends:

1. **DuckDuckGo** (Default) - Free, no API key required
2. **Tavily** - AI-optimized search with generous free tier
3. **Brave** - Independent search index with free tier

## Quick Start

### Using Default (DuckDuckGo)

No configuration needed! The agent can use web search immediately:

```bash
koder chat start
> What are the latest features in Python 3.13?
```

The agent will automatically decide when to use web search based on the query context.

## Configuration

### DuckDuckGo (Default)

**Cost:** Free
**API Key:** Not required
**Limits:** Rate limiting (handled automatically)

No configuration needed - works out of the box!

```bash
# In .env (optional, this is the default)
WEB_SEARCH_BACKEND=duckduckgo
```

### Tavily Search

**Cost:** 1,000 free searches/month (no credit card required)
**API Key:** Required
**Best For:** AI-optimized results with answer summaries

1. Sign up at [Tavily](https://tavily.com)
2. Get your API key
3. Configure in `.env`:

```bash
WEB_SEARCH_BACKEND=tavily
TAVILY_API_KEY=tvly-xxxxx
```

**Features:**
- AI-generated answer summaries
- Curated, high-quality results
- Optimized for LLM consumption
- Includes source citations

### Brave Search

**Cost:** 2,000 free searches/month
**API Key:** Required (credit card for verification)
**Best For:** Independent search index, privacy-focused

1. Sign up at [Brave Search API](https://brave.com/search/api/)
2. Verify with credit card (no charge for free tier)
3. Get your API key
4. Configure in `.env`:

```bash
WEB_SEARCH_BACKEND=brave
BRAVE_API_KEY=BSA_xxxxx
```

**Features:**
- Independent web index (not Google/Bing)
- Privacy-focused
- AI Grounding features
- Affordable paid tier ($3/1000 queries)

## Search Configuration

Customize search behavior in `.env`:

```bash
# Backend selection
WEB_SEARCH_BACKEND=duckduckgo  # or tavily, brave

# Number of results to return (1-50)
WEB_SEARCH_MAX_RESULTS=5

# Enable safe search filtering
WEB_SEARCH_SAFE_SEARCH=true
```

## Usage Examples

### Automatic Search (Recommended)

The agent automatically decides when to search based on query context:

```bash
koder chat start
> What happened in the 2024 Olympics?
# Agent automatically uses web search for current events

> What are the latest security vulnerabilities in Node.js?
# Agent searches for recent security information

> How do I use the newest React hooks?
# Agent searches for latest React documentation
```

### Explicit Search Request

You can explicitly request a web search:

```bash
koder chat start
> Search the web for latest AI breakthroughs in 2025

> Look up the current documentation for LangChain 0.3

> Find recent articles about quantum computing advances
```

### Task Mode

Use web search in one-off tasks:

```bash
koder task run "Research the latest best practices for Rust async programming"

koder task run "Find and summarize recent CVEs for Docker"
```

## How It Works

### Agent Decision Making

The agent uses web search when:
- Query mentions recent dates, current events, or "latest"
- Information likely changed after the model's training cutoff
- User explicitly requests web search
- Context suggests needing real-time information

### Search Flow

1. **Agent analyzes query** - Determines if web search is needed
2. **Formulates search query** - Creates effective search terms
3. **Executes search** - Uses configured backend
4. **Processes results** - Filters and formats relevant information
5. **Synthesizes answer** - Combines search results with reasoning

### Result Format

Search results include:
- **Title** - Page or article title
- **URL** - Source link for verification
- **Description** - Relevant excerpt or summary

For Tavily backend, also includes:
- **AI Summary** - Generated answer from search results

## Backend Comparison

| Feature | DuckDuckGo | Tavily | Brave |
|---------|------------|---------|-------|
| **Cost** | Free | Free tier (1K/mo) | Free tier (2K/mo) |
| **API Key** | Not required | Required | Required |
| **Setup Time** | Instant | 5 minutes | 10 minutes |
| **Search Quality** | Good | Excellent | Very Good |
| **AI Optimization** | No | Yes | Partial |
| **Answer Summaries** | No | Yes | No |
| **Rate Limits** | Soft limits | 1K/month free | 2K/month free |
| **Paid Tier** | N/A | $30/mo (4K) | $3/1000 queries |
| **Privacy** | Good | Standard | Excellent |
| **Best For** | Development | Production | Privacy-conscious |

## Best Practices

### When to Use Web Search

**Good Use Cases:**
- Current events and news
- Latest software versions/features
- Recent documentation
- Trending topics
- Time-sensitive information
- Technical specifications

**Not Recommended:**
- Code already in workspace
- General programming concepts
- Historical information
- Personal/private data
- Offline tasks

### Performance Tips

1. **Use DuckDuckGo for development** - No setup, unlimited usage
2. **Switch to Tavily for production** - Better quality, answer summaries
3. **Cache-friendly queries** - Similar queries may get cached results
4. **Specific search terms** - More specific = better results
5. **Combine with context retrieval** - Use both web search and codebase search

### Security Considerations

- **API keys** - Never commit to version control
- **Rate limits** - Monitor usage to avoid hitting limits
- **Search queries** - Be aware queries are sent to third-party services
- **Result validation** - Agent should validate search result relevance
- **Workspace isolation** - Web search is read-only, safe by default

## Troubleshooting

### DuckDuckGo Issues

**Problem:** Rate limiting errors
**Solution:** Wait a few minutes or switch backends

**Problem:** No results found
**Solution:** Try more general search terms

### Tavily Issues

**Problem:** "Insufficient balance" error
**Solution:** Check API key is valid and has remaining credits

**Problem:** "API key not found" error
**Solution:** Verify `TAVILY_API_KEY` is set in `.env`

### Brave Issues

**Problem:** "Unauthorized" error
**Solution:** Check API key format and validity

**Problem:** Rate limit exceeded
**Solution:** Upgrade to paid tier or switch backends

### General Issues

**Problem:** Agent not using web search
**Solution:** Be more explicit in query ("search the web for...")

**Problem:** Irrelevant results
**Solution:** Provide more specific search context

**Problem:** Slow responses
**Solution:** Reduce `WEB_SEARCH_MAX_RESULTS` or switch backends

## Advanced Usage

### Programmatic Access

Access the web search tool directly in Python:

```python
from koder.tools.web import WebSearchTool
from koder.config.settings import get_settings

# Create tool instance
search_tool = WebSearchTool(workspace_path=".")

# Execute search
results = search_tool._run("latest Python releases")
print(results)
```

### Custom Backend

Override backend per-query:

```python
# Use Tavily for this specific search
search_tool = WebSearchTool(
    workspace_path=".",
    backend="tavily",
    max_results=10
)
```

### Integration with Other Tools

Combine web search with code analysis:

```bash
koder task run "Search for latest FastAPI best practices and update our API code accordingly"
```

The agent will:
1. Use web search to find latest best practices
2. Use context retrieval to understand your codebase
3. Use code analysis to identify improvements
4. Suggest or implement changes

## API Reference

### WebSearchTool

**Parameters:**
- `workspace_path` (str) - Workspace directory path
- `backend` (str, optional) - Override default backend
- `max_results` (int, optional) - Override default max results
- `safe_search` (bool, optional) - Override default safe search

**Methods:**
- `_run(query: str) -> str` - Execute search and return formatted results

**Returns:**
Formatted string containing:
- Numbered search results
- Title, URL, and description for each result
- AI summary (if using Tavily backend)

## Related Documentation

- [Configuration Guide](configuration.md) - Environment variables and settings
- [Tool Permissions](tool-permissions.md) - Security and approval settings
- [Embeddings](embeddings.md) - Semantic code search
- [Architecture](architecture.md) - Tool system design

## Resources

- [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search)
- [Tavily API](https://tavily.com)
- [Brave Search API](https://brave.com/search/api/)
- [LangChain Tools](https://python.langchain.com/docs/integrations/tools/)
