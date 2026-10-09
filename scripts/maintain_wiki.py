#!/usr/bin/env python3
"""Run structural preflight and deterministic dynamic-index maintenance.

Default writes only manage_wiki's generated outputs/audit journal. --check is
read-only and fails for stale outputs. No git, network, scheduler or note edits.
"""
import argparse
import pathlib
import subprocess
import sys


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default='.')
    p.add_argument('--inventory', help='Optional complete Git tree for a text-only snapshot')
    p.add_argument('--check', action='store_true', help='Validate only; never regenerate')
    a = p.parse_args(argv)
    root = pathlib.Path(a.root).resolve()
    lint = [sys.executable, str(root / 'scripts/lint_wiki.py'), str(root)]
    if a.inventory:
        lint += ['--inventory', str(pathlib.Path(a.inventory).resolve())]
    engine = [sys.executable, str(root / 'scripts/manage_wiki.py'), '--root', str(root), 'check' if a.check else 'apply']
    for cmd in [lint, engine] + ([] if a.check else [lint]):
        result = subprocess.run(cmd, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
