"""Go code parsing and analysis tools."""

import re
from pathlib import Path
from typing import Any

from pydantic import Field

from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


@registry.register("code", needs_approval=False, is_read_only=True)
class ParseGoTool(ReadOnlyTool):
    """Parse and analyze Go code for structure, imports, and potential issues."""

    name: str = "parse_go_code"
    description: str = (
        "Parse Go code to extract package information, imports, functions, and types. "
        "Input should be either a file path or Go source code. "
        "Returns structured information about the Go code including potential issues."
    )

    def _run(self, input_text: str) -> str:
        """
        Parse Go code and extract structural information.

        Args:
            input_text: Either a file path or Go source code

        Returns:
            Structured analysis of the Go code
        """
        try:
            # Check if input is a file path
            file_path = Path(input_text)
            if file_path.exists() and file_path.suffix == '.go':
                with open(file_path, 'r', encoding='utf-8') as f:
                    go_code = f.read()
                source_info = f"File: {file_path}"
            else:
                go_code = input_text
                source_info = "Direct input"

            # Parse Go code structure
            analysis = self._analyze_go_code(go_code)
            analysis["source"] = source_info

            # Format results
            result = self._format_analysis(analysis)
            return result

        except Exception as e:
            return f"Error parsing Go code: {str(e)}"

    def _analyze_go_code(self, go_code: str) -> dict[str, Any]:
        """Analyze Go code structure and identify potential issues."""
        analysis = {
            "package": None,
            "imports": [],
            "functions": [],
            "types": [],
            "constants": [],
            "variables": [],
            "issues": [],
            "metrics": {}
        }

        lines = go_code.split('\n')
        in_multiline_comment = False
        in_import_block = False
        import_block_content = []

        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()

            # Skip empty lines and comments
            if not stripped_line:
                continue

            # Handle multiline comments
            if '/*' in stripped_line:
                in_multiline_comment = True
            if '*/' in stripped_line:
                in_multiline_comment = False
                continue
            if in_multiline_comment:
                continue

            # Skip single-line comments
            if stripped_line.startswith('//'):
                continue

            # Package declaration
            if stripped_line.startswith('package '):
                analysis["package"] = stripped_line.replace('package ', '').strip()

            # Import block handling
            if stripped_line.startswith('import') and stripped_line.endswith('{'):
                in_import_block = True
                continue
            if in_import_block:
                if stripped_line == '}':
                    in_import_block = False
                    # Process import block content
                    for import_line in import_block_content:
                        clean_import = import_line.strip().strip('"').strip("'")
                        if clean_import:
                            analysis["imports"].append(clean_import)
                    import_block_content = []
                    continue
                else:
                    import_block_content.append(stripped_line)
                    continue

            # Single import
            if stripped_line.startswith('import ') and not in_import_block:
                import_match = re.match(r'import\s+["\'](.+)["\']', stripped_line)
                if import_match:
                    analysis["imports"].append(import_match.group(1))

            # Function detection
            func_match = re.match(r'func\s+(\([^)]+\)\s+)?(\w+)', stripped_line)
            if func_match:
                func_name = func_match.group(2)
                receiver = func_match.group(1) if func_match.group(1) else None
                analysis["functions"].append({
                    "name": func_name,
                    "line": i,
                    "receiver": receiver
                })

            # Type detection (struct, interface)
            type_match = re.match(r'type\s+(\w+)\s+(\w+)', stripped_line)
            if type_match:
                analysis["types"].append({
                    "name": type_match.group(1),
                    "kind": type_match.group(2),
                    "line": i
                })

            # Constant detection
            const_match = re.match(r'const\s+(\w+)', stripped_line)
            if const_match:
                analysis["constants"].append({
                    "name": const_match.group(1),
                    "line": i
                })

            # Variable detection
            var_match = re.match(r'var\s+(\w+)', stripped_line)
            if var_match:
                analysis["variables"].append({
                    "name": var_match.group(1),
                    "line": i
                })

        # Basic issue detection
        self._detect_issues(go_code, analysis)

        # Calculate metrics
        analysis["metrics"] = {
            "total_lines": len(lines),
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('//')]),
            "comment_lines": len([l for l in lines if l.strip().startswith('//')]),
            "functions_count": len(analysis["functions"]),
            "imports_count": len(analysis["imports"]),
            "types_count": len(analysis["types"])
        }

        return analysis

    def _detect_issues(self, go_code: str, analysis: dict) -> None:
        """Detect potential issues in Go code."""
        lines = go_code.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for common Go issues
            if 'fmt.Println(' in stripped and '"' not in stripped and "'" not in stripped:
                analysis["issues"].append({
                    "type": "suspicious_print",
                    "line": i,
                    "message": "fmt.Println without string literals - might be debugging code"
                })

            # Check for error handling
            if re.search(r'[^{]\s+err\s*:?=', stripped) and i < len(lines):
                # Look for error checking in next few lines
                next_lines = lines[i:i+3]
                if not any('err != nil' in l for l in next_lines):
                    analysis["issues"].append({
                        "type": "missing_error_check",
                        "line": i,
                        "message": "Error assigned but not checked"
                    })

            # Check for potential nil pointer issues
            if '.' in stripped and 'nil' not in stripped:
                parts = stripped.split('.')
                if len(parts) > 1 and not any(keyword in stripped for keyword in ['if', 'for', 'switch']):
                    # Simple heuristic for potential nil access
                    analysis["issues"].append({
                        "type": "potential_nil_access",
                        "line": i,
                        "message": f"Potential nil pointer access: {stripped}"
                    })

    def _format_analysis(self, analysis: dict) -> str:
        """Format the analysis results."""
        result = []
        result.append("=== Go Code Analysis ===")
        result.append(f"Source: {analysis.get('source', 'Unknown')}")
        result.append("")

        # Package info
        if analysis["package"]:
            result.append(f"Package: {analysis['package']}")
            result.append("")

        # Imports
        if analysis["imports"]:
            result.append(f"Imports ({len(analysis['imports'])}):")
            for imp in analysis["imports"]:
                result.append(f"  - {imp}")
            result.append("")

        # Functions
        if analysis["functions"]:
            result.append(f"Functions ({len(analysis['functions'])}):")
            for func in analysis["functions"]:
                receiver_info = f" ({func['receiver']})" if func['receiver'] else ""
                result.append(f"  - {func['name']}{receiver_info} (line {func['line']})")
            result.append("")

        # Types
        if analysis["types"]:
            result.append(f"Types ({len(analysis['types'])}):")
            for type_info in analysis["types"]:
                result.append(f"  - {type_info['name']} ({type_info['kind']}) (line {type_info['line']})")
            result.append("")

        # Issues
        if analysis["issues"]:
            result.append(f"Potential Issues Found ({len(analysis['issues'])}):")
            for issue in analysis["issues"]:
                result.append(f"  ⚠️  {issue['type']} (line {issue['line']}): {issue['message']}")
            result.append("")

        # Metrics
        metrics = analysis["metrics"]
        result.append("Code Metrics:")
        result.append(f"  Total lines: {metrics['total_lines']}")
        result.append(f"  Code lines: {metrics['code_lines']}")
        result.append(f"  Functions: {metrics['functions_count']}")
        result.append(f"  Imports: {metrics['imports_count']}")
        result.append(f"  Types: {metrics['types_count']}")

        return "\n".join(result)


@registry.register("code", needs_approval=False, is_read_only=True)
class GoModAnalysisTool(ReadOnlyTool):
    """Analyze Go module dependencies and structure."""

    name: str = "analyze_go_mod"
    description: str = "Analyze go.mod file to extract module dependencies, Go version, and module structure."

    def _run(self, input_text: str) -> str:
        """
        Analyze go.mod file.

        Args:
            input_text: Path to go.mod file or directory containing it

        Returns:
            Analysis of Go module dependencies
        """
        try:
            # Handle directory or file path
            path = Path(input_text)
            if path.is_dir():
                go_mod_path = path / "go.mod"
            else:
                go_mod_path = path

            if not go_mod_path.exists():
                return f"go.mod file not found at {go_mod_path}"

            with open(go_mod_path, 'r') as f:
                content = f.read()

            # Parse go.mod
            module_info = self._parse_go_mod(content)
            module_info["path"] = str(go_mod_path)

            # Format results
            result = self._format_module_info(module_info)
            return result

        except Exception as e:
            return f"Error analyzing go.mod: {str(e)}"

    def _parse_go_mod(self, content: str) -> dict:
        """Parse go.mod file content."""
        info = {
            "module": None,
            "go_version": None,
            "dependencies": [],
            "replace": [],
            "exclude": []
        }

        lines = content.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('module '):
                info['module'] = line.replace('module ', '').strip()
            elif line.startswith('go '):
                info['go_version'] = line.replace('go ', '').strip()
            elif line.startswith('require ('):
                current_section = 'require'
            elif line.startswith('replace ('):
                current_section = 'replace'
            elif line.startswith('exclude ('):
                current_section = 'exclude'
            elif line == ')':
                current_section = None
            elif current_section == 'require' and line:
                parts = line.split()
                if len(parts) >= 2:
                    info['dependencies'].append({
                        'module': parts[0],
                        'version': parts[1]
                    })

        return info

    def _format_module_info(self, info: dict) -> str:
        """Format module information."""
        result = []
        result.append("=== Go Module Analysis ===")
        result.append(f"Module: {info.get('module', 'Unknown')}")
        result.append(f"Go Version: {info.get('go_version', 'Unknown')}")
        result.append(f"File: {info.get('path', 'Unknown')}")
        result.append("")

        if info['dependencies']:
            result.append(f"Dependencies ({len(info['dependencies'])}):")
            for dep in info['dependencies']:
                result.append(f"  - {dep['module']} {dep['version']}")
        else:
            result.append("No dependencies found")

        return "\n".join(result)