import unittest
import tempfile
import os
from academic_writing.convert_acronyms import replace_acronyms, read_acronyms

class TestConvertAcronyms(unittest.TestCase):
    def setUp(self):
        self.acronyms = {
            "api": {"short": "API", "long": "Application Programming Interface"},
            "nasa": {"short": "NASA", "long": "National Aeronautics and Space Administration"}
        }

    def test_standard_replacement(self):
        text = "First: \\ac{api}. Second: \\ac{api}."
        processed, seen = replace_acronyms(text, self.acronyms)
        self.assertIn("Application Programming Interface (API)", processed)
        self.assertIn("Second: API", processed)
        self.assertIn("api", seen)

    def test_capitalization(self):
        text = "\\Ac{api} is useful."
        processed, _ = replace_acronyms(text, self.acronyms)
        self.assertTrue(processed.startswith("Application Programming Interface"))
        
        # Test it doesn't lowercase the rest (e.g., NASA)
        text = "\\Ac{nasa} is a gov agency."
        processed, _ = replace_acronyms(text, self.acronyms)
        self.assertIn("National Aeronautics and Space Administration", processed)

    def test_plural(self):
        text = "We use many \\acp{api}."
        processed, _ = replace_acronyms(text, self.acronyms)
        self.assertIn("Application Programming Interfaces (APIs)", processed)

    def test_forced_forms(self):
        text = "\\acf{api} then \\acl{api} then \\acs{api} and plural \\acsp{api}."
        processed, _ = replace_acronyms(text, self.acronyms)
        self.assertIn("Application Programming Interface (API)", processed)
        self.assertIn("Application Programming Interface", processed)
        self.assertIn("API", processed)
        self.assertIn("APIs", processed)

    def test_complex_mixed_sequence(self):
        # Scenario: \acs first (marks as seen), then \ac (should be SHORT), 
        # then \acfp (forced plural full), then \ac (should be SHORT)
        text = "Start with \\acs{api}. Now second call: \\ac{api}. Then forced: \\acfp{api}. Final: \\ac{api}."
        processed, seen = replace_acronyms(text, self.acronyms)
        
        # 1. \acs{api} -> "API" (marks seen)
        # 2. \ac{api} -> "API" (because \acs marked seen)
        # 3. \acfp{api} -> "Application Programming Interfaces (APIs)"
        # 4. \ac{api} -> "API"
        
        self.assertIn("Start with API.", processed)
        self.assertIn("second call: API", processed)
        self.assertIn("forced: Application Programming Interfaces (APIs)", processed)
        self.assertIn("Final: API.", processed)

    def test_acl_does_not_mark_seen(self):
        # Scenario: \acl first (does NOT mark as seen), then \ac (should be FULL)
        text = "Start with \\acl{api}. Now first call: \\ac{api}."
        processed, _ = replace_acronyms(text, self.acronyms)
        
        self.assertIn("Start with Application Programming Interface.", processed)
        self.assertIn("first call: Application Programming Interface (API)", processed)

    def test_read_acronyms_flexible(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write("""
\\DeclareAcronym{api}{
    short = {API},
    long = {Application Programming Interface},
    tag = tech
}
\\DeclareAcronym{nasa}{
    long = {National Aeronautics and Space Administration},
    short = {NASA}
}
""")
            temp_path = f.name
        
        try:
            acros = read_acronyms(temp_path)
            self.assertEqual(len(acros), 2)
            self.assertEqual(acros["api"]["short"], "API")
            self.assertEqual(acros["nasa"]["long"], "National Aeronautics and Space Administration")
        finally:
            os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
