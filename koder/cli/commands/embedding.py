"""Embedding management CLI commands."""

import os
import time
from pathlib import Path

import typer
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from koder.cli.ui.console import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from koder.config.settings import get_settings
from koder.memory.embeddings import GoogleEmbeddings
from koder.memory.metrics import get_metrics
from koder.memory.retrieval import CodebaseRetriever
from koder.memory.vector_store import VectorStore
from koder.memory.watcher import watcher_manager

app = typer.Typer(help="Manage semantic code embeddings for enhanced AI understanding")


@app.command()
def quickstart(
    workspace: str = typer.Option(
        ".",
        "--workspace",
        "-w",
        help="Workspace directory to set up for semantic search",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-initialization even if already set up"
    ),
):
    """Quick setup for semantic search - indexes entire workspace."""
    settings = get_settings()

    try:
        workspace_path = Path(workspace).resolve()
        print_info(f"Setting up semantic search for: {workspace_path}")

        # Check if already set up
        if os.path.exists(settings.storage.vector_store_path):
            if not force:
                # Check if there's existing data
                try:
                    embeddings = GoogleEmbeddings(
                        api_key=settings.embeddings.google_api_key,
                        model=settings.embeddings.model,
                    )
                    vector_store = VectorStore(
                        embeddings=embeddings,
                        persist_directory=settings.storage.vector_store_path,
                    )
                    doc_count = vector_store.count()
                    if doc_count > 0:
                        print_warning(f"Already found {doc_count} indexed documents.")
                        print_info(
                            "Use --force to re-index or run 'koder embedding search' to test."
                        )
                        return
                except Exception:
                    pass

        print_info("Starting workspace indexing...")

        # Initialize embedding system
        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        # Initialize vector store
        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Initialize retriever
        retriever = CodebaseRetriever(
            vector_store=vector_store, workspace_path=workspace
        )

        # Clear existing data if force
        if force:
            try:
                retriever.vector_store.clear()
                print_info("Cleared existing embeddings.")
            except Exception:
                pass

        # Define comprehensive file patterns
        patterns = [
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

        # Skip common non-source directories
        skip_dirs = {
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

        total_indexed = 0

        print_info("Scanning files...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # Count files
            all_files = []
            for pattern in patterns:
                files = [
                    f
                    for f in workspace_path.glob(pattern)
                    if f.is_file()
                    and not any(skip_dir in f.parts for skip_dir in skip_dirs)
                ]
                all_files.extend(files)

            # Remove duplicates
            all_files = list(set(all_files))
            progress_task = progress.add_task(
                "Indexing workspace...", total=len(all_files)
            )

            for file_path in all_files:
                try:
                    progress.advance(progress_task)
                    rel_path = file_path.relative_to(workspace_path)

                    # Skip large files
                    if file_path.stat().st_size > 1024 * 1024:  # 1MB
                        continue

                    # Index file
                    ids = retriever.index_file(str(rel_path), chunk_size=1500)
                    if ids:
                        total_indexed += 1

                except Exception:
                    continue

        final_count = retriever.vector_store.count()

        print_success("✅ Quick setup completed!")
        print_info(f"📁 Files indexed: {total_indexed}")
        print_info(f"📄 Total chunks: {final_count}")
        print_info(f"📂 Workspace: {workspace_path}")
        print_info("\n💡 Try these commands:")
        print_info("  koder embedding search 'your query here'")
        print_info("  koder chat start")
        print_info("  koder task run 'explain the codebase structure'")

    except Exception as e:
        print_error(f"Quick setup failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate():
    """Validate embedding system connectivity and performance."""
    import time

    print_info("Validating embedding system connectivity...")

    try:
        # Load settings and test embeddings
        settings = get_settings()

        # Create embeddings with validation
        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        # Test embedding generation
        start_time = time.time()
        test_text = "This is a test to validate Google embeddings connectivity."

        result = embeddings.embed_query(test_text)
        response_time = (time.time() - start_time) * 1000

        # Test vector store
        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Test vector store operations
        from langchain_core.documents import Document

        test_doc = Document(
            page_content="Test document for validation", metadata={"test": True}
        )

        doc_ids = vector_store.add_documents([test_doc])
        search_results = vector_store.similarity_search("test", k=1)

        # Clean up test document
        if doc_ids:
            vector_store.delete(doc_ids)

        validation = {
            "overall_status": "fully_operational"
            if result and search_results
            else "embeddings_failed",
            "embeddings": {
                "connected": True,
                "model": settings.embeddings.model,
                "test_embedding": {
                    "dimensions": len(result),
                    "first_5_values": result[:5],
                    "response_time_ms": round(response_time, 2),
                },
            },
            "vector_store": {
                "connected": bool(search_results),
                "documents_count": vector_store.count(),
                "test_addition": len(doc_ids) > 0,
                "test_search": len(search_results) > 0,
            },
        }

        # Create validation results table
        validation_table = Table(title="Embedding System Validation")
        validation_table.add_column("Component", style="cyan")
        validation_table.add_column("Status", style="green")
        validation_table.add_column("Details", style="white")

        # Overall status
        status_emoji = {
            "fully_operational": ("✅", "green"),
            "healthy": ("✅", "green"),
            "embeddings_failed": ("❌", "red"),
            "vector_store_failed": ("⚠️", "yellow"),
            "unknown": ("❓", "dim"),
        }

        overall_status = validation["overall_status"]
        emoji, color = status_emoji.get(overall_status, ("❓", "dim"))
        validation_table.add_row(
            "Overall System",
            f"[{color}]{emoji} {overall_status.replace('_', ' ').title()}[/{color}]",
            "Complete system validation",
        )

        # Google Embeddings
        emb = validation["embeddings"]
        if emb.get("connected"):
            test_emb = emb.get("test_embedding", {})
            emb_details = (
                f"Model: {emb.get('model', 'N/A')}\n"
                f"Dimensions: {test_emb.get('dimensions', 'N/A')}\n"
                f"Response: {test_emb.get('response_time_ms', 'N/A')}ms"
            )
            validation_table.add_row("Google Gemini", "✅ Connected", emb_details)
        else:
            validation_table.add_row(
                "Google Gemini", "❌ Failed", emb.get("error", "Unknown error")
            )

        # Vector Store
        vs = validation["vector_store"]
        if vs.get("connected"):
            vs_details = (
                f"Documents: {vs.get('documents_count', 0)}\n"
                f"Test Addition: {'✅' if vs.get('test_addition') else '❌'}\n"
                f"Test Search: {'✅' if vs.get('test_search') else '❌'}"
            )
            validation_table.add_row("Vector Store", "✅ Operational", vs_details)
        else:
            validation_table.add_row(
                "Vector Store", "❌ Failed", vs.get("error", "Unknown error")
            )

        console.print(validation_table)

        # Sample embedding values if available
        if emb.get("connected") and emb.get("test_embedding"):
            test_emb = emb["test_embedding"]
            console.print("\n[bold]📊 Sample Embedding Values:[/bold]")
            console.print(f"Model: {emb.get('model')}")
            console.print(f"Dimensions: {test_emb.get('dimensions')}")
            console.print(f"Response Time: {test_emb.get('response_time_ms')}ms")

            sample_vals = test_emb.get("first_5_values", [])
            if sample_vals:
                rounded_vals = [round(x, 6) for x in sample_vals]
                console.print(f"First 5 Values: {rounded_vals}")

        console.print(f"\n[dim]Validation completed at: {time.time()}[/dim]")

        # Final status message
        if overall_status == "fully_operational":
            print_success("🎉 Embedding system is fully operational!")
        elif overall_status == "healthy":
            print_success("✅ Embedding system is healthy")
        else:
            print_warning(f"⚠️  Embedding system needs attention: {overall_status}")

    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def watch(
    workspace: str = typer.Option(
        ".", "--workspace", "-w", help="Workspace directory to watch"
    ),
    debounce: int = typer.Option(
        2, "--debounce", "-d", help="Seconds to wait before processing file changes"
    ),
):
    """Watch for file changes and automatically update embeddings."""
    import asyncio
    import signal
    import sys

    workspace_path = Path(workspace).resolve()
    print_info(f"Watching for changes in: {workspace_path}")
    print_info(f"Debounce delay: {debounce} seconds")
    print_info("Press Ctrl+C to stop watching...")

    def signal_handler(sig, frame):
        print_info("\nStopping file watcher...")
        watcher_manager.stop_watching(workspace)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start watching
        watcher_manager.start_watching(workspace)

        # Run async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Just keep the loop running
            loop.run_forever()
        finally:
            loop.close()

    except KeyboardInterrupt:
        print_info("\nFile watcher stopped.")
    except Exception as e:
        print_error(f"File watching failed: {str(e)}")
        raise typer.Exit(1)
    finally:
        watcher_manager.stop_watching(workspace)


@app.command()
def index(
    workspace: str = typer.Option(
        ".", "--workspace", "-w", help="Workspace directory to index"
    ),
    pattern: str | None = typer.Option(
        None,
        "--pattern",
        "-p",
        help="File pattern to index (e.g., '**/*.py', '**/*.js'). If not specified, uses default patterns",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-indexing even if already indexed"
    ),
    chunk_size: int = typer.Option(
        1500, "--chunk-size", "-c", help="Text chunk size for processing"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Index files for semantic search."""
    settings = get_settings()

    try:
        # Initialize embedding system
        if verbose:
            print_info("Initializing embedding system...")

        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        # Initialize vector store
        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Initialize retriever
        retriever = CodebaseRetriever(
            vector_store=vector_store, workspace_path=workspace
        )

        # Check if already indexed
        doc_count = retriever.vector_store.count()
        if doc_count > 0 and not force:
            print_warning(
                f"Already indexed {doc_count} documents. Use --force to re-index."
            )
            return

        if force and doc_count > 0:
            if verbose:
                print_info("Clearing existing embeddings...")
            retriever.vector_store.clear()

        # Define file patterns
        if pattern:
            patterns = [pattern]
        else:
            patterns = [
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

        workspace_path = Path(workspace).resolve()

        # Skip common non-source directories

        print_info(f"Indexing workspace: {workspace_path}")

        if verbose:
            print_info(
                "Using incremental indexing (only changed files will be processed)"
            )

        time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            progress_task = progress.add_task("Indexing workspace...", total=100)

            # Use smart incremental indexing
            stats = retriever.smart_index_directory(
                directory_path=".",
                patterns=patterns,
                chunk_size=chunk_size,
                force=force,  # Force re-indexing if specified
            )

            progress.update(progress_task, completed=100)

        # Report results
        elapsed_time = stats["duration"]

        console.print("\n[bold green]✅ Indexing completed![/bold green]")
        console.print(f"📁 Files found: {stats['total_files_found']}")
        console.print(f"📝 Files updated: {stats['updated_files']}")
        console.print(f"⏭️  Files skipped: {stats['skipped_files']}")
        console.print(f"📄 Total chunks: {stats['total_chunks']}")
        console.print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
        console.print(f"🚫 Errors: {stats['error_files']}")

        if verbose and stats["error_files"] > 0:
            console.print("\n[dim]Some files encountered errors during indexing.[/dim]")
            console.print("[dim]Use --verbose to see detailed error information.[/dim]")

    except Exception as e:
        print_error(f"Indexing failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    max_results: int = typer.Option(
        5, "--max-results", "-k", help="Maximum number of results"
    ),
    file_filter: str | None = typer.Option(
        None, "--file-filter", "-f", help="Filter results by file pattern"
    ),
    show_content: bool = typer.Option(
        True, "--show-content/--no-show-content", help="Show file content in results"
    ),
):
    """Search indexed code using semantic search."""
    settings = get_settings()

    try:
        # Initialize embedding system
        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        # Initialize vector store
        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Initialize retriever
        retriever = CodebaseRetriever(
            vector_store=vector_store, workspace_path=workspace
        )

        # Check if anything is indexed
        doc_count = retriever.vector_store.count()
        if doc_count == 0:
            print_warning(
                "No indexed documents found. Run 'koder embedding index' first."
            )
            return

        print_info(f"Searching for: '{query}'")
        print_info(f"Indexed documents: {doc_count}")

        # Perform search
        results = retriever.search_code(query, k=max_results, file_filter=file_filter)

        if not results:
            print_warning("No results found.")
            return

        # Display results
        console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")

        for i, doc in enumerate(results, 1):
            file_path = doc.metadata.get("file_path", "unknown")
            chunk_idx = doc.metadata.get("chunk_index", 0)
            total_chunks = doc.metadata.get("total_chunks", 1)

            console.print(
                f"[cyan]{i}. {file_path}[/cyan] (chunk {chunk_idx + 1}/{total_chunks})"
            )

            if show_content:
                console.print("[dim]" + "=" * 60 + "[/dim]")
                # Truncate very long content
                content = doc.page_content
                if len(content) > 800:
                    content = content[:800] + "...\n[truncated]"
                console.print(content)
                console.print("[dim]" + "=" * 60 + "[/dim]\n")
            else:
                console.print()

    except Exception as e:
        print_error(f"Search failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def status(
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed file information"
    ),
):
    """Show embedding system status."""
    settings = get_settings()

    try:
        # Initialize embedding system
        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        # Initialize vector store
        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Get collection info
        collection = vector_store.get_collection()
        doc_count = collection.count()

        # Create status table
        table = Table(title="Embedding System Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Model", settings.embeddings.model)
        table.add_row("Dimension", str(settings.embeddings.dimension))
        table.add_row("Workspace", str(Path(workspace).resolve()))
        table.add_row("Vector Store", settings.storage.vector_store_path)
        table.add_row("Total Documents", str(doc_count))

        console.print(table)

        if doc_count > 0 and details:
            console.print("\n[bold]File Types:[/bold]")

            # Get file type statistics
            try:
                # This is a simplified approach - in a real implementation,
                # you'd query the metadata more efficiently
                sample_docs = collection.get(limit=1000, include=["metadatas"])
                file_types = {}

                for metadata in sample_docs.get("metadatas", []):
                    file_path = metadata.get("file_path", "")
                    if file_path:
                        ext = Path(file_path).suffix or "no_extension"
                        file_types[ext] = file_types.get(ext, 0) + 1

                for ext, count in sorted(
                    file_types.items(), key=lambda x: x[1], reverse=True
                ):
                    console.print(f"  {ext or 'no_ext'}: {count} chunks")

            except Exception:
                console.print("  Unable to retrieve file type details")

        if doc_count == 0:
            console.print("\n[bold yellow]💡 No indexed documents found.[/bold yellow]")
            console.print(
                "Run 'koder embedding index' to start indexing your codebase."
            )

    except Exception as e:
        print_error(f"Status check failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def clear(
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    confirm: bool = typer.Option(
        False, "--confirm", "-y", help="Skip confirmation prompt"
    ),
):
    """Clear all indexed embeddings."""
    if not confirm:
        if not typer.confirm(
            "⚠️  This will delete all indexed embeddings. Are you sure?"
        ):
            print_info("Operation cancelled.")
            return

    try:
        settings = get_settings()

        # Initialize vector store
        embeddings = GoogleEmbeddings(
            api_key=settings.embeddings.google_api_key, model=settings.embeddings.model
        )

        vector_store = VectorStore(
            embeddings=embeddings, persist_directory=settings.storage.vector_store_path
        )

        # Clear embeddings
        vector_store.clear()

        print_success("✅ All embeddings cleared successfully.")

    except Exception as e:
        print_error(f"Clear failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def metrics(
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace directory"),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed metrics"
    ),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset all metrics"),
):
    """Show embedding system metrics and performance data."""
    if reset:
        if typer.confirm("⚠️  This will reset all embedding metrics. Are you sure?"):
            metrics_tracker = get_metrics(workspace)
            metrics_tracker.reset_metrics()
            print_success("✅ Metrics reset successfully.")
        return

    try:
        metrics_tracker = get_metrics(workspace)
        summary = metrics_tracker.get_summary()

        if "error" in summary:
            print_error(f"Failed to get metrics: {summary['error']}")
            return

        # Create main metrics table
        console.print("\n[bold]📊 Embedding Metrics Summary[/bold]\n")

        # Overview table
        overview_table = Table(title="Overview", show_header=False)
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")

        overview_table.add_row("Workspace", summary["workspace"])
        overview_table.add_row(
            "Health Status", _get_health_status_display(summary["health"])
        )
        overview_table.add_row("Last Updated", summary["last_updated"][:19] + "Z")
        overview_table.add_row(
            "Total Chunks", str(summary["documents"]["total_chunks"])
        )

        console.print(overview_table)

        # Performance table
        console.print("\n[bold]⚡ Performance[/bold]")
        perf_table = Table()
        perf_table.add_column("Operation", style="cyan")
        perf_table.add_column("Count", style="white")
        perf_table.add_column("Avg Time", style="yellow")
        perf_table.add_column("Total Time", style="green")

        perf_table.add_row(
            "Indexing",
            str(summary["performance"]["indexing"]["files_indexed"]),
            f"{summary['performance']['indexing']['average_time']:.2f}s",
            f"{summary['performance']['indexing']['total_time']:.1f}s",
        )
        perf_table.add_row(
            "Searching",
            str(summary["performance"]["searching"]["total_searches"]),
            f"{summary['performance']['searching']['average_time']:.2f}s",
            "N/A",
        )

        console.print(perf_table)

        # Recent activity
        console.print("\n[bold]📈 Recent Activity (7 days)[/bold]")
        activity_table = Table(show_header=False)
        activity_table.add_column("Activity", style="cyan")
        activity_table.add_column("Count", style="white")

        activity_table.add_row(
            "Files Indexed", str(summary["recent_activity"]["indexing"])
        )
        activity_table.add_row("Searches", str(summary["recent_activity"]["searching"]))
        activity_table.add_row("Errors", str(summary["recent_activity"]["errors"]))

        console.print(activity_table)

        # File types
        if summary["documents"]["file_types"]:
            console.print("\n[bold]📁 File Types[/bold]")
            file_types_table = Table()
            file_types_table.add_column("Extension", style="cyan")
            file_types_table.add_column("Chunks", style="white")

            for ext, count in list(summary["documents"]["file_types"].items())[:10]:
                display_ext = ext or "no_ext"
                file_types_table.add_row(display_ext, str(count))

            console.print(file_types_table)

        # Health issues and warnings
        if summary["issues"]:
            console.print("\n[bold red]❌ Health Issues[/bold red]")
            for issue in summary["issues"]:
                console.print(f"  • {issue}")

        if summary["warnings"]:
            console.print("\n[bold yellow]⚠️  Warnings[/bold yellow]")
            for warning in summary["warnings"]:
                console.print(f"  • {warning}")

        if not summary["issues"] and not summary["warnings"]:
            console.print("\n[bold green]✅ No issues detected[/bold green]")

        # Detailed metrics
        if detailed:
            console.print("\n[bold]🔍 Detailed Metrics[/bold]")
            console.print(f"[dim]Metrics file: {metrics_tracker.metrics_file}[/dim]")

            # Show daily stats for last few days
            console.print("\n[bold]Daily Activity[/bold]")
            daily_table = Table()
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Files", style="white")
            daily_table.add_row("Searches", style="white")
            daily_table.add_row("Duration", style="yellow")

            # Get last 5 days of data
            daily_stats = metrics_tracker.metrics.get("daily_stats", {})
            recent_dates = sorted(daily_stats.keys(), reverse=True)[:5]

            for date in recent_dates:
                stats = daily_stats[date]
                daily_table.add_row(
                    date,
                    str(stats.get("files_processed", 0)),
                    str(stats.get("searches", 0)),
                    f"{stats.get('duration', 0):.1f}s",
                )

            console.print(daily_table)

    except Exception as e:
        print_error(f"Metrics display failed: {str(e)}")
        raise typer.Exit(1)


def _get_health_status_display(status: str) -> str:
    """Get colored health status display."""
    status_colors = {
        "healthy": ("✅ Healthy", "green"),
        "degraded": ("⚠️  Degraded", "yellow"),
        "unhealthy": ("❌ Unhealthy", "red"),
        "error": ("🔥 Error", "red"),
        "unknown": ("❓ Unknown", "dim"),
    }

    text, color = status_colors.get(status, status_colors["unknown"])
    return f"[{color}]{text}[/{color}]"


@app.command()
def mode(
    mode: str | None = typer.Argument(
        None, help="Set retrieval mode: off, lexical, primary, reranker"
    ),
):
    """View or change the retrieval mode."""
    settings = get_settings()

    if mode is None:
        # Display current mode
        console.print(
            f"\n[bold]Current Retrieval Mode:[/bold] [cyan]{settings.embeddings.mode}[/cyan]\n"
        )

        console.print("[bold]Available Modes:[/bold]")
        console.print(
            "  • [cyan]off[/cyan]      - No retrieval (fastest, baseline for testing)"
        )
        console.print(
            "  • [cyan]lexical[/cyan]  - Keyword search only (fast, free, good for exact matches)"
        )
        console.print(
            "  • [cyan]primary[/cyan]  - Embeddings only (semantic search, higher cost)"
        )
        console.print(
            "  • [cyan]reranker[/cyan] - Hybrid: lexical + embedding re-rank [green](recommended)[/green]\n"
        )

        console.print("[bold]Settings:[/bold]")
        console.print(f"  Enabled: {settings.embeddings.enabled}")
        console.print(f"  Monthly Budget: ${settings.embeddings.max_monthly_cost_usd}")
        console.print(
            f"  Daily API Limit: {settings.embeddings.max_daily_api_calls} calls\n"
        )
    else:
        # Validate and set mode
        valid_modes = ["off", "lexical", "primary", "reranker"]
        if mode not in valid_modes:
            print_error(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"
            )
            raise typer.Exit(1)

        print_info(f"To change mode, set environment variable: EMBEDDINGS_MODE={mode}")
        print_info(f"Or update your .env file with: EMBEDDINGS_MODE={mode}")
        print_success(f"Current mode: {settings.embeddings.mode}")


@app.command()
def cost():
    """Show API cost tracking and budget status."""
    from koder.memory.cost_tracker import get_cost_tracker

    try:
        tracker = get_cost_tracker()
        stats = tracker.get_usage_stats(days=30)

        console.print("\n[bold]💰 Cost Tracking & Budget Status[/bold]\n")

        # Budget status
        budget_table = Table(title="Budget Status")
        budget_table.add_column("Metric", style="cyan")
        budget_table.add_column("Value", style="green")
        budget_table.add_column("Limit", style="yellow")
        budget_table.add_column("Status", style="white")

        today_calls = stats["budget"]["today_calls"]
        max_daily = stats["budget"]["max_daily_calls"]
        daily_pct = (today_calls / max(max_daily, 1)) * 100
        daily_status = "✅" if daily_pct < 80 else "⚠️" if daily_pct < 100 else "❌"

        month_cost = stats["budget"]["month_cost_usd"]
        max_monthly = stats["budget"]["max_monthly_cost_usd"]
        monthly_pct = (month_cost / max(max_monthly, 0.01)) * 100
        monthly_status = (
            "✅" if monthly_pct < 80 else "⚠️" if monthly_pct < 100 else "❌"
        )

        budget_table.add_row(
            "Today's API Calls",
            str(today_calls),
            str(max_daily),
            f"{daily_status} {daily_pct:.0f}%",
        )
        budget_table.add_row(
            "Month's Cost",
            f"${month_cost:.4f}",
            f"${max_monthly:.2f}",
            f"{monthly_status} {monthly_pct:.0f}%",
        )

        console.print(budget_table)

        # Usage stats
        console.print("\n[bold]📊 Usage Statistics (Last 30 Days)[/bold]")
        stats_table = Table()
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Total API Requests", str(stats["total_requests"]))
        stats_table.add_row("Total API Calls", str(stats["total_calls"]))
        stats_table.add_row("Total Cost", f"${stats['total_cost_usd']:.4f}")
        stats_table.add_row("Avg Daily Calls", f"{stats['avg_daily_calls']:.1f}")
        stats_table.add_row("Avg Daily Cost", f"${stats['avg_daily_cost_usd']:.4f}")

        console.print(stats_table)

        # Calls by mode
        if stats["calls_by_mode"]:
            console.print("\n[bold]🔍 Calls by Mode[/bold]")
            mode_table = Table()
            mode_table.add_column("Mode", style="cyan")
            mode_table.add_column("Calls", style="white")
            mode_table.add_column("Percentage", style="yellow")

            total_mode_calls = sum(stats["calls_by_mode"].values())
            for mode, calls in sorted(
                stats["calls_by_mode"].items(), key=lambda x: x[1], reverse=True
            ):
                pct = (calls / max(total_mode_calls, 1)) * 100
                mode_table.add_row(mode or "unknown", str(calls), f"{pct:.1f}%")

            console.print(mode_table)

        # Warnings
        if daily_pct >= 80:
            console.print(
                f"\n[yellow]⚠️  Warning: Daily API call limit at {daily_pct:.0f}%[/yellow]"
            )
        if monthly_pct >= 80:
            console.print(
                f"\n[yellow]⚠️  Warning: Monthly cost budget at {monthly_pct:.0f}%[/yellow]"
            )

        if daily_pct >= 100 or monthly_pct >= 100:
            console.print(
                "\n[red]❌ Budget limit exceeded! API calls will be blocked.[/red]"
            )
            console.print(
                "[dim]Adjust limits with EMBEDDINGS_MAX_DAILY_API_CALLS or EMBEDDINGS_MAX_MONTHLY_COST_USD[/dim]"
            )

    except Exception as e:
        print_error(f"Failed to get cost stats: {str(e)}")
        raise typer.Exit(1)


@app.command()
def compare(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze"),
):
    """Show A/B test comparison between retrieval modes."""
    from koder.memory.ab_test import get_ab_test_manager

    try:
        ab_manager = get_ab_test_manager()

        if not ab_manager.enabled:
            print_warning("A/B testing is currently disabled")
            print_info("Enable with: EMBEDDINGS_AB_TEST_ENABLED=true")
            return

        # Generate and display report
        report = ab_manager.generate_comparison_report(days=days)
        console.print(report)

        # Show configuration
        console.print("\n[bold]Configuration:[/bold]")
        console.print(
            f"  A/B Testing: {'✅ Enabled' if ab_manager.enabled else '❌ Disabled'}"
        )
        console.print(f"  Treatment Ratio: {ab_manager.ratio:.0%}")
        console.print(f"  Period: Last {days} days\n")

    except Exception as e:
        print_error(f"Failed to generate comparison: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
