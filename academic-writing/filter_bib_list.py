"""
BibTeX Citation Filter Script
=============================

This script filters a BibTeX (.bib) file to include only the references that are
actually cited in your LaTeX documents. It scans all .tex files in a directory,
extracts citation keys from \\cite{} commands, and creates a new .bib file
containing only the relevant entries. It's application is for large zotero
libraries that contain ALL references, but you only want to include those
that are cited in your LaTeX project.

Features:
- Recursively scans all .tex files in a directory for \\cite{} commands
- Handles multiple citations within a single \\cite{key1, key2, key3} command
- Filters out unwanted BibTeX fields (e.g., abstract, file, url, keywords)
- Warns about citation keys that are not found in the .bib file
- Outputs a clean, minimal .bib file with only the necessary references

Usage:
    python filter_bib_list.py <input.bib>                          # Uses defaults
    python filter_bib_list.py <input.bib> -o filtered.bib          # Custom output file
    python filter_bib_list.py <input.bib> -t /path/to/tex/files    # Custom tex directory
    python filter_bib_list.py <input.bib> -o out.bib -t ./chapters # Both options

Arguments:
    input_bib       : Path to the input BibTeX file (required)
    -o, --output    : Path to the output filtered BibTeX file (default: references.bib)
    -t, --tex-dir   : Directory containing LaTeX files to scan (default: current directory)

Default Excluded Fields:
    The following fields are removed from BibTeX entries by default:
    - tags, keywords, annote, annotation, file, note, comment, archivePrefix

Example Workflow:
    1. Place your main .bib file in your project directory
    2. Run: python filter_bib_list.py library.bib -t ./chapters -o references.bib
    3. The script will scan all .tex files in ./chapters for citations
    4. A new references.bib file will be created with only cited entries
"""

import argparse
import re
from pathlib import Path


def extract_citations_from_tex_files(tex_directory="."):
    """
    Extract all citation keys from LaTeX files in a directory.

    This function searches through all .tex files in the specified directory
    and extracts citation keys from \cite{} commands. It handles multiple
    citations within a single \cite{} command (comma-separated) and returns
    a unique set of all found citation keys.

    Args:
      tex_directory (str, optional): Path to the directory containing .tex files.
                     Defaults to current directory (".").

    Returns:
      set: A set of unique citation keys found in all .tex files.
         Each citation key is a string with leading/trailing whitespace removed.

    Example:
      >>> citations = extract_citations_from_tex_files("/path/to/latex/files")
      >>> print(citations)
      {'smith2020', 'jones2019', 'doe2021'}

    Note:
      - Only processes files with .tex extension
      - Uses UTF-8 encoding when reading files
      - Citation keys are extracted from \cite{key1,key2,...} patterns
      - Whitespace around citation keys is automatically stripped
      - Recursively searches through all subdirectories
    """
    citations = set()
    tex_files = Path(tex_directory).rglob("*.tex")

    for tex_file in tex_files:
        with open(tex_file, "r", encoding="utf-8") as f:
            content = f.read()
            cite_matches = re.findall(r"\\cite\{([^}]+)\}", content)
            for match in cite_matches:
                keys = [key.strip() for key in match.split(",")]
                citations.update(keys)

    return citations


def filter_entry_fields(entry_text, excluded_fields):
    """
    Remove specified fields from a BibTeX entry.

    This function parses a BibTeX entry and removes any fields that match
    the names specified in the excluded_fields list. The comparison is
    case-insensitive.

    Args:
      entry_text (str): The complete BibTeX entry as a string, including
        newlines and formatting.
      excluded_fields (list): A list of field names (strings) to be removed
        from the BibTeX entry. Field names are matched case-insensitively.

    Returns:
      str: The filtered BibTeX entry with specified fields removed,
        maintaining the original formatting and line structure.

    Example:
      >>> entry = "@article{key,\n  title={Sample},\n  author={John Doe},\n  year={2023}\n}"
      >>> excluded = ["author"]
      >>> filter_entry_fields(entry, excluded)
      "@article{key,\n  title={Sample},\n  year={2023}\n}"
    """
    lines = entry_text.split("\n")
    filtered_lines = []

    for line in lines:
        # Check if line contains a field definition
        field_match = re.match(r"\s*(\w+)\s*=", line)
        if field_match:
            field_name = field_match.group(1).lower()
            if field_name in [f.lower() for f in excluded_fields]:
                continue  # Skip this field
        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def extract_and_filter_bib_entries(bib_file, excluded_fields):
    """
    Parse a .bib file and extract bibliography entries with field filtering.

    This function reads a bibliography file, identifies all bibliography entries using
    regex pattern matching, extracts their keys, and filters out unwanted fields
    from each entry.

    Args:
      bib_file (str): Path to the .bib file to be parsed.
      excluded_fields (list): List of field names to exclude from the entries.

    Returns:
      dict: A dictionary where keys are bibliography entry keys and values are
          the filtered entry text with excluded fields removed.

    Note:
      - Expects entries to follow standard BibTeX format (@type{key, ...})
      - Uses UTF-8 encoding for file reading
      - Relies on filter_entry_fields() function for field filtering
    """
    with open(bib_file, "r", encoding="utf-8") as f:
        content = f.read()

    entries = {}
    # Find all entries using regex
    entry_pattern = r"(@\w+\s*\{\s*[^,\s]+\s*,.*?\n\})"
    matches = re.finditer(entry_pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        entry_text = match.group(1)
        # Extract the key
        key_match = re.search(r"@\w+\s*\{\s*([^,\s]+)\s*,", entry_text)
        if key_match:
            key = key_match.group(1)
            # Filter out unwanted fields
            filtered_entry = filter_entry_fields(entry_text, excluded_fields)
            entries[key] = filtered_entry

    return entries


def filter_bib_file_manual(input_bib, output_bib, cited_keys, excluded_fields=None):
    """
    Filter a .bib file to include only specified citation keys and exclude
    certain fields.

    This function reads a bibliography file, extracts entries matching the
    provided citation keys, removes specified fields from those entries, and
    writes the filtered results to a new file.

    Args:
      input_bib (str): Path to the input .bib file to be filtered.
      output_bib (str): Path to the output .bib file where filtered entries
      will be written.
      cited_keys (list): List of citation keys to include in the filtered
      output.
      excluded_fields (list, optional): List of field names to exclude from
      entries. Defaults to ["tags", "keywords", "mendeley-tags", "annote",
      "abstract", "file", "url"].

    Returns:
      None: The function writes output to a file and prints status
      information.

    Side Effects:
      - Creates/overwrites the output .bib file
      - Prints warnings for citation keys not found in the input file
      - Prints summary statistics about the filtering operation

    Example:
      >>> cited_keys = ["smith2020", "jones2021", "doe2022"]
      >>> filter_bib_file_manual("references.bib", "filtered.bib",
      ...                        cited_keys)
      Filtered 3 entries from 150 total entries
      Excluded fields: ['tags', 'keywords', 'mendeley-tags', 'annote',
      'abstract', 'file', 'url']
      Output written to: filtered.bib
    """
    if excluded_fields is None:
        excluded_fields = [
            "tags",
            "keywords",
            "mendeley-tags",
            "annote",
            "abstract",
            "file",
            "url",
        ]

    entries = extract_and_filter_bib_entries(input_bib, excluded_fields)

    with open(output_bib, "w", encoding="utf-8") as f:
        filtered_count = 0
        for key in cited_keys:
            if key in entries:
                f.write(entries[key] + "\n\n")
                filtered_count += 1
            else:
                print(f"Warning: Citation key '{key}' not found in .bib file")

    print(f"Filtered {filtered_count} entries from {len(entries)} total entries")
    print(f"Excluded fields: {excluded_fields}")
    print(f"Output written to: {output_bib}")


def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Filter BibTeX file based on citations found in LaTeX files"
    )
    parser.add_argument("input_bib", help="Path to the input BibTeX file")
    parser.add_argument(
        "-o",
        "--output",
        default="references.bib",  # Default output file name
        help="Output BibTeX file (default: references.bib)",
    )
    parser.add_argument(
        "-t",
        "--tex-dir",
        default=".",  # Default to current directory
        help="Directory containing LaTeX files (default: .)",
    )

    args = parser.parse_args()

    # Configuration
    input_bib_file = args.input_bib
    output_bib_file = args.output
    tex_directory = args.tex_dir

    # Fields to exclude
    excluded_fields = [
        "tags",
        "keywords",
        "annote",
        "annotation",
        "file",
        "note",
        "comment",
        "archivePrefix",
    ]

    # Extract citations and filter
    cited_keys = extract_citations_from_tex_files(tex_directory)
    print(f"Found {len(cited_keys)} unique citations")

    filter_bib_file_manual(input_bib_file, output_bib_file, cited_keys, excluded_fields)


if __name__ == "__main__":
    main()
