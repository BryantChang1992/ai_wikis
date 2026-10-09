#!/usr/bin/env python3
"""Reversible, evidence-backed Wiki management; Python standard library only.

Inputs: 知识库/维护记录/动态管理/{config.json,events.jsonl}.
Only apply rewrites the three named generated views and appends execution.jsonl.
record-use/decision/restore append events.jsonl; no command edits a knowledge page.
plan and check are read-only. Importance is a transparent lexicographic reading
order, NOT credibility. There is no age decay, access telemetry, or deletion.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
from collections import defaultdict

sys.dont_write_bytecode = True  # plan/check must not create import caches in the vault.

from lint_wiki import Resolver, WIKI, as_list, frontmatter, markdown_links, without_code

MANAGEMENT = '知识库/维护记录/动态管理'
CONFIG = MANAGEMENT + '/config.json'
EVENTS = MANAGEMENT + '/events.jsonl'
JOURNAL = MANAGEMENT + '/execution.jsonl'
PRIORITY = MANAGEMENT + '/priority.json'
CANDIDATES = MANAGEMENT + '/candidates.json'
VIEW = '知识库/阅读优先级.md'
OUTPUTS = (PRIORITY, CANDIDATES, VIEW)
STATES = {'active', 'reference', 'superseded', 'merged'}


def digest(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value, label):
    require(isinstance(value, str) and value.strip(), label + ' must be a nonempty string')
    return value


def safe_path(root, name, must_exist=False):
    """Only explicit portable repo paths, never traversal or symlink writes/reads."""
    nonempty(name, 'path')
    parts = name.split('/')
    require(not name.startswith('/') and not any(x in ('', '.', '..') for x in parts)
            and '\\' not in name and not re.match(r'^[A-Za-z]:', name)
            and not any(ord(c) < 32 for c in name), 'unsafe repository path: ' + name)
    require(not any(p.startswith('.') for p in parts), 'hidden repository path disallowed: ' + name)
    path = root.joinpath(*parts)
    for parent in [path, *path.parents]:
        if parent == root:
            break
        require(not parent.is_symlink(), 'symlink path disallowed: ' + name)
    require(path.resolve().is_relative_to(root), 'path escapes repository: ' + name)
    if must_exist:
        require(path.is_file(), 'missing file: ' + name)
    return path


def beneath(path, roots):
    return any(path.startswith(r + '/') for r in roots)


def list_strings(value, label):
    require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value),
            label + ' must be a list of nonempty strings')
    require(len(value) == len(set(value)), label + ' contains duplicates')
    return value


def read_jsonl(root, name):
    path = safe_path(root, name)
    if not path.exists():
        return []
    result = []
    for line, text in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        require(text.strip(), '%s:%d: empty JSONL record' % (name, line))
        try:
            row = json.loads(text)
        except ValueError as exc:
            raise ValueError('%s:%d: %s' % (name, line, exc)) from exc
        require(isinstance(row, dict), '%s:%d: expected object' % (name, line))
        result.append(row)
    return result


class Engine:
    def __init__(self, root, additional_events=None):
        self.root = pathlib.Path(root).resolve()
        self.config = json.loads(safe_path(self.root, CONFIG, True).read_text(encoding='utf-8'))
        self.validate_config()
        self.notes = self.read_notes()
        self.resolver = Resolver(self.notes)
        self.events = read_jsonl(self.root, EVENTS) + (additional_events or [])
        self.validate_events()
        self.enabled = self.enabled_events(self.events)
        self.states = {p: {'state': 'active', 'replacement': None, 'event': None,
                           'pending_review': False} for p in self.notes}
        self.evidence_status = {}
        self.decision_content_status = {}
        for event in self.events:
            if not self.enabled[event['id']]:
                continue
            status = self.evidence_check(event['evidence'])
            self.evidence_status[event['id']] = status
            if event['type'] == 'decision':
                content_status = {'note': 'verified' if self.notes[event['note']]['sha256'] == event['note_sha256'] else 'changed'}
                if event.get('replacement'):
                    content_status['replacement'] = ('verified' if self.notes[event['replacement']]['sha256'] == event['replacement_sha256'] else 'changed')
                self.decision_content_status[event['id']] = content_status
                self.states[event['note']] = {'state': event['state'],
                    'replacement': event.get('replacement'), 'event': event['id'],
                    'pending_review': status != 'verified' or 'changed' in content_status.values()}
        self.aliases = dict(self.config.get('canonical_aliases', {}))
        for note, state in self.states.items():
            if state['replacement']:
                self.aliases[note] = state['replacement']
        for source, target in self.aliases.items():
            self.note_path(source)
            self.note_path(target)
            require(source != target, 'self replacement: ' + source)
        self.canonical = {p: self.resolve_alias(p) for p in self.notes}
        for note, state in self.states.items():
            if state['state'] in ('merged', 'superseded'):
                require(self.states[self.canonical[note]]['state'] in ('active', 'reference'),
                        'replacement must end at a live note: ' + note)
        self.findings = self.validate_findings()

    def validate_config(self):
        c = self.config
        require(isinstance(c, dict) and c.get('schema_version') == 1, 'config schema_version must be 1')
        allowed = {'schema_version', 'note_roots', 'public_evidence_roots', 'research_tags',
                   'domain_groups', 'canonical_aliases', 'review_findings'}
        require(not set(c) - allowed, 'unknown config keys: ' + ', '.join(sorted(set(c) - allowed)))
        for key in ('note_roots', 'public_evidence_roots', 'research_tags'):
            list_strings(c.get(key), key)
        require(c['note_roots'] and c['public_evidence_roots'], 'root lists must not be empty')
        for name in c['note_roots'] + c['public_evidence_roots']:
            safe_path(self.root, name)
        require(isinstance(c.get('domain_groups'), list), 'domain_groups must be a list')
        ids = set()
        for group in c['domain_groups']:
            require(isinstance(group, dict) and set(group) == {'id', 'tags'}, 'invalid domain group')
            nonempty(group['id'], 'domain id')
            require(group['id'] not in ids, 'duplicate domain id')
            ids.add(group['id'])
            list_strings(group['tags'], 'domain tags')
        require(isinstance(c.get('canonical_aliases', {}), dict), 'canonical_aliases must be an object')
        require(isinstance(c.get('review_findings', []), list), 'review_findings must be a list')

    def read_notes(self):
        notes = {}
        for name in self.config['note_roots']:
            directory = safe_path(self.root, name)
            require(directory.is_dir(), 'missing note root: ' + name)
            for file in sorted(directory.rglob('*.md')):
                path = file.relative_to(self.root).as_posix()
                safe_path(self.root, path, True)
                if path in OUTPUTS or path.startswith(MANAGEMENT + '/'):
                    continue
                if file.name.lower() in ('readme.md', 'log.md') or file.name.lower().startswith('lint-'):
                    continue
                raw = file.read_text(encoding='utf-8')
                meta, duplicates, _, end = frontmatter(raw)
                require(not duplicates, 'duplicate metadata keys in ' + path)
                if meta.get('type') == 'meta':
                    continue
                tags = {str(t) for t in as_list(meta.get('tags')) if t}
                notes[path] = {'raw': raw, 'sha256': digest(file.read_bytes()), 'meta': meta, 'body': '\n'.join(raw.splitlines()[end:]), 'tags': tags}
        return notes

    def note_path(self, name):
        safe_path(self.root, name)
        require(name in self.notes, 'not an eligible explicit note path: ' + name)
        return name

    def evidence_shape(self, evidence):
        require(isinstance(evidence, dict) and set(evidence) == {'path', 'sha256'},
                'evidence must contain exactly path and sha256')
        path = evidence['path']
        safe_path(self.root, path)
        require(beneath(path, self.config['public_evidence_roots']), 'evidence outside public roots: ' + path)
        require(path not in OUTPUTS and not path.startswith(MANAGEMENT + '/'),
                'management output/input is not public use evidence: ' + path)
        require(isinstance(evidence['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', evidence['sha256']),
                'evidence sha256 must be lowercase SHA-256')

    def evidence_check(self, evidence):
        self.evidence_shape(evidence)
        path = safe_path(self.root, evidence['path'])
        if not path.is_file():
            return 'missing'
        return 'verified' if digest(path.read_bytes()) == evidence['sha256'] else 'changed'

    @staticmethod
    def enabled_events(events):
        enabled = {event['id']: True for event in events}
        for event in reversed(events):
            if enabled[event['id']] and event['type'] == 'restore':
                enabled[event['target']] = False
        return enabled

    def validate_events(self):
        seen = {}
        for event in self.events:
            require(event.get('schema_version') == 1, 'event schema_version must be 1')
            ident = nonempty(event.get('id'), 'event id')
            require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*', ident), 'invalid event id')
            require(ident not in seen, 'duplicate event id: ' + ident)
            kind = event.get('type')
            fields = {'schema_version', 'id', 'type', 'reason', 'evidence'}
            nonempty(event.get('reason'), 'event reason')
            self.evidence_shape(event.get('evidence'))
            if kind == 'use':
                fields |= {'note'}
                self.note_path(event.get('note'))
            elif kind == 'decision':
                fields |= {'note', 'state', 'replacement', 'note_sha256', 'replacement_sha256'}
                self.note_path(event.get('note'))
                require(isinstance(event.get('state'), str) and event['state'] in STATES, 'invalid lifecycle state')
                require(isinstance(event.get('note_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', event['note_sha256']), 'decision needs actual reviewed note_sha256')
                replacement = event.get('replacement')
                if replacement is not None:
                    self.note_path(replacement)
                    require(replacement != event['note'], 'self replacement')
                    require(isinstance(event.get('replacement_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', event['replacement_sha256']), 'decision needs actual reviewed replacement_sha256')
                else:
                    require(event.get('replacement_sha256') is None, 'replacement_sha256 requires replacement')
                require(event['state'] not in ('merged', 'superseded') or replacement,
                        'merged/superseded requires a replacement')
                require(event['state'] != 'active' or replacement is None, 'active cannot have replacement')
            elif kind == 'restore':
                fields |= {'target'}
                require(isinstance(event.get('target'), str) and event['target'] in seen, 'restore target must be an earlier event')
                require(self.enabled_events(list(seen.values()))[event['target']],
                        'restore target is already reversed; reverse its restore to redo')
            else:
                raise ValueError('unknown event type: ' + str(kind))
            require(not set(event) - fields, 'unknown event fields: ' + ', '.join(sorted(set(event) - fields)))
            seen[ident] = event

    def resolve_alias(self, path):
        seen = set()
        while path in self.aliases:
            require(path not in seen, 'replacement/alias cycle: ' + path)
            seen.add(path)
            path = self.aliases[path]
        return path

    def validate_findings(self):
        result, ids = [], set()
        for row in self.config.get('review_findings', []):
            require(isinstance(row, dict) and set(row) == {'id', 'notes', 'reason', 'evidence'},
                    'invalid review finding fields')
            nonempty(row['id'], 'finding id')
            require(row['id'] not in ids, 'duplicate finding id')
            ids.add(row['id'])
            nonempty(row['reason'], 'finding reason')
            list_strings(row['notes'], 'finding notes')
            require(row['notes'], 'finding must reference notes')
            for note in row['notes']:
                self.note_path(note)
            self.evidence_shape(row['evidence'])
            result.append(dict(row, kind='review_finding', automatic_action=None,
                               evidence_status=self.evidence_check(row['evidence'])))
        return result

    def links(self, source, text):
        text = without_code(text)
        targets = set()
        for raw, kind in [(m[1], 'wiki') for m in WIKI.finditer(text)] + [
                (raw, 'markdown') for raw, _ in markdown_links(text)]:
            status, hits = self.resolver.resolve(source, raw, kind)
            if status == 'resolved':
                targets.update(hits)
        return targets

    def use_has_link(self, event):
        path = safe_path(self.root, event['evidence']['path'])
        if path.suffix.lower() != '.md':
            return False
        raw = path.read_text(encoding='utf-8')
        meta, _, _, end = frontmatter(raw)
        if path.name.lower() in ('readme.md', 'log.md') or meta.get('type') == 'meta':
            return False
        canonical = self.canonical[event['note']]
        artifact = self.canonical.get(event['evidence']['path'], event['evidence']['path'])
        if artifact == canonical:
            return False
        # A sources/related frontmatter list alone is not observed public reuse.
        body = '\n'.join(raw.splitlines()[end:])
        targets = self.links(event['evidence']['path'], body)
        return any(self.canonical[t] == canonical for t in targets if t in self.canonical)

    def domain(self, path):
        tags = self.notes[path]['tags']
        return next((g['id'] for g in self.config['domain_groups'] if tags.intersection(g['tags'])), None)

    def build(self):
        uses = defaultdict(list)
        candidates = list(self.findings)
        resolved_duplicates = []
        for event in self.events:
            if not self.enabled[event['id']]:
                continue
            status = self.evidence_status[event['id']]
            if event['type'] == 'use' and status == 'verified' and not self.use_has_link(event):
                status = 'no_explicit_note_link'
            if status != 'verified':
                candidates.append({'kind': 'evidence_review', 'event': event['id'],
                    'event_type': event['type'], 'evidence': event['evidence'],
                    'evidence_status': status, 'automatic_action': None,
                    'reason': 'Historical evidence requires review; use is excluded, explicit lifecycle is retained.'})
            elif event['type'] == 'use':
                uses[self.canonical[event['note']]].append(event)
            if event['type'] == 'decision' and 'changed' in self.decision_content_status[event['id']].values():
                candidates.append({'kind': 'decision_content_review', 'event': event['id'],
                    'note': event['note'], 'replacement': event.get('replacement'),
                    'content_status': self.decision_content_status[event['id']],
                    'automatic_action': None, 'reason': 'Reviewed note or replacement changed; retain explicit decision pending review.'})
        inbound = defaultdict(lambda: defaultdict(set))
        for source, data in self.notes.items():
            source_canonical = self.canonical[source]
            group = self.domain(source_canonical)
            if group is None:
                continue
            for target in self.links(source, data['raw']):
                target_canonical = self.canonical[target]
                if source_canonical != target_canonical:
                    inbound[target_canonical][group].add(source_canonical)
        duplicate_bodies = defaultdict(list)
        for note, data in self.notes.items():
            body = '\n'.join(line.rstrip() for line in data['body'].splitlines()
                             if not re.match(r'^#\s+', line)).strip()
            if body:
                duplicate_bodies[digest(body)].append(note)
        for body_hash, notes in sorted(duplicate_bodies.items()):
            if len(notes) > 1:
                row = {'kind': 'duplicate_body', 'notes': sorted(notes),
                    'body_sha256': body_hash, 'automatic_action': None,
                    'reason': 'Identical body after excluding H1 and trailing spaces; review scope and stable links before any decision.'}
                resolved = (len({self.canonical[n] for n in notes}) == 1
                    and sum(self.states[n]['state'] == 'active' for n in notes) == 1
                    and not any(self.states[n]['pending_review'] for n in notes))
                if resolved:
                    row.update(resolution='canonicalized_main_view',
                        decision_events=sorted(self.states[n]['event'] for n in notes if self.states[n]['event']),
                        reason='Explicit lifecycle decisions select one main entry; physical bodies and paths intentionally preserved.')
                    resolved_duplicates.append(row)
                else:
                    candidates.append(row)
        rows = []
        for path, data in sorted(self.notes.items()):
            canonical = self.canonical[path]
            state = self.states[path]
            matched = sorted(data['tags'].intersection(self.config['research_tags']))
            group_sources = {g: sorted(sources) for g, sources in sorted(inbound[canonical].items())}
            use_ids = self.deduplicated_use_ids(uses[canonical])
            rows.append({'path': path, 'title': data['meta'].get('title') or pathlib.PurePosixPath(path).stem,
                'canonical': canonical, 'lifecycle': state,
                'importance': {'research_match': bool(matched), 'matched_research_tags': matched,
                    'observed_uses': len(use_ids), 'use_events': use_ids,
                    'inbound_domain_count': len(group_sources), 'inbound_domains': group_sources},
                'credibility': {'confidence': data['meta'].get('confidence'),
                    'confidence_rationale': data['meta'].get('confidence_rationale'),
                    'source_checked': data['meta'].get('source_checked'),
                    'source_check_scope': data['meta'].get('source_check_scope'),
                    'status': data['meta'].get('status'), 'independently_verified_by_manager': False}})
        rows.sort(key=lambda row: (-int(row['importance']['research_match']),
                    -row['importance']['observed_uses'], -row['importance']['inbound_domain_count'], row['path']))
        main = [row for row in rows if row['lifecycle']['state'] == 'active']
        alternate = [row for row in rows if row['lifecycle']['state'] != 'active']
        for rank, row in enumerate(main, 1):
            row['rank'] = rank
        manifest = {'config': self.config, 'events': self.events,
                    'notes': {p: d['sha256'] for p, d in sorted(self.notes.items())},
                    'event_evidence': self.evidence_status,
                    'finding_evidence': [f['evidence_status'] for f in self.findings]}
        input_hash = digest(encoded(manifest))
        payload = {'schema_version': 1, 'input_sha256': input_hash,
            'method': {'order': ['research_match descending', 'observed_uses descending',
                               'inbound_domain_count descending', 'path ascending'],
                       'domain_assignment': 'First matching configured domain group of canonical source.',
                       'access_telemetry': 'Not collected. Zero means no verified recorded public reuse.',
                       'use_deduplication': 'One verified public artifact per canonical note; canonical paths and exact-content mirrors collapse; revisions do not add uses.',
                       'credibility': 'Reported metadata only; citations, use, age and importance never establish truth.',
                       'lifecycle': 'Explicit reversible events only; source text and paths unchanged.'},
            'main': main, 'alternate': alternate}
        candidate_payload = {'schema_version': 1, 'input_sha256': input_hash,
                             'automatic_actions': ['rebuild_generated_views'], 'candidates': candidates,
                             'resolved_duplicates': resolved_duplicates}
        return {PRIORITY: encoded(payload), CANDIDATES: encoded(candidate_payload),
                VIEW: self.render(payload, len(candidates)).encode('utf-8')}

    def deduplicated_use_ids(self, events):
        # Union path identity and exact bytes: aliases, revisions and exact mirrors
        # cannot create artificial repeat use, including transitive alias groups.
        parent = {}
        def find(key):
            parent.setdefault(key, key)
            while parent[key] != key:
                parent[key] = parent[parent[key]]
                key = parent[key]
            return key
        for event in events:
            evidence = event['evidence']
            artifact = self.canonical.get(evidence['path'], evidence['path'])
            left, right = find(('path', artifact)), find(('hash', evidence['sha256']))
            parent[right] = left
        groups = {}
        for event in events:
            key = find(('hash', event['evidence']['sha256']))
            groups[key] = min(groups.get(key, event['id']), event['id'])
        return sorted(groups.values())

    @staticmethod
    def render(payload, candidate_count):
        lines = ['---', 'type: meta', 'title: 阅读优先级（自动生成）', '---', '', '# 阅读优先级', '',
            '此页由 scripts/manage_wiki.py 生成；不要手工修改。源页正文、稳定路径和可信度元数据均保留。', '',
            '按「匹配当前研究标签 → 有公开证据的去重使用次数 → 不同入链领域数 → 路径」排序。',
            '重要性不等于可信度；不按年龄或 confidence 排序。0 次表示没有已验证的公开复用记录，不代表无人阅读。',
            '每个规范来源页只按配置中首个匹配领域归组；别名折叠后计数。引用多不代表可信。', '',
            '## 当前阅读入口', '',
            '| 顺序 | 页面 | 当前研究匹配 | 已验证公开复用 | 入链领域 | 可信度备注 |',
            '|---|---|---|---|---|---|']
        def cell(value):
            return str(value).replace('|', '\\|').replace('\n', ' ')
        def link(row):
            return '[[%s]]' % row['path'][:-3]
        for row in payload['main']:
            importance = row['importance']
            confidence = row['credibility']['confidence']
            cred = '未记录；未由本工具核验' if confidence is None else '历史值 %s；未由本工具核验' % cell(confidence)
            pending = '；决策证据待复核' if row['lifecycle']['pending_review'] else ''
            lines.append('| %d | %s | %s | %d | %d | %s%s |' % (row['rank'], link(row),
                cell('、'.join(importance['matched_research_tags']) or '无'), importance['observed_uses'],
                importance['inbound_domain_count'], cred, pending))
        lines += ['', '## 保留参考与替代入口', '',
                  '只有显式生命周期决策把页面移到此表；不删除、不搬移、不自动合并正文。', '',
                  '| 页面 | 状态 | 替代入口 | 决策 | 证据状态 |', '|---|---|---|---|---|']
        for row in payload['alternate']:
            state = row['lifecycle']
            target = state['replacement']
            lines.append('| %s | %s | %s | %s | %s |' % (link(row), state['state'],
                '[[%s]]' % target[:-3] if target else '无', cell(state['event']),
                '待复核；保留原决策' if state['pending_review'] else '已核对文件哈希'))
        lines += ['', '## 维护与边界', '',
            '- 自动结构/证据候选：%d；仅供审阅，不会自动更改生命周期，也不代表全部语义缺口已解决。' % candidate_count,
            '- 详细信号与证据：[[知识库/维护记录/动态管理/priority.json]]；候选：[[知识库/维护记录/动态管理/candidates.json]]。',
            '- 事件：[[知识库/维护记录/动态管理/events.jsonl]]；执行审计：[[知识库/维护记录/动态管理/execution.jsonl]]。',
            '- 规则：[[知识库/动态管理规则]]；人工语义缺口：[[知识库/维护记录/待核验与知识缺口]]。',
            '- record-use、decision、restore 只追加事件；apply 只重建命名的管理视图。',
            '- 历史证据变动会提示待复核，并从使用计数排除；不会抹除历史事件。',
            '', '输入指纹：' + payload['input_sha256'], '']
        return '\n'.join(lines)


def changed_outputs(engine, outputs):
    return [name for name, value in outputs.items()
            if not safe_path(engine.root, name).is_file() or safe_path(engine.root, name).read_bytes() != value]


def append_jsonl(root, name, value):
    path = safe_path(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.stat().st_nlink == 1, 'hardlinked append target disallowed: ' + name)
    if path.exists() and path.stat().st_size:
        with path.open('rb') as handle:
            handle.seek(-1, os.SEEK_END)
            require(handle.read() == b'\n', 'JSONL must end in newline before append: ' + name)
    with path.open('ab') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8') + b'\n')
        handle.flush()
        os.fsync(handle.fileno())


def journal_transitions(engine, outputs):
    previous_path = safe_path(engine.root, PRIORITY)
    old, baseline = {}, 'initialized'
    if previous_path.is_file():
        try:
            prior = json.loads(previous_path.read_text(encoding='utf-8'))
            require(isinstance(prior['main'], list) and isinstance(prior['alternate'], list), 'invalid previous projection lists')
            old = {r['path']: r for r in prior['main'] + prior['alternate']}
            for path, row in old.items():
                require(isinstance(path, str) and path, 'invalid previous path')
                rank = row.get('rank')
                require(rank is None or (type(rank) is int and rank > 0), 'invalid previous rank')
                require(isinstance(row.get('canonical'), str), 'invalid previous canonical path')
                require(all(isinstance(row.get(field), dict) for field in ('lifecycle', 'importance', 'credibility')), 'invalid previous row types')
                for field in ('lifecycle', 'importance', 'canonical', 'credibility'):
                    row[field]
                row['lifecycle']['event']
            baseline = 'existing'
        except (ValueError, KeyError, TypeError, UnicodeError):
            old = {}
            baseline = 'regenerated_without_valid_baseline'
    current = json.loads(outputs[PRIORITY])
    new = {r['path']: r for r in current['main'] + current['alternate']}
    events = {event['id']: event for event in engine.events}
    def original_note(event):
        while event['type'] == 'restore':
            event = events[event['target']]
        return event['note']
    def summary(row):
        if row is None:
            return None
        return {'rank': row.get('rank'), 'lifecycle': row['lifecycle'],
                'importance': row['importance'], 'canonical': row['canonical']}
    transitions = []
    for path in sorted(set(old) | set(new)):
        before, after = old.get(path), new.get(path)
        if before == after:
            continue
        actions, reasons = [], []
        if before is None:
            actions.append(baseline if baseline != 'existing' else 'added_to_scope')
            reasons.append('First available baseline for this note; no prior promotion or demotion is claimed.')
        elif after is None:
            actions.append('removed_from_scope')
            reasons.append('Note no longer belongs to configured eligible scope; no source file was removed by this tool.')
        else:
            if before['lifecycle'] != after['lifecycle']:
                actions.append('lifecycle_changed')
                reasons.append('Explicit lifecycle event or reviewed evidence status changed.')
            if before['canonical'] != after['canonical']:
                actions.append('canonical_changed')
                reasons.append('Configured alias or explicit replacement changed canonical aggregation.')
            if before['importance'] != after['importance']:
                actions.append('signals_changed')
                reasons.append('Configured research tags, verified public reuse, or distinct inbound domains changed; confidence and age are excluded.')
            old_rank, new_rank = before.get('rank'), after.get('rank')
            if old_rank != new_rank:
                action = ('entered_main' if old_rank is None else 'left_main' if new_rank is None
                          else 'promoted' if new_rank < old_rank else 'demoted')
                actions.append(action)
                reasons.append('Reading order recomputed by research match, public use, domain count and path; relative ranks can change when other notes change.')
            if before['credibility'] != after['credibility']:
                actions.append('reported_metadata_changed')
                reasons.append('Reported credibility metadata changed; it is not used to determine priority.')
            if not actions:
                actions.append('display_changed')
                reasons.append('Display metadata changed without changing importance or lifecycle.')
        event_id = (after or before)['lifecycle']['event']
        transitions.append({'path': path, 'actions': actions, 'reasons': reasons,
                            'before': summary(before), 'after': summary(after),
                            'lifecycle_event': events.get(event_id),
                            'event_history': [dict(event, effective=engine.enabled[event['id']])
                                for event in engine.events
                                if original_note(event) == path]})
    return transitions


def validate_journal(root):
    journal = read_jsonl(root, JOURNAL)
    for sequence, row in enumerate(journal, 1):
        require(row.get('schema_version') == 1 and row.get('type') == 'execution'
                and type(row.get('sequence')) is int and row['sequence'] == sequence,
                'invalid execution journal record or sequence')
        changed = row.get('changed')
        require(isinstance(changed, list) and all(isinstance(p, str) and p in OUTPUTS for p in changed)
                and len(changed) == len(set(changed)), 'invalid execution journal changed paths')
        for field in ('previous', 'current'):
            values = row.get(field)
            require(isinstance(values, dict) and set(values) == set(OUTPUTS), 'invalid execution journal hashes')
            for value in values.values():
                require((field == 'previous' and value is None) or
                        (isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)),
                        'invalid execution journal hash')
        require(isinstance(row.get('input_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', row['input_sha256']),
                'invalid execution journal input hash')
        require(isinstance(row.get('transitions', []), list), 'invalid execution journal transitions')
    return journal


def audit_issues(root, journal):
    files = {name: safe_path(root, name) for name in OUTPUTS}
    if not journal:
        return ['missing_execution_record'] if any(path.exists() for path in files.values()) else []
    return ['journal_hash_mismatch:' + name for name, path in files.items()
            if not path.is_file() or digest(path.read_bytes()) != journal[-1]['current'][name]]


def apply(engine, outputs):
    journal = validate_journal(engine.root)
    changed = changed_outputs(engine, outputs)
    issues = audit_issues(engine.root, journal)
    require('missing_execution_record' not in issues, 'generated files exist without execution record; restore/review the append-only journal')
    if not changed:
        require(not issues, 'execution journal does not attest current generated files; review history')
        return {'changed': [], 'journal_appended': False}
    # Validate journal and every fixed output path before changing anything.
    journal_path = safe_path(engine.root, JOURNAL)
    if journal_path.exists() and journal_path.stat().st_size:
        require(journal_path.read_bytes().endswith(b'\n'), 'execution journal needs final newline')
    for name in OUTPUTS:
        safe_path(engine.root, name)
    previous = {name: digest(safe_path(engine.root, name).read_bytes())
                if safe_path(engine.root, name).is_file() else None for name in OUTPUTS}
    current = {name: digest(value) for name, value in outputs.items()}
    record = {'schema_version': 1, 'type': 'execution', 'sequence': len(journal) + 1,
              'changed': changed, 'previous': previous, 'current': current,
              'phase': 'write_ahead', 'operation': 'rebuild_generated_views',
              'reason': 'Reconcile named generated views with validated current inputs; source notes are untouched.',
              'transitions': journal_transitions(engine, outputs),
              'input_sha256': json.loads(outputs[PRIORITY])['input_sha256']}
    # Write-ahead audit allows an interrupted rebuild to be detected by check and
    # safely retried. A subsequent no-op never appends another execution record.
    append_jsonl(engine.root, JOURNAL, record)
    for name in changed:
        path = safe_path(engine.root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='manage-', delete=False) as handle:
                temporary = handle.name
                handle.write(outputs[name])
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    return {'changed': changed, 'journal_appended': True}


def record(engine, args):
    path = safe_path(engine.root, args.evidence, True)
    evidence = {'path': args.evidence, 'sha256': args.sha256 or digest(path.read_bytes())}
    engine.evidence_shape(evidence)
    require(engine.evidence_check(evidence) == 'verified', 'new evidence hash mismatch')
    event = {'schema_version': 1, 'type': args.command, 'reason': args.reason, 'evidence': evidence}
    if args.command == 'record-use':
        event['type'] = 'use'
        event['note'] = engine.note_path(args.note)
        require(engine.use_has_link(event), 'use evidence must explicitly link to note or canonical alias')
        canonical = engine.canonical[args.note]
        for previous in engine.events:
            if previous['type'] == 'use' and engine.canonical[previous['note']] == canonical and previous['evidence'] == evidence:
                return {'appended': False, 'event': previous['id'], 'enabled': engine.enabled[previous['id']]}
        identity = [canonical, evidence]
    elif args.command == 'decision':
        engine.note_path(args.note)
        if args.replacement:
            engine.note_path(args.replacement)
        event.update(note=args.note, state=args.state, replacement=args.replacement,
            note_sha256=engine.notes[args.note]['sha256'],
            replacement_sha256=engine.notes[args.replacement]['sha256'] if args.replacement else None)
        identity = [engine.events, event]
    else:
        event['target'] = args.event_id
        identity = [engine.events, event]
    event['id'] = event['type'] + '-' + digest(encoded(identity))
    # All validations, including replacement cycles and explicit paths, precede append.
    Engine(engine.root, [event])
    append_jsonl(engine.root, EVENTS, event)
    return {'appended': True, 'event': event['id']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.', help='repository root')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('plan', 'apply', 'check'):
        sub.add_parser(command)
    use = sub.add_parser('record-use')
    use.add_argument('note')
    decision = sub.add_parser('decision')
    decision.add_argument('note')
    decision.add_argument('state', choices=sorted(STATES))
    decision.add_argument('--replacement')
    restore = sub.add_parser('restore')
    restore.add_argument('event_id')
    for command in (use, decision, restore):
        command.add_argument('--evidence', required=True, help='public repository artifact, not private conversation')
        command.add_argument('--sha256', help='expected artifact hash; defaults to current actual content')
        command.add_argument('--reason', required=True, help='public maintenance rationale, no private query text')
    args = parser.parse_args(argv)
    try:
        engine = Engine(args.root)
        journal = validate_journal(engine.root)
        if args.command in ('record-use', 'decision', 'restore'):
            result = record(engine, args)
        else:
            outputs = engine.build()
            changed = changed_outputs(engine, outputs)
            if args.command == 'apply':
                result = apply(engine, outputs)
            elif args.command == 'check':
                issues = audit_issues(engine.root, journal)
                result = {'fresh': not changed and not issues, 'stale_outputs': changed, 'audit_issues': issues}
            else:
                result = {'read_only': True, 'would_change': changed,
                          'audit_issues': audit_issues(engine.root, journal),
                          'priority': json.loads(outputs[PRIORITY]),
                          'candidates': json.loads(outputs[CANDIDATES])}
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.command == 'check' and not result['fresh'] else 0
    except (ValueError, OSError, UnicodeError) as exc:
        print('manage_wiki: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
