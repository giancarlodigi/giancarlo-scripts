import os
import unittest
import tempfile
import shutil
from academic_writing.combine_latex_sections import process_tex_file, expand_recursive

class TestCombineLatexSections(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_recursive_expansion(self):
        # Create a nested structure
        main_path = os.path.join(self.test_dir, "main.tex")
        sub_path = os.path.join(self.test_dir, "sub.tex")
        nested_path = os.path.join(self.test_dir, "nested.tex")
        
        with open(main_path, "w") as f:
            f.write("\\begin{document}\n\\input{sub}\n\\end{document}")
        with open(sub_path, "w") as f:
            f.write("Sub content\n\\input{nested}")
        with open(nested_path, "w") as f:
            f.write("Nested content")
            
        result = process_tex_file(main_path)
        
        self.assertIn("Sub content", result)
        self.assertIn("Nested content", result)
        self.assertTrue(result.find("Sub content") < result.find("Nested content"))

    def test_preamble_protection(self):
        main_path = os.path.join(self.test_dir, "main.tex")
        with open(main_path, "w") as f:
            f.write("\\documentclass{article}\n\\input{preamble_sub}\n\\begin{document}\n\\input{body_sub}\n\\end{document}")
        
        # This file should NOT be expanded if it's in the preamble
        pre_sub = os.path.join(self.test_dir, "preamble_sub.tex")
        with open(pre_sub, "w") as f:
            f.write("SHOULD_NOT_SEE_THIS")
            
        body_sub = os.path.join(self.test_dir, "body_sub.tex")
        with open(body_sub, "w") as f:
            f.write("SHOULD_SEE_THIS")

        result = process_tex_file(main_path)
        self.assertIn("\\input{preamble_sub}", result)
        self.assertNotIn("SHOULD_NOT_SEE_THIS", result)
        self.assertIn("SHOULD_SEE_THIS", result)

    def test_multiple_inputs_on_line(self):
        content = "Text \\input{file1} and \\input{file2}"
        
        # Mock get_file_content to avoid actual file I/O for this simple test
        import academic_writing.combine_latex_sections as cls
        original_get = cls.get_file_content
        cls.get_file_content = lambda x: f"CONTENT_OF_{os.path.basename(x)}"
        
        try:
            result = expand_recursive(content, self.test_dir)
            self.assertIn("CONTENT_OF_file1", result)
            self.assertIn("CONTENT_OF_file2", result)
        finally:
            cls.get_file_content = original_get

if __name__ == "__main__":
    unittest.main()
