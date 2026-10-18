import unittest
from public_sync_scope import validate_public_scope
class PublicScopeTest(unittest.TestCase):
    def test_generic_scope(self):
        self.assertEqual([], validate_public_scope({'excluded_scope': 'Only public research is included.'}))
    def test_enumeration_rejected(self):
        self.assertTrue(validate_public_scope({'excluded_mixed_documents': [], 'excluded_scope': 'Public only'}))
    def test_missing_scope_rejected(self):
        self.assertTrue(validate_public_scope({}))
    def test_paths_rejected(self):
        for text in ['private/example.md', 'https://example.com/private', r'private\example']:
            self.assertTrue(validate_public_scope({'excluded_scope': text}))
if __name__ == '__main__': unittest.main()
