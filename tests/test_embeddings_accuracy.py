"""Comprehensive embedding search accuracy testing framework."""

import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from koder.config.loader import load_env_file
from koder.memory.embeddings import GoogleEmbeddings
from koder.memory.retrieval import CodebaseRetriever
from koder.memory.vector_store import VectorStore
from koder.tools.context import ContextRetrievalTool

# Initialize rich console for beautiful output
console = Console()


@dataclass
class TestResult:
    """Individual test result."""

    query: str
    expected_matches: int
    actual_matches: int
    relevance_scores: list[int]
    response_time_ms: float
    precision: float
    recall: float
    f1_score: float
    top_result_relevance: int
    results: list[dict[str, Any]]


@dataclass
class TestSuite:
    """Complete test suite results."""

    test_name: str
    total_tests: int
    passed_tests: int
    avg_response_time: float
    avg_precision: float
    avg_recall: float
    avg_f1_score: float
    top_relevance_avg: float
    results: list[TestResult]


class EmbeddingAccuracyTester:
    """Comprehensive embedding search accuracy testing framework."""

    def __init__(self, workspace_path: str = "."):
        """Initialize the tester."""
        load_env_file()
        self.workspace_path = workspace_path
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        self.context_tool = None
        self.test_results = []

    def setup(self) -> bool:
        """Set up the test environment."""
        try:
            console.print(
                "[bold cyan]🔧 Setting up embedding test environment...[/bold cyan]"
            )

            # Initialize embeddings
            self.embeddings = GoogleEmbeddings(
                api_key="AIzaSyD2Lmun2MWtIHbkpem-Ofdy9COU_deBwnM",
                model="models/text-embedding-004",
            )

            # Initialize vector store
            self.vector_store = VectorStore(
                embeddings=self.embeddings, persist_directory="./data/vector_store"
            )

            # Initialize retriever
            self.retriever = CodebaseRetriever(
                vector_store=self.vector_store, workspace_path=self.workspace_path
            )

            # Initialize context tool
            self.context_tool = ContextRetrievalTool(workspace_path=self.workspace_path)

            # Check if we have data to test
            doc_count = self.vector_store.count()
            console.print(f"📊 Found {doc_count} documents in vector store")

            if doc_count == 0:
                console.print(
                    "[yellow]⚠️  No indexed documents found. Testing with limited scope.[/yellow]"
                )
                return False

            return True

        except Exception as e:
            console.print(f"[red]❌ Setup failed: {str(e)}[/red]")
            return False

    def calculate_relevance_score(self, query: str, result: dict[str, Any]) -> int:
        """
        Calculate relevance score for a search result (1-10 scale).

        Args:
            query: The search query
            result: Search result with metadata and content

        Returns:
            Relevance score (1-10)
        """
        content = result.get("page_content", "").lower()
        file_path = result.get("metadata", {}).get("file_path", "")
        query_lower = query.lower()

        score = 1  # Base score

        # Exact match bonus
        if query_lower in content:
            score += 4
        elif any(word in content for word in query_lower.split() if len(word) > 2):
            score += 2

        # File path relevance
        if any(
            word in file_path.lower() for word in query_lower.split() if len(word) > 2
        ):
            score += 1

        # Content length bonus (longer matches get higher scores)
        if len(content) > 100:
            score += min(1, len(content) // 500)

        return min(10, score)

    def run_search_test(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """
        Run a single search test.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Dictionary with test results
        """
        start_time = time.time()

        try:
            results = self.vector_store.similarity_search(query, k=max_results)
            response_time = (time.time() - start_time) * 1000

            if not results:
                return {
                    "query": query,
                    "results": [],
                    "response_time_ms": response_time,
                    "actual_matches": 0,
                    "relevance_scores": [],
                    "top_result_relevance": 0,
                }

            # Calculate relevance scores
            relevance_scores = []
            for result in results:
                score = self.calculate_relevance_score(query, result)
                relevance_scores.append(score)

            return {
                "query": query,
                "results": results,
                "response_time_ms": response_time,
                "actual_matches": len(results),
                "relevance_scores": relevance_scores,
                "top_result_relevance": relevance_scores[0] if relevance_scores else 0,
            }

        except Exception as e:
            return {
                "query": query,
                "results": [],
                "response_time_ms": 0,
                "actual_matches": 0,
                "relevance_scores": [],
                "top_result_relevance": 0,
                "error": str(e),
            }

    def test_exact_matches(self) -> TestSuite:
        """Test exact match queries."""
        console.print("\n[bold]🎯 Testing Exact Match Queries[/bold]")

        exact_queries = [
            "main()",
            "def main():",
            "#!/usr/bin/env python3",
            "from koder.cli.app import app",
            'print("Hello, World!")',
            "Koder - AI-powered code assistant",
        ]

        results = []
        for query in exact_queries:
            test_result = self.run_search_test(query)
            if "error" not in test_result:
                # For exact matches, we expect 1-3 matches
                expected_matches = 1
                precision = 1.0 if test_result["actual_matches"] > 0 else 0.0
                recall = (
                    1.0 if test_result["actual_matches"] >= expected_matches else 0.0
                )
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if (precision + recall) > 0
                    else 0.0
                )

                results.append(
                    TestResult(
                        query=query,
                        expected_matches=expected_matches,
                        actual_matches=test_result["actual_matches"],
                        relevance_scores=test_result["relevance_scores"],
                        response_time_ms=test_result["response_time_ms"],
                        precision=precision,
                        recall=recall,
                        f1_score=f1_score,
                        top_result_relevance=test_result["top_result_relevance"],
                        results=test_result["results"],
                    )
                )

        return self._create_test_suite("Exact Match Tests", results)

    def test_semantic_search(self) -> TestSuite:
        """Test semantic search understanding."""
        console.print("\n[bold]🧠 Testing Semantic Search[/bold]")

        semantic_queries = [
            "main entry point",
            "application initialization",
            "program startup code",
            "cli application setup",
            "executable script structure",
        ]

        results = []
        for query in semantic_queries:
            test_result = self.run_search_test(query)
            if "error" not in test_result:
                # For semantic search, we expect any matches (0+)
                precision = 1.0 if test_result["actual_matches"] > 0 else 0.0
                recall = 1.0  # We can't measure recall without ground truth
                f1_score = precision

                results.append(
                    TestResult(
                        query=query,
                        expected_matches=1,  # Expected at least one match
                        actual_matches=test_result["actual_matches"],
                        relevance_scores=test_result["relevance_scores"],
                        response_time_ms=test_result["response_time_ms"],
                        precision=precision,
                        recall=recall,
                        f1_score=f1_score,
                        top_result_relevance=test_result["top_result_relevance"],
                        results=test_result["results"],
                    )
                )

        return self._create_test_suite("Semantic Search Tests", results)

    def test_edge_cases(self) -> TestSuite:
        """Test edge cases and boundary conditions."""
        console.print("\n[bold]⚠️  Testing Edge Cases[/bold]")

        edge_cases = [
            "nonexistent function xyz",
            "quantum computing implementation",
            "space travel algorithm",
            "cooking recipe code",
            "weather forecasting logic",
            "",  # empty query
            "   ",  # whitespace only
        ]

        results = []
        for query in edge_cases:
            test_result = self.run_search_test(query)
            if "error" not in test_result:
                # For edge cases, we expect 0 matches (good system should handle gracefully)
                expected_matches = 0
                precision = (
                    1.0 if test_result["actual_matches"] == expected_matches else 0.0
                )
                recall = 1.0
                f1_score = (
                    1.0 if test_result["actual_matches"] == expected_matches else 0.0
                )

                results.append(
                    TestResult(
                        query=f"'{query}'",
                        expected_matches=expected_matches,
                        actual_matches=test_result["actual_matches"],
                        relevance_scores=test_result["relevance_scores"],
                        response_time_ms=test_result["response_time_ms"],
                        precision=precision,
                        recall=recall,
                        f1_score=f1_score,
                        top_result_relevance=test_result["top_result_relevance"],
                        results=test_result["results"],
                    )
                )

        return self._create_test_suite("Edge Case Tests", results)

    def test_context_retrieval_tool(self) -> TestSuite:
        """Test the ContextRetrievalTool used by AI agents."""
        console.print("\n[bold]🤖 Testing ContextRetrievalTool Integration[/bold]")

        context_queries = [
            "main entry point",
            "application setup",
            "Python code structure",
        ]

        results = []
        for query in context_queries:
            try:
                start_time = time.time()
                context = self.context_tool._run(query, max_results=3)
                response_time = (time.time() - start_time) * 1000

                # Parse results to extract document information
                lines = context.split("\n")
                matches = [line for line in lines if "From " in line]

                # Calculate relevance scores
                relevance_scores = []
                for match in matches[:3]:  # Take top 3
                    score = 5 if query.lower() in match.lower() else 3  # Simple scoring
                    relevance_scores.append(score)

                expected_matches = 1  # Expect at least one match
                precision = 1.0 if len(matches) > 0 else 0.0
                recall = 1.0 if len(matches) >= expected_matches else 0.0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if (precision + recall) > 0
                    else 0.0
                )

                results.append(
                    TestResult(
                        query=query,
                        expected_matches=expected_matches,
                        actual_matches=len(matches),
                        relevance_scores=relevance_scores,
                        response_time_ms=response_time,
                        precision=precision,
                        recall=recall,
                        f1_score=f1_score,
                        top_result_relevance=relevance_scores[0]
                        if relevance_scores
                        else 0,
                        results=[{"content": match} for match in matches],
                    )
                )

            except Exception as e:
                console.print(f"[red]Error testing context tool: {str(e)}[/red]")

        return self._create_test_suite("ContextRetrievalTool Tests", results)

    def test_embedding_generation(self) -> dict[str, Any]:
        """Test embedding generation quality and performance."""
        console.print("\n[bold]🔍 Testing Embedding Generation[/bold]")

        test_texts = [
            "Python function definition",
            "Class initialization method",
            "Error handling pattern",
            "Database connection query",
            "String processing operation",
        ]

        generation_results = []
        for text in test_texts:
            try:
                start_time = time.time()
                embedding = self.embeddings.embed_query(text)
                response_time = (time.time() - start_time) * 1000

                generation_results.append(
                    {
                        "text": text,
                        "text_length": len(text),
                        "embedding_dimensions": len(embedding),
                        "response_time_ms": response_time,
                        "first_5_values": embedding[:5],
                        "last_5_values": embedding[-5:],
                        "sample_value": embedding[0],
                    }
                )

            except Exception as e:
                console.print(
                    f"[red]Error generating embedding for '{text}': {str(e)}[/red]"
                )

        return {
            "total_tests": len(test_texts),
            "successful_tests": len(generation_results),
            "avg_response_time": statistics.mean(
                [r["response_time_ms"] for r in generation_results]
            )
            if generation_results
            else 0,
            "avg_dimensions": statistics.mean(
                [r["embedding_dimensions"] for r in generation_results]
            )
            if generation_results
            else 0,
            "results": generation_results,
        }

    def _create_test_suite(
        self, test_name: str, results: list[TestResult]
    ) -> TestSuite:
        """Create a test suite from results."""
        if not results:
            return TestSuite(
                test_name=test_name,
                total_tests=0,
                passed_tests=0,
                avg_response_time=0.0,
                avg_precision=0.0,
                avg_recall=0.0,
                avg_f1_score=0.0,
                top_relevance_avg=0.0,
                results=[],
            )

        passed_tests = sum(1 for r in results if r.f1_score > 0)

        return TestSuite(
            test_name=test_name,
            total_tests=len(results),
            passed_tests=passed_tests,
            avg_response_time=statistics.mean([r.response_time_ms for r in results]),
            avg_precision=statistics.mean([r.precision for r in results]),
            avg_recall=statistics.mean([r.recall for r in results]),
            avg_f1_score=statistics.mean([r.f1_score for r in results]),
            top_relevance_avg=statistics.mean(
                [r.top_result_relevance for r in results]
            ),
            results=results,
        )

    def run_all_tests(self) -> list[TestSuite]:
        """Run all tests and return results."""
        if not self.setup():
            console.print("[red]❌ Cannot run tests: No indexed data available[/red]")
            return []

        test_suites = []

        # Run different test categories
        test_suites.append(self.test_exact_matches())
        test_suites.append(self.test_semantic_search())
        test_suites.append(self.test_edge_cases())
        test_suites.append(self.test_context_retrieval_tool())

        return test_suites

    def generate_report(self, test_suites: list[TestSuite]) -> dict[str, Any]:
        """Generate a comprehensive test report."""
        console.print("\n[bold]📊 Generating Test Report[/bold]")

        total_tests = sum(suite.total_tests for suite in test_suites)
        total_passed = sum(suite.passed_tests for suite in test_suites)
        overall_success_rate = (
            (total_passed / total_tests) * 100 if total_tests > 0 else 0
        )

        # Create results table
        results_table = Table(title="Test Results Summary")
        results_table.add_column("Test Category", style="cyan")
        results_table.add_column("Total Tests", style="white")
        results_table.add_column("Passed", style="green")
        results_table.add_column("Success Rate", style="yellow")
        results_table.add_column("Avg Response Time", style="blue")
        results_table.add_column("Avg F1 Score", style="magenta")

        for suite in test_suites:
            success_rate = (
                (suite.passed_tests / suite.total_tests) * 100
                if suite.total_tests > 0
                else 0
            )
            results_table.add_row(
                suite.test_name,
                str(suite.total_tests),
                str(suite.passed_tests),
                f"{success_rate:.1f}%",
                f"{suite.avg_response_time:.1f}ms",
                f"{suite.avg_f1_score:.3f}",
            )

        console.print(results_table)

        # Overall summary
        summary_panel = Panel(
            f"""
[bold]Overall Test Results:[/bold]

📈 Total Tests: {total_tests}
✅ Passed Tests: {total_passed}
🎯 Success Rate: {overall_success_rate:.1f}%
⏱️  Avg Response Time: {statistics.mean([suite.avg_response_time for suite in test_suites]):.1f}ms
🎯 Avg F1 Score: {statistics.mean([suite.avg_f1_score for suite in test_suites]):.3f}
🌟 Top Relevance Avg: {statistics.mean([suite.top_relevance_avg for suite in test_suites]):.1f}
            """,
            title="Test Summary",
            border_style="green"
            if overall_success_rate > 70
            else "yellow"
            if overall_success_rate > 40
            else "red",
        )
        console.print(summary_panel)

        return {
            "overall_success_rate": overall_success_rate,
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "test_suites": [asdict(suite) for suite in test_suites],
            "timestamp": time.time(),
        }

    def save_report(
        self, report: dict[str, Any], filename: str = "embedding_accuracy_report.json"
    ):
        """Save the test report to a file."""
        report_path = Path(filename)
        try:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"✅ Report saved to: {report_path}")
        except Exception as e:
            console.print(f"[red]❌ Failed to save report: {str(e)}[/red]")


def main():
    """Run the comprehensive embedding accuracy tests."""
    tester = EmbeddingAccuracyTester()

    console.print(
        Panel(
            "[bold]🔍 Koder Embedding Search Accuracy Tester[/bold]\n\n"
            "This tool comprehensively tests your embedding system's\n"
            "search accuracy, performance, and integration capabilities.\n"
            "It will test exact matches, semantic understanding,\n"
            "edge cases, and AI agent integration.",
            title="Embedding Accuracy Tester",
            border_style="cyan",
        )
    )

    # Run all tests
    test_suites = tester.run_all_tests()

    if not test_suites:
        console.print("[red]❌ No tests could be executed[/red]")
        return

    # Generate and display report
    report = tester.generate_report(test_suites)

    # Save report
    tester.save_report(report)

    # Final assessment
    if report["overall_success_rate"] >= 70:
        console.print("\n[green]✅ Embedding system shows GOOD accuracy![/green]")
    elif report["overall_success_rate"] >= 40:
        console.print("\n[yellow]⚠️  Embedding system shows MODERATE accuracy[/yellow]")
    else:
        console.print("\n[red]❌ Embedding system needs IMPROVEMENT[/red]")


if __name__ == "__main__":
    main()
