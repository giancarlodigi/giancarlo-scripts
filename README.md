# giancarlo-scripts

A collection of scripts and files I frequently use, tailored for my personal and academic projects.

## Academic Writing

This repository includes several scripts and templates designed to streamline the process of preparing academic documents. The tools provided here help with tasks such as combining LaTeX files, converting acronyms, and integrating R outputs into LaTeX documents. This directory contains scripts to assist with academic writing workflows, particularly involving LaTeX, R, and Pandoc.

### Python Scripts

- **`academic-writing/combine_latex_sections.py`**:

  - Recursively expands `\input{...}` commands in a main LaTeX file into a single output file.
  - Useful for flattening a multi-file LaTeX project into one file (e.g., for submission or conversion).
  - Can optionally convert `\newpage` and `\clearpage` commands to a `PANDOCPAGEBREAK` marker for better compatibility with Pandoc conversions to Word.
  - *Usage*: `python combine_latex_sections.py -i main.tex -o main-expanded.tex`

- **`academic-writing/convert_acronyms.py`**:
  - Replaces LaTeX acronym commands (e.g., `\ac{API}`, `\acp{API}`) with their expanded text forms (e.g., "Application Programming Interface (API)").
  - Mimics the behavior of the LaTeX `acro` package, tracking first usage to define the acronym.
  - Useful for converting LaTeX documents to plain text or other formats where LaTeX commands are not supported.
  - *Usage*: `python convert_acronyms.py -a acronyms.tex -i input.tex -o output.tex`

### R Scripts

- **`academic-writing/R_to_latex.R`**:
  - Contains helper functions to bridge R and LaTeX.
  - `convert_gt_to_latex(tbl)`: Converts a `{gt}` table object into a LaTeX string containing only the table body rows (between `\toprule` and `\bottomrule`).
  - `add_tex_to_file(...)`: Inserts LaTeX content (like table rows) into a specific position in an existing LaTeX template file.

### Pandoc Utilities

- **`academic-writing/pandoc/pandoc_pagebreak.lua`**:
  - A Lua filter for Pandoc to handle page breaks when converting to Word (OpenXML).
  - Converts the text marker `PANDOCPAGEBREAK` (and `\newpage`/`\clearpage` in some contexts) into a native Word page break.
  
- **`academic-writing/pandoc/custom-manuscript-template.docx`**:
  - A reference Word document template for Pandoc conversions that preserves styles and formatting that I commonly use in academic manuscripts.
