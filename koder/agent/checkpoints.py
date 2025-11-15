"""Checkpoint configuration for state persistence."""

from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


@contextmanager
def get_checkpointer(checkpoint_path: str):
    """
    Get SQLite checkpointer instance as a context manager.

    Args:
        checkpoint_path: Path to SQLite database file

    Yields:
        Configured SqliteSaver instance
    """
    # Ensure directory exists
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)

    # In langgraph-checkpoint-sqlite v3.0+, from_conn_string returns a context manager
    # Use proper context management to keep database connection open
    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        yield checkpointer


def get_checkpoint_config(
    thread_id: str,
    checkpoint_ns: str = "",
    checkpoint_id: str | None = None,
    recursion_limit: int = 100,
) -> dict:
    """
    Generate checkpoint configuration for graph invocation.

    Args:
        thread_id: Thread identifier
        checkpoint_ns: Checkpoint namespace (optional)
        checkpoint_id: Specific checkpoint ID to resume from (optional)
        recursion_limit: Maximum recursion depth for graph execution (default: 100)

    Returns:
        Configuration dictionary for LangGraph
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": recursion_limit,
    }

    if checkpoint_ns:
        config["configurable"]["checkpoint_ns"] = checkpoint_ns

    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    return config


class ThreadManager:
    """Manage conversation threads and their metadata."""

    def __init__(self, db_path: str):
        """
        Initialize thread manager.

        Args:
            db_path: Path to SQLite database for thread metadata
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize thread metadata database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                user_id TEXT,
                metadata TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def create_thread(
        self,
        thread_id: str,
        title: str | None = None,
        user_id: str = "default",
    ) -> str:
        """
        Create new thread entry.

        Args:
            thread_id: Thread identifier
            title: Thread title
            user_id: User identifier

        Returns:
            Thread ID
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO threads (thread_id, title, user_id)
            VALUES (?, ?, ?)
        """,
            (thread_id, title, user_id),
        )
        conn.commit()
        conn.close()

        return thread_id

    def list_threads(self, user_id: str | None = None) -> list[dict]:
        """
        List all threads, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of thread dictionaries
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_id:
            cursor.execute(
                """
                SELECT thread_id, created_at, updated_at, title, user_id
                FROM threads
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """,
                (user_id,),
            )
        else:
            cursor.execute(
                """
                SELECT thread_id, created_at, updated_at, title, user_id
                FROM threads
                ORDER BY updated_at DESC
            """
            )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "thread_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "title": row[3],
                "user_id": row[4],
            }
            for row in rows
        ]

    def get_thread(self, thread_id: str) -> dict | None:
        """
        Get thread metadata.

        Args:
            thread_id: Thread identifier

        Returns:
            Thread dictionary or None
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT thread_id, created_at, updated_at, title, user_id
            FROM threads
            WHERE thread_id = ?
        """,
            (thread_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "thread_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "title": row[3],
            "user_id": row[4],
        }

    def delete_thread(self, thread_id: str) -> None:
        """
        Delete thread metadata.

        Args:
            thread_id: Thread identifier
        """
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
        conn.commit()
        conn.close()
