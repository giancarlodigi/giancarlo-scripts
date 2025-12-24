-- This Lua filter for Pandoc handles page breaks in documents.
-- It converts specific markers like "PANDOCPAGEBREAK"
-- into appropriate page break elements for OpenXML (Word) output.
-- ! Usage: text needs to have "PANDOCPAGEBREAK" where a page break is desired.

-- Handle paragraphs containing only the PAGEBREAK marker
function Para(el)
  if #el.content == 1 and el.content[1].t == "Str" and el.content[1].text == "PANDOCPAGEBREAK" then
    return pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  end
  -- Also check for RawInline
  if #el.content == 1 and el.content[1].t == "RawInline" then
    local raw = el.content[1]
    if raw.format == "latex" and (raw.text:match("\\newpage") or raw.text:match("\\clearpage")) then
      return pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
    end
  end
end

-- Handle plain text markers
function Str(el)
  if el.text == "PANDOCPAGEBREAK" then
    return pandoc.RawInline('openxml', '<w:br w:type="page"/>')
  end
end