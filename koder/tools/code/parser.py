"""Code parsing tools using tree-sitter."""

from pathlib import Path
from typing import Any

import tree_sitter_python as tspython
from pydantic import Field
from tree_sitter import Language, Parser

from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


@registry.register("code", needs_approval=False, is_read_only=True)
class ParsePythonTool(ReadOnlyTool):
    """Parse Python code to extract structure information."""

    name: str = "parse_python_code"
    description: str = (
        "Parse Python code to extract functions, classes, and imports. "
        "Input should be either a file path or Python source code. "
        "Returns structured information about the code."
    )

    parser: Parser = Field(default=None)

    def __init__(self, **kwargs):
        """Initialize with Python language support."""
        super().__init__(**kwargs)
        # Initialize parser with Python language (tree-sitter 0.20+ API)
        PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(PY_LANGUAGE)

    def _run(self, source: str) -> str:
        """
        Parse Python code.

        Args:
            source: File path or Python source code

        Returns:
            Structured code information
        """
        try:
            # Check if source is a file path
            path = Path(self.workspace_path) / source
            if path.exists() and path.is_file():
                code = path.read_text(encoding="utf-8")
            else:
                # Treat as source code
                code = source

            # Parse code
            tree = self.parser.parse(bytes(code, "utf8"))
            root_node = tree.root_node

            # Extract structure
            structure = self._extract_structure(root_node, code)

            # Format output
            lines = ["Python Code Structure:", ""]

            if structure["imports"]:
                lines.append("Imports:")
                for imp in structure["imports"]:
                    lines.append(f"  {imp}")
                lines.append("")

            if structure["classes"]:
                lines.append(f"Classes ({len(structure['classes'])}):")
                for cls in structure["classes"]:
                    lines.append(f"  class {cls['name']}:")
                    if cls["methods"]:
                        for method in cls["methods"]:
                            lines.append(f"    def {method}(...)")
                lines.append("")

            if structure["functions"]:
                lines.append(f"Functions ({len(structure['functions'])}):")
                for func in structure["functions"]:
                    lines.append(f"  def {func['name']}(...)")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return self._handle_error(e)

    def _extract_structure(self, node, code: str) -> dict[str, Any]:
        """Extract code structure from parse tree."""
        structure = {
            "imports": [],
            "functions": [],
            "classes": [],
        }

        def traverse(n):
            """Recursively traverse tree."""
            if n.type == "import_statement" or n.type == "import_from_statement":
                import_text = code[n.start_byte : n.end_byte]
                structure["imports"].append(import_text)

            elif n.type == "function_definition":
                # Get function name
                name_node = n.child_by_field_name("name")
                if name_node:
                    func_name = code[name_node.start_byte : name_node.end_byte]
                    structure["functions"].append(
                        {"name": func_name, "line": n.start_point[0] + 1}
                    )

            elif n.type == "class_definition":
                # Get class name
                name_node = n.child_by_field_name("name")
                if name_node:
                    class_name = code[name_node.start_byte : name_node.end_byte]

                    # Get class methods
                    methods = []
                    body_node = n.child_by_field_name("body")
                    if body_node:
                        for child in body_node.children:
                            if child.type == "function_definition":
                                method_name_node = child.child_by_field_name("name")
                                if method_name_node:
                                    method_name = code[
                                        method_name_node.start_byte : method_name_node.end_byte
                                    ]
                                    methods.append(method_name)

                    structure["classes"].append(
                        {
                            "name": class_name,
                            "line": n.start_point[0] + 1,
                            "methods": methods,
                        }
                    )

            # Traverse children
            for child in n.children:
                traverse(child)

        traverse(node)
        return structure
