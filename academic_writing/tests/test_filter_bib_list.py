import unittest
import tempfile
import os
from academic_writing.filter_bib_list import extract_citations_from_tex_files, filter_entry_fields

class TestFilterBibList(unittest.TestCase):
    def test_citation_extraction_variants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "test.tex")
            with open(tex_path, "w") as f:
                f.write("""
                \\cite{key1}
                \\citep{key2, key3}
                \\citet{key4}
                \\citeauthor{key5}
                \\cite*{key6}
                """)
            
            keys = extract_citations_from_tex_files(tmpdir)
            expected = {"key1", "key2", "key3", "key4", "key5", "key6"}
            self.assertEqual(keys, expected)

    def test_multi_line_field_filtering(self):
        entry = """@article{smith2020,
  title={A Great Study},
  abstract={This is a
  multi-line
  abstract.},
  author={Smith, J.},
  year={2020}
}"""
        excluded = ["abstract"]
        result = filter_entry_fields(entry, excluded)
        
        self.assertNotIn("abstract", result)
        self.assertNotIn("multi-line", result)
        self.assertIn("title={A Great Study}", result)
        self.assertIn("author={Smith, J.}", result)
        self.assertIn("year={2020}", result)

    def test_filter_multiple_fields(self):
        entry = """@article{key,
  title={Title},
  file={path/to/file},
  keywords={kw1, kw2},
  year={2023}
}"""
        excluded = ["file", "keywords"]
        result = filter_entry_fields(entry, excluded)
        self.assertNotIn("file", result)
        self.assertNotIn("keywords", result)
        self.assertIn("title={Title}", result)
        self.assertIn("year={2023}", result)

if __name__ == "__main__":
    unittest.main()
