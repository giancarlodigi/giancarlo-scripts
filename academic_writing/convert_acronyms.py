"""
Convert Acronyms - LaTeX Acronym Command Replacement Tool
==========================================================

This script processes LaTeX files containing acronym commands (e.g., \\ac{}, \\acp{})
and replaces them with their expanded text forms. It mimics the behavior of the
LaTeX 'acro' package, making it useful for converting LaTeX documents to plain text
or other formats where LaTeX commands are not supported.

Features:
---------
- Parses \\DeclareAcronym definitions from a LaTeX acronyms file
- Tracks first usage of acronyms to expand them fully (e.g., "Long Name (SHORT)")
- Subsequent uses are replaced with just the short form
- Supports various acronym command variants for full control
- Replaces \\printacronyms command with a formatted list of all used acronyms

Supported Commands:
-------------------
    \\ac{key}   - Standard: "Long Name (SHORT)" on first use, "SHORT" thereafter
    \\Ac{key}   - Same as \\ac but capitalizes the first letter
    \\acp{key}  - Plural form: appends 's' to both long and short forms
    \\Acp{key}  - Capitalized plural form

    \\acf{key}  - Force full form: always "Long Name (SHORT)"
    \\Acf{key}  - Capitalized forced full form
    \\acfp{key} - Forced full plural form
    \\Acfp{key} - Capitalized forced full plural form

    \\acl{key}  - Force long form only: "Long Name" (does NOT mark as seen)
    \\Acl{key}  - Capitalized long form
    \\aclp{key} - Long plural form
    \\Aclp{key} - Capitalized long plural form

    \\acs{key}  - Force short form only: "SHORT" (marks as seen)
    \\Acs{key}  - Capitalized short form
    \\acsp{key} - Short plural form
    \\Acsp{key} - Capitalized short plural form

    \\printacronyms[include=abbrev, heading=none]
                - Replaced with a formatted list of all acronyms used in the document,
                  sorted alphabetically by short form. Each entry is formatted as:
                  "\\textbf{SHORT}, Long Form"

Acronym File Format:
--------------------
The acronyms file should contain \\DeclareAcronym definitions in this format:

    \\DeclareAcronym{api}{
        short = {API},
        long  = {Application Programming Interface},
        tag   = tech
    }

Usage:
------
Command-line:
    python convert_acronyms.py -a <acronyms.tex> -i <input.tex> -o <output.tex>

Arguments:
    -a, --acronyms  Path to the LaTeX file with \\DeclareAcronym definitions
    -i, --input     Path to the input file containing acronym commands
    -o, --output    Path for the output file with expanded acronyms

Examples:
    python convert_acronyms.py -a acros.tex -i document.tex -o document_expanded.tex
    python convert_acronyms.py --acronyms defs.tex --input paper.tex --output paper_out.tex

"""

import argparse
import re


def read_acronyms(file_path) -> dict:
    """
    Parse a LaTeX .tex file for \\DeclareAcronym definitions and return their
    short and long forms.
    """
    with open(file_path, "r") as file:
        content = file.read()

    # Find each \DeclareAcronym block
    # We look for \DeclareAcronym{key}{body} where body ends with a } on its own line or followed by whitespace
    block_pattern = re.compile(r"\\DeclareAcronym\{([^}]+)\}\s*\{(.*?)\n\}", re.DOTALL)
    
    # Patterns for fields within a block
    short_pattern = re.compile(r"short\s*=\s*\{([^}]+)\}")
    long_pattern = re.compile(r"long\s*=\s*\{([^}]+)\}")

    acronyms = {}
    for match in block_pattern.finditer(content):
        key = match.group(1).strip()
        body = match.group(2)
        
        short_match = short_pattern.search(body)
        long_match = long_pattern.search(body)
        
        if short_match and long_match:
            acronyms[key] = {
                "short": short_match.group(1).strip(),
                "long": long_match.group(1).strip()
            }

    return acronyms


def replace_acronyms(text, acronyms) -> tuple[str, set]:
    """
    Replaces LaTeX-style acronym commands in a text with their definitions.
    """

    def capitalize_first(s):
        if not s:
            return s
        return s[0].upper() + s[1:]

    def get_replacement(command, key, seen_acronyms):
        short = acronyms[key]["short"]
        long = acronyms[key]["long"]
        cmd_upper = command.upper()
        
        is_plural = cmd_upper.endswith("P")
        is_caps = command[0].isupper()
        
        s_suffix = "s" if is_plural else ""
        
        # Determine base forms
        short_form = f"{short}{s_suffix}"
        long_form = f"{long}{s_suffix}"
        if is_caps:
            long_form = capitalize_first(long_form)
            short_form = capitalize_first(short_form)
            
        full_form = f"{long_form} ({short_form})"

        # 1. Force short form: \acs, \acsp
        if "ACS" in cmd_upper:
            return short_form
            
        # 2. Force long form: \acl, \aclp
        if "ACL" in cmd_upper:
            return long_form
            
        # 3. Force full form: \acf, \acfp
        if "ACF" in cmd_upper:
            seen_acronyms.add(key)
            return full_form
            
        # 4. Standard: \ac, \acp
        if key not in seen_acronyms:
            seen_acronyms.add(key)
            return full_form
        else:
            return short_form

    # Regex pattern matches LaTeX-like commands like: \acp{...}, \ac{...}, etc.
    pattern = r"\\([aA]c[sfl]?p?)\{([^}]+)\}"
    
    seen_acronyms = set()
    
    def re_replace(match):
        command = match.group(1)
        key = match.group(2)
        if key in acronyms:
            return get_replacement(command, key, seen_acronyms)
        return match.group(0)

    processed_text = re.sub(pattern, re_replace, text)
    return processed_text, seen_acronyms


def generate_acronym_list(seen_acronyms: set, acronyms: dict) -> str:
    """
    Generate a formatted list of used acronyms.

    Args:
        seen_acronyms (set): Set of acronym keys that were used in the text.
        acronyms (dict): Dictionary mapping acronym keys to their definitions.

    Returns:
        str: A formatted string listing all used acronyms, sorted alphabetically
            by their short form.
    """
    if not seen_acronyms:
        return ""

    # Sort alphabetically by short form
    used = sorted(
        [(acronyms[key]["short"], acronyms[key]["long"]) for key in seen_acronyms],
        key=lambda x: x[0].lower(),
    )

    # Format as a list
    lines = []
    for short, long in used:
        lines.append(f"\\textbf{{{short}}}, {long}")

    return "\n\n".join(lines)


def main():
    """Command-line interface for processing acronyms in LaTeX files."""
    parser = argparse.ArgumentParser(
        description="Replace LaTeX acronym commands with their expanded forms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_acronyms.py -a acros.tex -i input.tex -o output.tex
  python convert_acronyms.py --acronyms acros.tex --input document.tex --output processed.tex
        """,
    )
    parser.add_argument(
        "-a",
        "--acronyms",
        required=True,
        help="Path to the LaTeX file containing \\DeclareAcronym definitions",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the input text file to process",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output file for processed text",
    )

    args = parser.parse_args()

    # Read acronyms from file
    acronyms = read_acronyms(args.acronyms)
    print(f"Loaded {len(acronyms)} acronyms from {args.acronyms}")

    # Read input text
    with open(args.input, "r") as f:
        text = f.read()

    # Process acronyms
    processed_text, seen_acronyms = replace_acronyms(text, acronyms)

    # Generate the acronym list and replace \printacronyms
    acronym_list = generate_acronym_list(seen_acronyms, acronyms)
    processed_text = processed_text.replace(
        r"\printacronyms[include=abbrev, heading=none]", acronym_list
    )

    # Write output
    with open(args.output, "w") as f:
        f.write(processed_text)

    print(f"Processed text written to {args.output}")


if __name__ == "__main__":
    main()
