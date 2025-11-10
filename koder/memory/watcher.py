"""File watching system for automatic re-indexing."""

import asyncio
import time
from pathlib import Path
from typing import Optional, Set

from koder.config.settings import get_settings
from koder.memory.embeddings import GoogleEmbeddings
from koder.memory.retrieval import CodebaseRetriever
from koder.memory.vector_store import VectorStore
from koder.observability.logging import get_logger

logger = get_logger(__name__)


class FileWatcher:
    """Watches for file changes and automatically updates embeddings."""

    def __init__(self, workspace_path: str, debounce_seconds: int = 2):
        """
        Initialize file watcher.

        Args:
            workspace_path: Path to workspace directory
            debounce_seconds: Seconds to wait before processing changes
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.debounce_seconds = debounce_seconds
        self._retriever: Optional[CodebaseRetriever] = None
        self._watching = False
        self._file_mtimes: dict[str, float] = {}
        self._pending_changes: Set[str] = set()
        self._last_scan = 0.0

        # Supported file patterns
        self.patterns = [
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.jsx",
            "**/*.tsx",
            "**/*.md",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
            "**/*.txt",
            "**/*.sql",
            "**/*.sh",
            "**/*.go",
            "**/*.rs",
            "**/*.java",
            "**/*.cpp",
            "**/*.c",
            "**/*.h",
            "**/*.dockerfile",
            "**/Dockerfile*",
        ]

        # Skip directories
        self.skip_dirs = {
            ".git",
            ".vscode",
            ".idea",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".env",
            "dist",
            "build",
            "target",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "coverage",
            ".next",
            ".nuxt",
            "site-packages",
            "spm-packages",
        }

    def _ensure_initialized(self):
        """Initialize the retriever on first use."""
        if self._retriever is not None:
            return

        try:
            settings = get_settings()

            # Initialize embedding system
            embeddings = GoogleEmbeddings(
                api_key=settings.embeddings.google_api_key,
                model=settings.embeddings.model,
            )

            # Initialize vector store
            vector_store = VectorStore(
                embeddings=embeddings,
                persist_directory=settings.storage.vector_store_path,
            )

            # Initialize retriever
            self._retriever = CodebaseRetriever(
                vector_store=vector_store, workspace_path=str(self.workspace_path)
            )

            logger.info("file_watcher_initialized", workspace=str(self.workspace_path))

        except Exception as e:
            logger.error("file_watcher_init_failed", error=str(e))
            self._retriever = None

    def _scan_files(self) -> Set[str]:
        """Scan workspace for tracked files."""
        tracked_files = set()

        for pattern in self.patterns:
            for file_path in self.workspace_path.glob(pattern):
                if file_path.is_file() and not any(
                    skip_dir in file_path.parts for skip_dir in self.skip_dirs
                ):
                    # Skip large files (>1MB)
                    try:
                        if file_path.stat().st_size <= 1024 * 1024:
                            rel_path = str(file_path.relative_to(self.workspace_path))
                            tracked_files.add(rel_path)
                    except (OSError, ValueError):
                        continue

        return tracked_files

    def _get_file_mtime(self, file_path: str) -> float:
        """Get file modification time."""
        try:
            full_path = self.workspace_path / file_path
            return full_path.stat().st_mtime
        except OSError:
            return 0.0

    def _detect_changes(self) -> tuple[Set[str], Set[str]]:
        """
        Detect file changes since last scan.

        Returns:
            Tuple of (changed_files, removed_files)
        """
        current_files = self._scan_files()
        changed_files = set()
        removed_files = set()

        # Check for changed files
        for file_path in current_files:
            mtime = self._get_file_mtime(file_path)
            old_mtime = self._file_mtimes.get(file_path, 0.0)

            if mtime > old_mtime:
                changed_files.add(file_path)
                self._file_mtimes[file_path] = mtime

        # Check for removed files
        for file_path in self._file_mtimes.keys():
            if file_path not in current_files:
                removed_files.add(file_path)

        # Clean up removed files from mtime tracking
        for file_path in removed_files:
            del self._file_mtimes[file_path]

        return changed_files, removed_files

    def _process_changes(self, changed_files: Set[str], removed_files: Set[str]):
        """Process detected file changes."""
        if not changed_files and not removed_files:
            return

        self._ensure_initialized()
        if not self._retriever:
            return

        try:
            # Remove embeddings for deleted files
            for file_path in removed_files:
                try:
                    self._retriever.vector_store.delete(where={"file_path": file_path})
                    logger.info("file_removed_from_index", file_path=file_path)
                except Exception as e:
                    logger.error(
                        "file_removal_failed", file_path=file_path, error=str(e)
                    )

            # Re-index changed files
            for file_path in changed_files:
                try:
                    # Remove old embeddings for this file
                    self._retriever.vector_store.delete(where={"file_path": file_path})

                    # Add new embeddings
                    ids = self._retriever.index_file(file_path, chunk_size=1500)
                    if ids:
                        logger.info(
                            "file_reindexed", file_path=file_path, chunks=len(ids)
                        )
                except Exception as e:
                    logger.error(
                        "file_reindex_failed", file_path=file_path, error=str(e)
                    )

            if changed_files or removed_files:
                logger.info(
                    "index_updated",
                    changed_count=len(changed_files),
                    removed_count=len(removed_files),
                )

        except Exception as e:
            logger.error("change_processing_failed", error=str(e))

    def start_watching(self):
        """Start watching for file changes."""
        if self._watching:
            return

        self._watching = True
        logger.info("file_watching_started", workspace=str(self.workspace_path))

        # Initial scan
        self._file_mtimes = {
            file_path: self._get_file_mtime(file_path)
            for file_path in self._scan_files()
        }

        # Start background task
        asyncio.create_task(self._watch_loop())

    def stop_watching(self):
        """Stop watching for file changes."""
        self._watching = False
        logger.info("file_watching_stopped", workspace=str(self.workspace_path))

    async def _watch_loop(self):
        """Main watching loop."""
        while self._watching:
            try:
                current_time = time.time()

                # Debounce - don't scan too frequently
                if current_time - self._last_scan >= self.debounce_seconds:
                    changed_files, removed_files = self._detect_changes()

                    if changed_files or removed_files:
                        # Add to pending changes
                        self._pending_changes.update(changed_files)
                        self._pending_changes.update(removed_files)

                        # Process changes after debounce delay
                        await asyncio.sleep(self.debounce_seconds)

                        if self._pending_changes:
                            self._process_changes(self._pending_changes, set())
                            self._pending_changes.clear()

                    self._last_scan = current_time

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error("watch_loop_error", error=str(e))
                await asyncio.sleep(5)  # Wait longer on error

    def force_reindex(self, file_paths: Optional[list[str]] = None):
        """Force re-indexing of specific files or all files."""
        self._ensure_initialized()
        if not self._retriever:
            return

        try:
            if file_paths:
                # Re-index specific files
                for file_path in file_paths:
                    try:
                        # Remove old embeddings
                        self._retriever.vector_store.delete(
                            where={"file_path": file_path}
                        )

                        # Add new embeddings
                        ids = self._retriever.index_file(file_path, chunk_size=1500)
                        if ids:
                            logger.info(
                                "file_force_reindexed",
                                file_path=file_path,
                                chunks=len(ids),
                            )
                    except Exception as e:
                        logger.error(
                            "file_force_reindex_failed",
                            file_path=file_path,
                            error=str(e),
                        )
            else:
                # Re-index all files
                tracked_files = self._scan_files()
                for file_path in tracked_files:
                    try:
                        self._retriever.vector_store.delete(
                            where={"file_path": file_path}
                        )
                        ids = self._retriever.index_file(file_path, chunk_size=1500)
                        if ids:
                            logger.debug("file_reindexed_full", file_path=file_path)
                    except Exception:
                        continue

                logger.info("full_reindex_completed", files_count=len(tracked_files))

        except Exception as e:
            logger.error("force_reindex_failed", error=str(e))


class FileWatcherManager:
    """Manages multiple file watchers."""

    def __init__(self):
        """Initialize watcher manager."""
        self._watchers: dict[str, FileWatcher] = {}

    def get_watcher(self, workspace_path: str) -> FileWatcher:
        """Get or create a watcher for a workspace."""
        workspace_key = str(Path(workspace_path).resolve())

        if workspace_key not in self._watchers:
            self._watchers[workspace_key] = FileWatcher(workspace_path)

        return self._watchers[workspace_key]

    def start_watching(self, workspace_path: str):
        """Start watching a workspace."""
        watcher = self.get_watcher(workspace_path)
        watcher.start_watching()

    def stop_watching(self, workspace_path: str):
        """Stop watching a workspace."""
        workspace_key = str(Path(workspace_path).resolve())
        if workspace_key in self._watchers:
            self._watchers[workspace_key].stop_watching()

    def stop_all(self):
        """Stop all watchers."""
        for watcher in self._watchers.values():
            watcher.stop_watching()

    def force_reindex(
        self, workspace_path: str, file_paths: Optional[list[str]] = None
    ):
        """Force re-indexing for a workspace."""
        watcher = self.get_watcher(workspace_path)
        watcher.force_reindex(file_paths)


# Global watcher manager instance
watcher_manager = FileWatcherManager()
