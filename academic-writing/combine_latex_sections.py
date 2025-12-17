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
        with open(tex_path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return f"% Could not include: {tex_path} (file not found or not provided)\n"


def resolve_input_path(input_str, base_dir):
    """Resolve the path of an \\input file relative to the base directory."""
    tex_path = input_str.strip().strip("{}")
    if os.path.isabs(tex_path):
        return tex_path
    return os.path.join(base_dir, tex_path)


def process_tex_file(tex_path):
    """Process a LaTeX file and expand all \\input commands after \\begin{document}."""
    base_dir = os.path.dirname(os.path.abspath(tex_path))
    with open(tex_path, encoding="utf-8") as f:
        lines = f.readlines()
    output_lines = []
    input_pattern = re.compile(r"\\input\{([^}]+)\}")
    in_document = False
    for line in lines:
        if not in_document:
            output_lines.append(line)
            # Check for \begin{document}
            if re.match(r"\\begin\{document\}", line):
                in_document = True
            continue
        match = input_pattern.search(line)
        if match:
            input_file = match.group(1)
            resolved_path = resolve_input_path(input_file, base_dir)
            output_lines.append(f"% --- Begin {input_file} ---\n\n")
            content = get_file_content(resolved_path)
            output_lines.append(content)
            output_lines.append(f"% --- End {input_file} ---\n\n")
        else:
            output_lines.append(line)
    return "".join(output_lines)


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
