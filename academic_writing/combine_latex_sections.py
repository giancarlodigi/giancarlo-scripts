"""
LaTeX Input Expander Script
===========================

This script reads a LaTeX main.tex file and recursively replaces every \\input{...}
command with the actual contents of the referenced file, producing a single
expanded output file.

Features:
- Only processes \\input commands that appear AFTER \\begin{document}
- Resolves relative file paths based on the main .tex file location
- Inserts comment markers around each included file for traceability
- Gracefully handles missing files by inserting a comment instead of failing
- Optionally converts \\newpage and \\clearpage to PANDOCPAGEBREAK for pandoc compatibility

Usage:
    python combine_latex_sections.py                           # Uses defaults: main.tex -> main-expanded.tex
    python combine_latex_sections.py -i myfile.tex             # Custom input file
    python combine_latex_sections.py -i myfile.tex -o out.tex  # Custom input and output files
    python combine_latex_sections.py -c                        # Convert page breaks for pandoc

Arguments:
    -i, --input        : Path to the input LaTeX file (default: main.tex)
    -o, --output       : Path to the output expanded LaTeX file (default: main-expanded.tex)
    -c, --convertpandoc: Replace \\newpage and \\clearpage with PANDOCPAGEBREAK
"""

import argparse
import os
import re

# Default file paths
DEFAULT_INPUT_TEX = "main.tex"
DEFAULT_OUTPUT_TEX = "main-expanded.tex"


def get_file_content(tex_path):
    """Get the content of a LaTeX file or a comment if the file is not found."""
    try:
        # LaTeX allows omitting the .tex extension
        if not os.path.exists(tex_path) and not tex_path.endswith(".tex"):
            tex_path += ".tex"
        with open(tex_path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return f"% Could not include: {tex_path} (file not found)\n"


def expand_recursive(content, base_dir):
    """Recursively expand \\input commands in the content."""
    input_pattern = re.compile(r"\\input\{([^}]+)\}")

    def replace_match(match):
        input_file = match.group(1).strip()
        # Resolve path relative to the current file's directory
        resolved_path = os.path.join(base_dir, input_file)
        if not os.path.exists(resolved_path) and not resolved_path.endswith(".tex"):
            resolved_path += ".tex"
        
        new_base_dir = os.path.dirname(os.path.abspath(resolved_path))
        
        inner_content = get_file_content(resolved_path)
        if inner_content.startswith("% Could not include"):
            return inner_content

        # Recurse into the included file's content
        expanded_inner = expand_recursive(inner_content, new_base_dir)
        
        return (
            f"\n% --- Begin {input_file} ---\n"
            f"{expanded_inner}"
            f"\n% --- End {input_file} ---\n"
        )

    return input_pattern.sub(replace_match, content)


def process_tex_file(tex_path):
    """Process a LaTeX file and expand all \\input commands after \\begin{document}."""
    full_path = os.path.abspath(tex_path)
    base_dir = os.path.dirname(full_path)
    
    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    # Split into preamble and body at \begin{document}
    doc_start_pattern = re.compile(r"\\begin\{document\}")
    match = doc_start_pattern.search(content)
    
    if not match:
        # If no \begin{document} found, process the whole file (might be a fragment)
        return expand_recursive(content, base_dir)
    
    preamble = content[:match.end()]
    body = content[match.end():]
    
    expanded_body = expand_recursive(body, base_dir)
    
    return preamble + expanded_body


def convert_pagebreaks_for_pandoc(content):
    """Replace \\newpage and \\clearpage with PANDOCPAGEBREAK."""
    content = re.sub(r"\\newpage", "PANDOCPAGEBREAK", content)
    content = re.sub(r"\\clearpage", "PANDOCPAGEBREAK", content)
    return content


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Expand \\input commands in a LaTeX file into a single output file."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT_TEX,
        help=f"Path to the input LaTeX file (default: {DEFAULT_INPUT_TEX})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_TEX,
        help=f"Path to the output expanded LaTeX file (default: {DEFAULT_OUTPUT_TEX})",
    )
    parser.add_argument(
        "-c",
        "--convertpandoc",
        action="store_true",
        help="Replace \\newpage and \\clearpage with PANDOCPAGEBREAK",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    result = process_tex_file(args.input)
    if args.convertpandoc:
        result = convert_pagebreaks_for_pandoc(result)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"Expanded LaTeX written to {args.output}")
