"""Tests use temporary public-vault fixtures; no real events are invented."""
import contextlib
import hashlib
import io
import json
import pathlib
import tempfile
import unittest

import manage_wiki as manager


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.a = '知识库/wiki/A.md'
        self.b = '知识库/wiki/B.md'
        self.s = '知识库/wiki/Storage.md'
        self.sa = '知识库/wiki/Storage-alias.md'
        self.t = '知识库/wiki/Streaming.md'
        self.review = '知识库/维护记录/公开审阅.md'
        self.config = {'schema_version': 1, 'note_roots': ['知识库/wiki'],
            'public_evidence_roots': ['知识库'], 'research_tags': ['focus'],
            'domain_groups': [{'id': 'storage', 'tags': ['storage']},
                              {'id': 'stream', 'tags': ['stream']}],
            'canonical_aliases': {self.sa: self.s}, 'review_findings': []}
        self.write(self.a, '---\ntype: concept\ntitle: A\ntags: [focus]\nconfidence: 0.1\ncreated: 1900-01-01\n---\n# A\nOriginal A.\n')
        self.write(self.b, '---\ntype: concept\ntags: [none]\nconfidence: 0.99\ncreated: 2999-01-01\n---\n# B\nOriginal B.\n')
        self.write(self.s, '---\ntype: synthesis\ntags: [storage, stream]\n---\n# Storage\nUses [[知识库/wiki/A]] to compare mechanisms.\n')
        self.write(self.sa, '---\ntype: survey\ntags: [stream]\n---\n# Alias\nUses [[知识库/wiki/A]] to compare mechanisms.\n')
        self.write(self.t, '---\ntype: synthesis\ntags: [stream]\n---\n# Streaming\nUses [[知识库/wiki/A]].\n')
        self.write(self.review, '---\ntype: meta\n---\n# Public review\nA is retained at [[知识库/wiki/A]], B at [[知识库/wiki/B]].\n')
        self.write(manager.EVENTS, '')
        self.save_config()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def save_config(self):
        self.write(manager.CONFIG, json.dumps(self.config, ensure_ascii=False))

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def run_cli(self, *args, expected=0):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = manager.main(['--root', str(self.root), *args])
        self.assertEqual(code, expected, (args, err.getvalue(), out.getvalue()))
        return json.loads(out.getvalue()) if out.getvalue() else err.getvalue()

    def use(self, note=None, evidence=None, **kwargs):
        return self.run_cli('record-use', note or self.a, '--evidence', evidence or self.s,
                            '--reason', 'Public synthesis reuse.', **kwargs)

    def decide(self, state, note=None, replacement=None, **kwargs):
        args = ['decision', note or self.a, state, '--evidence', self.review,
                '--reason', 'Reviewed public scope and stable entry.']
        if replacement:
            args += ['--replacement', replacement]
        return self.run_cli(*args, **kwargs)

    def restore(self, ident, **kwargs):
        return self.run_cli('restore', ident, '--evidence', self.review,
                            '--reason', 'Reverse prior public maintenance decision.', **kwargs)

    def priority(self):
        return json.loads(manager.Engine(self.root).build()[manager.PRIORITY])

    def rows(self):
        p = self.priority()
        return {r['path']: r for r in p['main'] + p['alternate']}

    def test_no_fabricated_access_or_confidence_ranking(self):
        rows = self.rows()
        self.assertTrue(all(r['importance']['observed_uses'] == 0 for r in rows.values()))
        self.assertEqual(self.priority()['main'][0]['path'], self.a)
        self.assertEqual(rows[self.a]['credibility']['confidence'], '0.1')
        self.assertFalse(rows[self.a]['credibility']['independently_verified_by_manager'])
        self.assertEqual(rows[self.a]['importance']['inbound_domain_count'], 2)

    def test_apply_is_output_only_and_repeated_apply_is_idempotent(self):
        before = self.snapshot()
        first = self.run_cli('apply')
        after = self.snapshot()
        self.assertEqual(set(first['changed']), set(manager.OUTPUTS))
        self.assertEqual(set(after) - set(before), set(manager.OUTPUTS) | {manager.JOURNAL})
        self.assertTrue(all(after[k] == v for k, v in before.items()))
        second = self.run_cli('apply')
        self.assertEqual(second, {'changed': [], 'journal_appended': False})
        self.assertEqual(after, self.snapshot())
        self.assertTrue(self.run_cli('check')['fresh'])

    def test_plan_and_check_are_read_only_even_when_stale(self):
        before = self.snapshot()
        self.assertTrue(self.run_cli('plan')['would_change'])
        self.run_cli('check', expected=1)
        self.assertEqual(before, self.snapshot())
        self.run_cli('apply')
        self.write(self.a, (self.root / self.a).read_text() + 'New content.\n')
        stale = self.snapshot()
        self.run_cli('check', expected=1)
        self.run_cli('plan')
        self.assertEqual(stale, self.snapshot())

    def test_use_same_evidence_and_note_is_idempotent(self):
        first = self.use()
        snapshot = self.snapshot()
        second = self.use()
        self.assertTrue(first['appended'])
        self.assertFalse(second['appended'])
        self.assertEqual(first['event'], second['event'])
        self.assertEqual(snapshot, self.snapshot())
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)

    def test_artifact_alias_and_revision_cannot_inflate_use(self):
        self.use()
        self.use(evidence=self.sa)
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)
        self.write(self.s, (self.root / self.s).read_text() + '\nReformatted public synthesis.\n')
        self.use()
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)
        candidates = json.loads(manager.Engine(self.root).build()[manager.CANDIDATES])['candidates']
        self.assertTrue(any(c.get('evidence_status') == 'changed' for c in candidates))

    def test_public_artifact_paths_count_separately(self):
        self.use()
        self.use(evidence=self.t)
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 2)

    def test_excludes_self_generated_index_meta_and_metadata_only_use(self):
        self.write(self.a, (self.root / self.a).read_text() + '[[知识库/wiki/A]]\n')
        self.use(evidence=self.a, expected=2)
        for path, content in [('知识库/wiki/README.md', '[[知识库/wiki/A]]'),
                              ('知识库/wiki/log.md', '[[知识库/wiki/A]]'),
                              (self.review, (self.root / self.review).read_text()),
                              ('知识库/wiki/Metadata.md', '---\ntype: synthesis\nrelated: ["[[知识库/wiki/A]]"]\n---\nNo body use.')]:
            self.write(path, content)
            self.use(evidence=path, expected=2)
        self.run_cli('apply')
        self.use(evidence=manager.VIEW, expected=2)

    def test_code_example_links_do_not_prove_use(self):
        self.write(self.s, '# S\n`[[知识库/wiki/A]]`\n```md\n[[知识库/wiki/A]]\n```\n<!-- [[知识库/wiki/A]] -->')
        self.use(expected=2)

    def test_plain_markdown_body_link_can_prove_use(self):
        self.write(self.s, '# S\nComparing [A](A.md).\n')
        self.use()
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)

    def test_alias_aware_crossdomain_counts_and_excludes_meta_indexes(self):
        self.write('知识库/wiki/README.md', '---\ntags: [extra]\n---\n[[知识库/wiki/A]]')
        self.write('知识库/wiki/Meta.md', '---\ntype: meta\ntags: [extra]\n---\n[[知识库/wiki/A]]')
        self.config['domain_groups'].append({'id': 'extra', 'tags': ['extra']})
        self.save_config()
        signals = self.rows()[self.a]['importance']
        self.assertEqual(signals['inbound_domains'], {'storage': [self.s], 'stream': [self.t]})

    def test_reference_preserves_sources_and_is_fully_reversible(self):
        before = {p: (self.root / p).read_bytes() for p in (self.a, self.b)}
        event = self.decide('reference', replacement=self.b)['event']
        self.assertEqual(self.rows()[self.a]['lifecycle']['state'], 'reference')
        self.assertEqual(self.rows()[self.a]['canonical'], self.b)
        self.assertNotIn(self.a, [r['path'] for r in self.priority()['main']])
        reversal = self.restore(event)['event']
        self.assertEqual(self.rows()[self.a]['lifecycle']['state'], 'active')
        self.assertEqual(self.rows()[self.a]['canonical'], self.a)
        self.restore(reversal)
        self.assertEqual(self.rows()[self.a]['lifecycle']['state'], 'reference')
        self.assertTrue(all((self.root / p).read_bytes() == content for p, content in before.items()))
        self.assertEqual(len(manager.read_jsonl(self.root, manager.EVENTS)), 3)

    def test_use_reversal_and_redo(self):
        event = self.use()['event']
        reversal = self.restore(event)['event']
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 0)
        self.assertFalse(self.use()['enabled'])
        self.restore(reversal)
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)

    def test_stale_and_missing_evidence_preserves_history_and_flags(self):
        event = self.use()['event']
        self.write(self.s, '# Storage\nChanged evidence.\n')
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 0)
        evidence_path = '知识库/公开复用.md'
        self.write(evidence_path, '# Public reuse\n[[知识库/wiki/A]]\n')
        self.use(evidence=evidence_path)
        (self.root / evidence_path).unlink()
        payload = json.loads(manager.Engine(self.root).build()[manager.CANDIDATES])
        self.assertEqual({c.get('evidence_status') for c in payload['candidates'] if c['kind'] == 'evidence_review'}, {'changed', 'missing'})
        self.restore(event)
        self.assertEqual(len(manager.read_jsonl(self.root, manager.EVENTS)), 3)

    def test_stale_decision_kept_with_pending_review(self):
        self.decide('reference', replacement=self.b)
        self.write(self.review, '# Updated public review.\n')
        state = self.rows()[self.a]['lifecycle']
        self.assertEqual(state['state'], 'reference')
        self.assertTrue(state['pending_review'])

    def test_rejects_new_bad_evidence_without_mutation(self):
        before = self.snapshot()
        self.run_cli('record-use', self.a, '--evidence', self.s, '--reason', 'x', '--sha256', '0' * 64, expected=2)
        self.use(evidence='知识库/missing.md', expected=2)
        self.run_cli('record-use', self.a, '--evidence', self.s, '--reason', '', expected=2)
        self.assertEqual(before, self.snapshot())

    def test_rejects_missing_replacement_cycles_and_self_reference(self):
        self.decide('merged', expected=2)
        self.decide('superseded', replacement='知识库/wiki/missing.md', expected=2)
        self.decide('merged', replacement=self.a, expected=2)
        self.decide('reference', replacement=self.b)
        before = self.snapshot()
        self.decide('reference', note=self.b, replacement=self.a, expected=2)
        self.decide('active', replacement=self.b, expected=2)
        self.assertEqual(before, self.snapshot())

    def test_superseded_and_merged_have_live_replacement(self):
        for state in ('superseded', 'merged'):
            event = self.decide(state, replacement=self.b)['event']
            self.assertEqual(self.rows()[self.a]['lifecycle']['state'], state)
            self.assertEqual(self.rows()[self.a]['canonical'], self.b)
            self.restore(event)

    def test_rejects_traversal_hidden_and_symlinks(self):
        before = self.snapshot()
        for path in ('../A.md', '/etc/passwd', '知识库/../wiki/A.md', '知识库//wiki/A.md', '.private/A.md'):
            self.use(evidence=path, expected=2)
        self.assertEqual(before, self.snapshot())
        symlink = self.root / '知识库/linked.md'
        symlink.symlink_to(self.root / self.s)
        self.use(evidence='知识库/linked.md', expected=2)
        symlink.unlink()
        self.run_cli('apply')
        generated = self.root / manager.VIEW
        generated.unlink()
        generated.symlink_to(self.root / self.a)
        source_before = (self.root / self.a).read_bytes()
        self.run_cli('apply', expected=2)
        self.assertEqual((self.root / self.a).read_bytes(), source_before)

    def test_config_alias_cycles_rejected(self):
        self.config['canonical_aliases'] = {self.a: self.b, self.b: self.a}
        self.save_config()
        self.run_cli('plan', expected=2)

    def test_duplicates_only_produce_candidates_never_lifecycle_change(self):
        self.write(self.b, '---\ntype: concept\n---\n# Different H1\nOriginal A.\n')
        payload = self.run_cli('plan')
        duplicates = [c for c in payload['candidates']['candidates'] if c['kind'] == 'duplicate_body']
        self.assertTrue(any(c['notes'] == [self.a, self.b] for c in duplicates))
        self.run_cli('apply')
        self.assertEqual(self.rows()[self.b]['lifecycle']['state'], 'active')
        self.assertEqual(manager.read_jsonl(self.root, manager.EVENTS), [])

    def test_bad_event_schema_and_restore_targets_rejected(self):
        self.restore('missing-event', expected=2)
        event = self.use()['event']
        self.restore(event)
        self.restore(event, expected=2)
        rows = manager.read_jsonl(self.root, manager.EVENTS)
        rows[0]['surprise'] = 'unknown field'
        self.write(manager.EVENTS, '\n'.join(json.dumps(r) for r in rows) + '\n')
        self.run_cli('plan', expected=2)

    def test_public_review_findings_are_read_only_candidates(self):
        self.config['review_findings'] = [{'id': 'R1', 'notes': [self.a, self.b],
            'reason': 'Potential overlap; keep both pending review.',
            'evidence': {'path': self.review, 'sha256': hashlib.sha256((self.root / self.review).read_bytes()).hexdigest()}}]
        self.save_config()
        result = self.run_cli('plan')
        finding = result['candidates']['candidates'][0]
        self.assertEqual(finding['kind'], 'review_finding')
        self.assertIsNone(finding['automatic_action'])
        self.assertTrue(all(r['lifecycle']['state'] == 'active' for r in self.rows().values()))

    def test_tampered_generated_output_detected_and_audited_once(self):
        self.run_cli('apply')
        self.write(manager.VIEW, 'Manually edited generated output.\n')
        self.run_cli('check', expected=1)
        changed = self.run_cli('apply')['changed']
        self.assertEqual(changed, [manager.VIEW])
        self.assertEqual(len(manager.read_jsonl(self.root, manager.JOURNAL)), 2)
        self.run_cli('apply')
        self.assertEqual(len(manager.read_jsonl(self.root, manager.JOURNAL)), 2)

    def test_exact_content_mirrors_cannot_inflate_use(self):
        mirror = '知识库/公开复用镜像.md'
        self.write(mirror, (self.root / self.s).read_text())
        self.use()
        self.use(evidence=mirror)
        self.assertEqual(self.rows()[self.a]['importance']['observed_uses'], 1)

    def test_reviewed_note_and_replacement_hashes_are_actual_and_guard_change(self):
        event_id = self.decide('reference', replacement=self.b)['event']
        event = manager.read_jsonl(self.root, manager.EVENTS)[0]
        self.assertEqual(event['note_sha256'], hashlib.sha256((self.root / self.a).read_bytes()).hexdigest())
        self.assertEqual(event['replacement_sha256'], hashlib.sha256((self.root / self.b).read_bytes()).hexdigest())
        self.write(self.b, (self.root / self.b).read_text() + 'New replacement content.\n')
        self.assertTrue(self.rows()[self.a]['lifecycle']['pending_review'])
        candidates = self.run_cli('plan')['candidates']['candidates']
        self.assertTrue(any(c['kind'] == 'decision_content_review' for c in candidates))
        self.restore(event_id)
        self.assertEqual(self.rows()[self.a]['lifecycle']['state'], 'active')

    def test_resolved_duplicates_do_not_remain_pending_and_restore_reopens(self):
        self.write(self.b, '---\ntype: concept\n---\n# Different H1\nOriginal A.\n')
        event = self.decide('reference', replacement=self.b)['event']
        payload = self.run_cli('plan')['candidates']
        self.assertFalse(any(c.get('notes') == [self.a, self.b] for c in payload['candidates']))
        self.assertTrue(any(c.get('notes') == [self.a, self.b] and c['resolution'] == 'canonicalized_main_view'
                            for c in payload['resolved_duplicates']))
        self.restore(event)
        payload = self.run_cli('plan')['candidates']
        self.assertTrue(any(c.get('notes') == [self.a, self.b] for c in payload['candidates']))

    def test_journal_preserves_reasons_signals_rank_and_lifecycle_transition(self):
        self.run_cli('apply')
        first = manager.read_jsonl(self.root, manager.JOURNAL)[0]
        self.assertTrue(all(t['actions'] == ['initialized'] for t in first['transitions']))
        self.use()
        self.run_cli('apply')
        second = manager.read_jsonl(self.root, manager.JOURNAL)[1]
        change = next(t for t in second['transitions'] if t['path'] == self.a)
        self.assertIn('signals_changed', change['actions'])
        self.assertEqual(change['before']['importance']['observed_uses'], 0)
        self.assertEqual(change['after']['importance']['observed_uses'], 1)
        event = self.decide('reference', replacement=self.b)['event']
        self.run_cli('apply')
        last = manager.read_jsonl(self.root, manager.JOURNAL)[-1]
        change = next(t for t in last['transitions'] if t['path'] == self.a)
        self.assertIn('left_main', change['actions'])
        self.assertEqual(change['lifecycle_event']['id'], event)
        self.assertTrue(change['lifecycle_event']['reason'])
        self.assertTrue(change['reasons'])
        reversal = self.restore(event)['event']
        self.run_cli('apply')
        last = manager.read_jsonl(self.root, manager.JOURNAL)[-1]
        change = next(t for t in last['transitions'] if t['path'] == self.a)
        self.assertEqual(change['event_history'][-1]['id'], reversal)
        self.assertEqual(change['event_history'][-1]['type'], 'restore')
        self.assertTrue(change['event_history'][-1]['reason'])

    def test_malformed_generated_json_is_repaired_without_traceback(self):
        self.run_cli('apply')
        self.write(manager.PRIORITY, '{"main":[{"path":"broken"}],"alternate":[]}')
        self.run_cli('apply')
        self.assertTrue(self.run_cli('check')['fresh'])
        last = manager.read_jsonl(self.root, manager.JOURNAL)[-1]
        self.assertTrue(all(t['actions'] == ['regenerated_without_valid_baseline'] for t in last['transitions']))

    def test_malformed_rank_baseline_is_repaired(self):
        self.run_cli('apply')
        bad = json.loads((self.root / manager.PRIORITY).read_text())
        bad['main'][0]['rank'] = 'bogus'
        self.write(manager.PRIORITY, json.dumps(bad))
        self.run_cli('apply')
        self.assertTrue(self.run_cli('check')['fresh'])

    def test_corrupted_journal_blocks_check_and_noop_apply_without_mutation(self):
        self.run_cli('apply')
        self.write(manager.JOURNAL, 'not json\n')
        before = self.snapshot()
        self.run_cli('check', expected=2)
        self.run_cli('apply', expected=2)
        self.assertEqual(before, self.snapshot())

    def test_missing_or_hash_mismatched_journal_cannot_claim_fresh(self):
        self.run_cli('apply')
        journal = self.root / manager.JOURNAL
        original = journal.read_bytes()
        journal.unlink()
        result = self.run_cli('check', expected=1)
        self.assertIn('missing_execution_record', result['audit_issues'])
        before = self.snapshot()
        self.run_cli('apply', expected=2)
        self.assertEqual(before, self.snapshot())
        journal.write_bytes(original)
        rows = manager.read_jsonl(self.root, manager.JOURNAL)
        rows[-1]['current'][manager.VIEW] = '0' * 64
        self.write(manager.JOURNAL, json.dumps(rows[-1]) + '\n')
        result = self.run_cli('check', expected=1)
        self.assertIn('journal_hash_mismatch:' + manager.VIEW, result['audit_issues'])
        self.run_cli('apply', expected=2)

    def test_malformed_event_types_are_clean_schema_errors(self):
        self.decide('reference')
        rows = manager.read_jsonl(self.root, manager.EVENTS)
        rows[0]['state'] = []
        self.write(manager.EVENTS, json.dumps(rows[0]) + '\n')
        self.run_cli('plan', expected=2)

    def test_generated_wikilinks_resolve_in_existing_linter(self):
        outputs = manager.Engine(self.root).build()
        resolver = manager.Resolver(set(self.rows()) | set(manager.OUTPUTS) | {manager.EVENTS, manager.JOURNAL,
            '知识库/动态管理规则.md', '知识库/维护记录/待核验与知识缺口.md'})
        for match in manager.WIKI.finditer(outputs[manager.VIEW].decode()):
            status, _ = resolver.resolve(manager.VIEW, match[1])
            self.assertEqual(status, 'resolved', match[1])

    def test_age_and_confidence_do_not_change_importance(self):
        before = self.rows()[self.a]['importance']
        self.write(self.a, (self.root / self.a).read_text().replace('0.1', '0.999').replace('1900-01-01', '2999-01-01'))
        self.assertEqual(before, self.rows()[self.a]['importance'])


if __name__ == '__main__':
    unittest.main()
