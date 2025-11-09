"""Default configuration values."""

# Default model configurations
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_OPENAI_MODEL = "gpt-4-turbo-preview"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096

# Default storage paths
DEFAULT_VECTOR_STORE_PATH = "./data/vector_store"
DEFAULT_CHECKPOINT_PATH = "./data/checkpoints/checkpoints.db"
DEFAULT_CACHE_PATH = "./data/cache"

# Default agent parameters
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TIMEOUT_SECONDS = 300

# Default embeddings
DEFAULT_GOOGLE_EMBEDDING_MODEL = "models/text-embedding-004"
DEFAULT_EMBEDDING_DIMENSION = 768

# Default observability settings
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LANGSMITH_PROJECT = "koder"
