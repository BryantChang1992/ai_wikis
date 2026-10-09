#!/usr/bin/env python3
"""Focused regression tests; never edit the audited vault."""
import importlib.util
import json
import pathlib
import tempfile
import unittest
import sys
sys.dont_write_bytecode = True

SPEC = importlib.util.spec_from_file_location('lint_wiki', pathlib.Path(__file__).with_name('lint_wiki.py'))
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.r = lint.Resolver({'知识库/wiki/Qwen-3.6-模型发布.md', '知识库/wiki/Card.md', '知识库/wiki/sub/Other.md', '知识库/sources/Paper.pdf', '知识库/sources/精读分析.md', '别处/精读分析.md'})
        self.here = '知识库/wiki/sub/Other.md'

    def test_dots_in_note_names(self):
        self.assertEqual(self.r.resolve(self.here, '知识库/wiki/Qwen-3.6-模型发布')[0], 'resolved')

    def test_rooted_relative_shortest_alias_anchor(self):
        for raw in ('知识库/wiki/Card', '/知识库/wiki/Card.md', '../Card#机制|卡片', 'wiki/Card', 'Card'):
            self.assertEqual(self.r.resolve(self.here, raw), ('resolved', ['知识库/wiki/Card.md']))

    def test_bad_explicit_root_is_not_basename_fallback(self):
        self.assertEqual(self.r.resolve(self.here, '知识库/absent/Card')[0], 'missing')

    def test_ambiguous_bare_basename(self):
        self.assertEqual(self.r.resolve(self.here, '精读分析')[0], 'ambiguous')

    def test_pdf_and_percent_decoding(self):
        self.assertEqual(self.r.resolve(self.here, '知识库/sources/Paper.pdf')[0], 'resolved')
        self.assertEqual(self.r.resolve(self.here, '%E7%9F%A5%E8%AF%86%E5%BA%93/wiki/Card')[0], 'resolved')

    def test_markdown_is_relative_not_global(self):
        self.assertEqual(self.r.resolve(self.here, '../Card.md', 'markdown')[0], 'resolved')
        self.assertEqual(self.r.resolve(self.here, 'Card.md', 'markdown')[0], 'missing')
        self.assertEqual(self.r.resolve(self.here, 'https://example.test/a', 'markdown')[0], 'external')


class ParserTests(unittest.TestCase):
    def test_fences_and_inline_examples_preserve_lines(self):
        text = '[[Live]]\n```md\n[[Bad]]\n```\n~~~\n[[Bad2]]\n~~~\n`[[Bad3]]` and ``x ` [[Bad4]]``\n[[Next]]\n'
        clean = lint.without_code(text)
        self.assertEqual(lint.WIKI.findall(clean), ['Live', 'Next'])
        self.assertEqual(clean.count('\n'), text.count('\n'))

    def test_frontmatter_scalars_lists_and_duplicates(self):
        text = "---\ntitle: A\nsources: ['[[知识库/wiki/Card]]', 'https://example.test']\nrelated:\n- '[[Card]]'\ntitle: B\n---\n"
        fm, duplicates, skipped, _ = lint.frontmatter(text)
        self.assertEqual(fm['sources'], ['[[知识库/wiki/Card]]', 'https://example.test'])
        self.assertEqual(fm['related'], ['[[Card]]'])
        self.assertEqual(duplicates, [{'key': 'title', 'line': 6}])
        self.assertFalse(skipped)

    def test_quoted_keys_comments_and_escaped_examples(self):
        text = "---\ntitle: A\n\"title\": B\nsources: ['https://example.test/a#section'] # comment\n---\n"
        fm, duplicates, _, _ = lint.frontmatter(text)
        self.assertEqual(duplicates[0]['key'], 'title')
        self.assertEqual(fm['sources'], ['https://example.test/a#section'])
        self.assertEqual(lint.WIKI.findall(r'\[[Example]] [[Live]]'), ['Live'])

    def test_nested_data_is_not_top_level_duplicate(self):
        text = '---\ntitle: A\nsource_citations:\n- title: B\n  page: 1\n---\n'
        _, duplicates, unsupported, _ = lint.frontmatter(text)
        self.assertFalse(duplicates)
        self.assertTrue(unsupported)

    def test_inline_mapping_reports_unsupported_not_malformed(self):
        text = "---\nsource_citations: {title: A, page: 1}\ntitle: '{literal text}'\n---\n"
        fm, duplicates, unsupported, _ = lint.frontmatter(text)
        self.assertIsNone(fm['source_citations'])
        self.assertEqual(unsupported, ['structured value for source_citations at line 2'])
        self.assertEqual(fm['title'], '{literal text}')
        self.assertFalse(duplicates)

    def test_markdown_balanced_urls_and_reference_definitions(self):
        text = '[x](https://example.test/foo_(bar)) ![p](../pic.svg)\n[ref]: <a%20b.md> "title"\n'
        self.assertEqual([v for v, _ in lint.markdown_links(text)], ['https://example.test/foo_(bar)', '../pic.svg', 'a%20b.md'])


class AuditTests(unittest.TestCase):
    def write(self, root, name, content):
        p = pathlib.Path(root) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')

    def test_inventory_existence_and_graph_read_only(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            self.write(root, '知识库/README.md', '[[知识库/wiki/Card]]\n')
            self.write(root, '知识库/wiki/Card.md', "---\ntype: concept\ntitle: Card\nsources:\n- '[[知识库/sources/Paper.pdf]]'\ntags: [test]\ncreated: 2026-10-09\nstatus: draft\nrelated: []\n---\n[image](../diagram/pic.svg)\n")
            inv = pathlib.Path(outside) / 'inventory.json'
            inv.write_text(json.dumps({'truncated': False, 'tree': [{'type': 'blob', 'path': '知识库/sources/Paper.pdf'}, {'type': 'blob', 'path': '知识库/diagram/pic.svg'}]}))
            before = {str(p.relative_to(root)): p.read_bytes() for p in pathlib.Path(root).rglob('*') if p.is_file()}
            result = lint.audit(root, inv)
            after = {str(p.relative_to(root)): p.read_bytes() for p in pathlib.Path(root).rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            self.assertFalse(result['issues'])
            self.assertEqual(result['wiki']['readme_unreachable'], [])
            self.assertEqual(result['sources']['reference_status_counts'], {'resolved': 1})

    def test_attachment_wikilinks_include_json(self):
        r = lint.Resolver({'知识库/维护记录/baseline.json'})
        self.assertEqual(r.resolve('知识库/schema.md', '知识库/维护记录/baseline.json')[0], 'resolved')

    def test_placeholders_only_in_known_meta_docs(self):
        with tempfile.TemporaryDirectory() as root:
            self.write(root, '知识库/purpose.md', '[[wikilink]] [[RealMissing]]')
            self.write(root, '知识库/sources/papers/note.md', '[[wikilink]]')
            result = lint.audit(root)
            self.assertEqual(result['issue_counts']['documentation_placeholder'], 1)
            self.assertEqual(result['issue_counts']['wiki_missing'], 2)
            self.assertEqual([i['severity'] for i in result['issues'] if i['code'] == 'documentation_placeholder'], ['warning'])

    def test_truncated_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            inv = pathlib.Path(root) / 'i.json'
            inv.write_text('{"tree": [], "truncated": true}')
            with self.assertRaises(ValueError):
                lint.audit(root, inv)

    def test_graph_and_duplicate_related(self):
        with tempfile.TemporaryDirectory() as root:
            self.write(root, '知识库/README.md', '[[知识库/wiki/A]]')
            self.write(root, '知识库/wiki/A.md', "---\ntype: meta\nrelated: ['[[B]]', '[[B]]', '[[A]]']\n---\n")
            self.write(root, '知识库/wiki/B.md', '---\ntype: meta\n---\n')
            self.write(root, '知识库/wiki/C.md', '---\ntype: meta\n---\n')
            result = lint.audit(root)
            self.assertEqual(result['wiki']['readme_unreachable'], ['知识库/wiki/C.md'])
            self.assertEqual(result['issue_counts']['duplicate_related'], 1)
            self.assertEqual(result['issue_counts']['self_related'], 1)


if __name__ == '__main__':
    unittest.main()
