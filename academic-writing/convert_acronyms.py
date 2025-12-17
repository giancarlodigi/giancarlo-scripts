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

    Scans for blocks like:
        \\DeclareAcronym{KEY}{
            short = {SHORT},
            long  = {LONG},
            tag   = TAG
        }
    Builds a dict mapping each acronym key to its short and long variants.
    The tag field is parsed but not returned.

    Args:
        file_path (str | pathlib.Path): Path to the LaTeX file.

    Returns:
        dict[str, dict[str, str]]: Maps acronym name to:
            - 'short': The acronym.
            - 'long' : The expanded form.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If there is an error reading the file.

    Limitations:
        - Assumes specific pattern and order for fields.
        - Does not handle nested or escaped braces.
        - Acronym keys are limited to word characters.

    Example:
        acronyms = read_acronyms("acronyms.tex")
        print(acronyms["api"]["long"])
    """
    with open(file_path, "r") as file:
        content = file.read()

    # Regular expression to match the \DeclareAcronym block
    pattern = re.compile(
        r"\\DeclareAcronym\{(\w+)\}\{\s*short\s*=\s*\{([^}]+)\},\s*long\s*=\s*\{([^}]+)\},\s*tag\s*=\s*([^}]+)\s*\}",
        re.MULTILINE,
    )

    acronyms = {}
    for match in pattern.finditer(content):
        acronym = match.group(1)
        short = match.group(2)
        long = match.group(3)
        acronyms[acronym] = {"short": short, "long": long}

    return acronyms


def replace_acronyms(text, acronyms) -> tuple[str, set]:
    """
    Replaces LaTeX-style acronym commands in a text with their definitions.

    This function searches for acronym commands like `\\ac{key}`, `\\acp{key}`,
    etc., within the input text. It then replaces these commands based on a
    provided dictionary of acronyms and a set of rules that mimic the
    behavior of the LaTeX 'acronym' package.

    The function tracks the first usage of each acronym to expand it to its
    full form "Long Name (Short Name)", while subsequent usages are replaced
    with just the short form. Specific commands can be used to override this
    default behavior.

    ! IMPORTANT:
    ! - the \\acl commands do not mark the acronym as "seen". This means that
    ! subsequent uses of `\\ac` will still expand to the full form

    Supported commands:
    - `\\ac`, `\\Ac`: Standard usage. Expands to full form on first use,
      short form thereafter, with `\\Ac` capitalizes the output.
    - `\\acp`, `\\Acp`: Plural version of `\\ac`. Appends 's' to the
      long and/or short forms.

    - `\\acf`, `\\Acf`: Forces the full form "Long Name (Short Name)".
    - `\\acfp`, `\\Acfp`: Forces the plural full form.

    - `\\acl`, `\\Acl`: Forces the long form only.
    - `\\aclp`, `\\Aclp`: Forces the plural long form.

    - `\\acs`, `\\Acs`: Forces the short form only.
    - `\\acsp`, `\\Acsp`: Forces the plural short form.

    If an acronym key is not found in the `acronyms` dictionary, the
    original command (e.g., `\\ac{unknown}`) is left unchanged in the text.

    Args:
        text (str): The input string containing LaTeX-style acronym commands.
        acronyms (dict): A dictionary mapping acronym keys to their definitions.
            The expected format is:
            {
                "key": {"short": "SHORT", "long": "Long Name"},
                ...
            }

    Returns:
        tuple[str, set]: A tuple containing:
            - The processed text with all recognized acronym commands replaced.
            - A set of acronym keys that were used (seen) in the text.
    """

    def check_capital(command, text) -> str:
        if command[0].isupper():
            text = text.capitalize()
        return text

    # Regex pattern matches LaTeX-like commands like: \acp{...}, \ac{...}, etc.
    pattern = r"\\([aA]c[sfl]?p?)\{([^}]+)\}"

    # Find all matches in the input text
    matches = list(re.finditer(pattern, text))

    # Track which acronyms have been seen by initializing a set
    seen_acronyms = set()

    # Process each match and build the new text
    result = []
    last_end = 0

    # Iterate through all matches found in the text for acronyms
    for match in matches:
        # Add all text unchanged up until the current acronym match
        result.append(text[last_end : match.start()])

        command = match.group(1)  # ac, acs, acp, etc.
        key = match.group(2)  # The acronym key (e.g., "api")

        if key not in acronyms:
            # If acronym not found, keep original text
            result.append(match.group(0))
        else:
            short = acronyms[key]["short"]
            long = acronyms[key]["long"]

            # ------------------------------------------------------------------
            # Special scenarios:
            #   1) Force short form
            #   2) Force long form

            # Short form: \acs and \acsp are forced short forms
            # - Special case and forces it to be seen in `seen_acronyms`
            if command.upper() in ("ACS", "ACSP"):
                if command.upper() == "ACSP":
                    insert_text = f"{short}s"
                else:
                    insert_text = short

                seen_acronyms.add(key)

            # Long form: \acl, \aclp
            # ie. \acl{api} -> Application Programming Interface
            # notes:
            #  - force long form, so does NOT count towards `seen_acronyms`
            if command.upper() in ("ACL", "ACLP"):
                if command.upper() == "ACLP":
                    insert_text = f"{check_capital(command, long)}s"
                else:
                    insert_text = f"{check_capital(command, long)}"

            # ------------------------------------------------------------------

            # If the acronym has NOT been seen before, process it
            if key not in seen_acronyms:
                # Full form: \acf, \acfp
                # ie. \acf{api} -> API (Application Programming Interface)
                if command.upper() in ("ACF", "ACFP"):
                    if command.upper() == "ACFP":
                        insert_text = f"{check_capital(command, long)}s ({short}s)"
                    else:
                        insert_text = f"{check_capital(command, long)} ({short})"
                    seen_acronyms.add(key)  # Mark as seen

                # Default case for \ac
                # ie. \ac{api} -> API (Application Programming Interface)
                if command.upper() in ("AC", "ACP"):
                    if command.upper() == "ACP":
                        insert_text = f"{check_capital(command, long)}s ({short}s)"
                    else:
                        insert_text = f"{check_capital(command, long)} ({short})"
                    seen_acronyms.add(key)  # Mark as seen

            # Subsequent uses of the acronym which has been seen before
            else:
                if command.upper() == "ACP":
                    insert_text = f"{short}s"
                elif command.upper() == "AC":
                    insert_text = short

            # Insert the text
            result.append(insert_text)

        last_end = match.end()

    # Add any remaining text
    result.append(text[last_end:])

    return "".join(result), seen_acronyms


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
