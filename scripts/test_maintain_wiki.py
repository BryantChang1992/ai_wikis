import pathlib
import subprocess
import unittest
from unittest.mock import patch
import maintain_wiki


class WorkflowTests(unittest.TestCase):
    def run_workflow(self, args, codes):
        with patch('maintain_wiki.subprocess.run', side_effect=[subprocess.CompletedProcess([], c) for c in codes]) as run:
            result = maintain_wiki.main(args)
            return result, [call.args[0] for call in run.call_args_list]

    def test_preflight_failure_prevents_mutating_engine(self):
        result, calls = self.run_workflow([], [1])
        self.assertEqual(result, 1)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][1].endswith('lint_wiki.py'))

    def test_check_only_uses_read_only_engine(self):
        result, calls = self.run_workflow(['--check'], [0, 0])
        self.assertEqual(result, 0)
        self.assertEqual(calls[1][-1], 'check')
        self.assertEqual(len(calls), 2)

    def test_apply_has_postflight_and_inventory(self):
        result, calls = self.run_workflow(['--inventory', 'tree.json'], [0, 0, 0])
        self.assertEqual(result, 0)
        self.assertEqual(calls[1][-1], 'apply')
        self.assertEqual(calls[0], calls[2])
        self.assertEqual(calls[0][-2], '--inventory')
        self.assertEqual(calls[0][-1], str(pathlib.Path('tree.json').resolve()))

    def test_engine_failure_stops_postflight(self):
        result, calls = self.run_workflow([], [0, 2])
        self.assertEqual(result, 2)
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
