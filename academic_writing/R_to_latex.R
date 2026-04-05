###############################################################################
#' Convert a {gt} table to LaTeX body rows
#'
#' Converts a [`gt::gt()`] table into a character string containing only the
#' table body between `\toprule` and `\bottomrule` (i.e., the rows suitable
#' for inclusion inside a LaTeX `tabular`/`tabularx` environment). The helper
#' also removes `\\addlinespace[2.5pt]` and replaces common comparison operators
#' with LaTeX math equivalents for better formatting.
#'
#' @param tbl A {gt} table object (class `"gt_tbl"`).
#' @param start_pos Optional integer line index to specify where to start the
#'  extraction of table body rows. If `NULL` (default), extraction starts just
#'  after the first `\midrule` line.
#'
#' @return A length-1 character string that can be used as the body of a LaTeX
#' table.
#'
convert_gt_to_latex <- function(tbl, start_pos = NULL) {
  # Check if the table is a gt object
  if (class(tbl)[1] != "gt_tbl") {
    stop("Input must be a gt table.")
  }

  # Convert the gt table to LaTeX and extract the relevant lines ---------------
  latex_lines <- tbl |>
    gt::as_latex() |>
    as.character() |>
    stringr::str_split("\n")

  # If start_pos is provided, extract lines from that position onward
  if (is.null(start_pos)) {
    start_idx <- which(stringr::str_detect(latex_lines[[1]], "\\\\midrule"))[1] + 1
  } else {
    start_idx <- start_pos
  }

  # Find the end index (line before \bottomrule)
  end_idx <- which(stringr::str_detect(latex_lines[[1]], "\\\\bottomrule"))[1] - 1

  # Extract and clean the table content ----------------------------------------
  table_content <- latex_lines[[1]][start_idx:end_idx] |>
    paste(collapse = "\n") |>

    # Remove any \addlinespace commands
    stringr::str_remove_all("\\\\addlinespace\\[2.5pt\\]") |>
    stringr::str_remove_all("\\[2.5pt\\]") |>

    # Replace comparison operators with LaTeX math equivalents
    stringr::str_replace_all("<=", "$\\leq$") |>
    stringr::str_replace_all(">=", "$\\geq$") |>
    stringr::str_replace_all("<", "$<$") |>
    stringr::str_replace_all(">", "$>$")

  return(table_content)
}


###############################################################################
#' Insert LaTeX table content into a template file
#'
#' Reads an existing LaTeX template file (typically containing a `tabular`/
#' `tabularx` environment) and inserts `latex_content` at a specified line
#' position, preserving all lines before and after that point. The updated
#' file is written to `output_path` using the same `file_name` as the template.
#'
#' @param latex_content Character vector containing the LaTeX content to insert
#'   (e.g., table body rows). If length > 1, each element is treated as a line.
#' @param file_name Name of the LaTeX template file (e.g., `"table1.tex"`).
#' @param template_path Directory containing the template file.
#' @param template_pos_start Integer line index in the template at which to
#'   insert `latex_content`. Lines `1:template_pos_start` are kept, then the new
#'   content is inserted, then the remaining lines are appended.
#' @param output_path Directory where the updated LaTeX file will be written.
#'
#' @return Invisibly returns `NULL`; called for its side effect of writing the
#'   updated LaTeX file.
#'
add_tex_to_file <- function(
  latex_content,
  file_name,
  template_path,
  template_pos_start,
  output_path
) {
  # Read the existing content of the template table file
  # - this is where the table body will be inserted
  existing_lines <- readr::read_lines(file.path(template_path, file_name))

  # Insert the new content at the specified locations, while keeping existing
  # content before and after unchanged
  new_lines <- c(
    existing_lines[1:(template_pos_start)],
    latex_content,
    existing_lines[(template_pos_start + 1):length(existing_lines)]
  )

  # Write to a new latex file in the directory specified
  readr::write_lines(
    new_lines,
    file.path(
      output_path,
      file_name
    )
  )

  # Print to console what file has been written and where
  cat(
    "\n",
    cli::col_green(file_name),
    "has been written to", 
    cli::col_blue(output_path),
    "\n"
  )
}
