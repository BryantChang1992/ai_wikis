#!/usr/bin/env python3
"""Read-only structural audit of an Obsidian-style Markdown vault (Python 3 stdlib).

Usage: python3 scripts/lint_wiki.py . --inventory github-tree.json --format json
The optional GitHub recursive-tree inventory proves path existence only. Content
checks apply only to materialized Markdown. No network access or files are changed.
A small frontmatter reader supports top-level scalars and scalar lists, not full
YAML. Unsupported structured values are reported and never silently validated.
Heading/block anchors, external availability, semantic accuracy, independent source
counts, PDF identity/licensing, and rendered diagrams require separate review.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import posixpath
import re
import sys
import urllib.parse

EXTERNAL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
KEY = re.compile(r"^([A-Za-z_][\w-]*|'[^']+'|\"[^\"]+\"):(?:\s+(.*)|$)")
WIKI = re.compile(r"(?<!\\)\[\[([^\]\n]+)\]\]")


def blank(text):
    return ''.join('\n' if c == '\n' else ' ' for c in text)


def without_code(text):
    """Mask fenced blocks, inline backticks and HTML comments, preserving offsets."""
    out, fence = [], None
    for line in text.splitlines(keepends=True):
        m = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            out.append(blank(line))
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
                fence = None
        elif m:
            fence = m[1]
            out.append(blank(line))
        else:
            out.append(line)
    text = ''.join(out)
    text = re.sub(r'<!--.*?-->', lambda m: blank(m[0]), text, flags=re.S)
    # A closing delimiter must have exactly the opener's number of backticks.
    text = re.sub(r'(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)', lambda m: blank(m[0]), text, flags=re.S)
    return text


def split_flow(value):
    parts, start, quote, depth, escaped = [], 0, None, 0, False
    for i, c in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote:
            if c == '\\' and quote == '"':
                escaped = True
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
        elif c == ',' and depth == 0:
            parts.append(value[start:i].strip())
            start = i + 1
    parts.append(value[start:].strip())
    return parts


def strip_comment(value):
    quote, escaped = None, False
    for i, char in enumerate(value):
        if escaped:
            escaped = False
        elif quote:
            if char == '\\' and quote == '"':
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == '#' and (i == 0 or value[i - 1].isspace()):
            return value[:i].rstrip()
    return value


def scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except ValueError:
            return value[1:-1]
    return re.split(r'\s+#', value, maxsplit=1)[0].rstrip()


def frontmatter(text):
    lines = text.splitlines()
    result, duplicates, unsupported = {}, [], []
    if not lines or lines[0].strip() != '---':
        return result, duplicates, unsupported, 0
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in ('---', '...')), None)
    if end is None:
        return result, duplicates, ['unclosed frontmatter'], 0
    blocks, current = [], None
    for i in range(1, end):
        m = KEY.match(lines[i])
        if m:
            if current:
                blocks.append(current)
            current = [scalar(m[1]), m[2] or '', i + 1, []]
        elif current:
            current[3].append(lines[i])
        elif lines[i].strip() and not lines[i].lstrip().startswith('#'):
            unsupported.append('unparsed line %d' % (i + 1))
    if current:
        blocks.append(current)
    for key, value, line, tail in blocks:
        value = strip_comment(value)
        if key in result:
            duplicates.append({'key': key, 'line': line})
        if value.startswith(('>', '|')):
            parsed = '\n'.join(tail).strip()
        elif value.startswith('{'):
            parsed = None
            unsupported.append('structured value for %s at line %d' % (key, line))
        elif value.startswith('[') and value.endswith(']'):
            parsed = [scalar(x) for x in split_flow(value[1:-1]) if x]
        elif value:
            parsed = scalar(value)
        else:
            significant = [x for x in tail if x.strip() and not x.lstrip().startswith('#')]
            if all(re.match(r'^\s*-\s+', x) for x in significant):
                parsed = [scalar(re.sub(r'^\s*-\s+', '', x)) for x in significant]
            elif significant:
                parsed = None
                unsupported.append('structured value for %s at line %d' % (key, line))
            else:
                parsed = []
        result[key] = parsed
    return result, duplicates, unsupported, end + 1


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def link_target(value):
    return urllib.parse.unquote(value.split('|', 1)[0].split('#', 1)[0].strip())


class Resolver:
    def __init__(self, paths):
        self.paths = set(paths)
        self.top = {p.split('/', 1)[0] for p in self.paths if '/' in p}
        self.basename = collections.defaultdict(set)
        for p in self.paths:
            self.basename[posixpath.basename(p)].add(p)
            if p.lower().endswith('.md'):
                self.basename[posixpath.basename(p)[:-3]].add(p)

    def variants(self, target):
        return [target] if target.endswith('.md') else [target, target + '.md']

    def resolve(self, source, raw, kind='wiki'):
        target = link_target(raw)
        if EXTERNAL.match(target) or target.startswith('//'):
            return 'external', []
        if not target:
            return 'resolved', [source]
        # URLs in Markdown can include query strings; local path checks ignore them.
        target = target.split('?', 1)[0].replace('\\ ', ' ')
        if kind == 'markdown':
            candidate = posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(posixpath.dirname(source), target))
            hits = [candidate] if candidate in self.paths else []
            return ('resolved' if hits else 'missing'), hits
        relative = target.startswith(('./', '../'))
        rooted = target.startswith('/') or target.split('/', 1)[0] in self.top
        if relative:
            candidates = self.variants(posixpath.normpath(posixpath.join(posixpath.dirname(source), target)))
            hits = sorted(set(candidates) & self.paths)
        elif rooted:
            hits = sorted(set(self.variants(posixpath.normpath(target.lstrip('/')))) & self.paths)
        elif '/' not in target:
            hits = sorted(self.basename.get(target, set()))
        else:
            # Obsidian shortest paths can omit a shared ancestor (e.g. wiki/X).
            variants = self.variants(posixpath.normpath(target))
            exact = sorted(set(variants) & self.paths)
            local = [p for p in self.variants(posixpath.normpath(posixpath.join(posixpath.dirname(source), target))) if p in self.paths]
            hits = exact or local or sorted(p for p in self.paths if any(p.endswith('/' + v) for v in variants))
        return ('resolved' if len(hits) == 1 else 'ambiguous' if hits else 'missing'), hits


def markdown_links(text):
    """Yield inline destinations and reference definitions, with balanced () URLs."""
    for m in re.finditer(r'(?<!\\)\]\(', text):
        start, i, depth, escaped = m.end(), m.end(), 1, False
        while i < len(text) and depth:
            c = text[i]
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            i += 1
        if depth:
            continue
        raw = text[start:i - 1].strip()
        if raw.startswith('<') and '>' in raw:
            raw = raw[1:raw.index('>')]
        else:
            raw = re.split(r'\s+[\"\']', raw, maxsplit=1)[0].strip()
        if raw:
            yield raw, start
    for m in re.finditer(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)', text, re.M):
        yield m[1].strip('<>'), m.start(1)


def audit(root, inventory=None):
    root = pathlib.Path(root)
    files = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
    paths = set(files)
    dirs = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_dir() and '.git' not in p.parts}
    tree_blobs = set()
    if inventory:
        raw = json.loads(pathlib.Path(inventory).read_text(encoding='utf-8'))
        if raw.get('truncated'):
            raise ValueError('Inventory is truncated; missing-path conclusions would be unreliable')
        for entry in raw['tree']:
            if entry['type'] == 'blob':
                tree_blobs.add(entry['path'])
            elif entry['type'] == 'tree':
                dirs.add(entry['path'])
        paths.update(tree_blobs)
    resolver = Resolver(paths)
    md_resolver = Resolver(paths | dirs | {d + '/' for d in dirs})
    docs = {p: f.read_text(encoding='utf-8') for p, f in files.items() if p.endswith('.md')}
    issues, infos, metadata, graph = [], [], {}, collections.defaultdict(set)
    counts = collections.Counter()
    source_rows, wiki_links = [], []
    def issue(code, path, detail, line=None, severity='warning', **extra):
        row = dict(code=code, severity=severity, file=path, detail=detail, **extra)
        if line:
            row['line'] = line
        issues.append(row)
    for path, text in sorted(docs.items()):
        fm, dups, unsupported, fm_end = frontmatter(text)
        metadata[path] = fm
        for dup in dups:
            issue('duplicate_frontmatter_key', path, dup['key'], dup['line'], 'error')
        for detail in unsupported:
            issue('unsupported_frontmatter', path, detail, severity='info')
        clean = without_code(text)
        links = [(m[1], m.start(), 'wiki') for m in WIKI.finditer(clean)]
        links += [(target, pos, 'markdown') for target, pos in markdown_links(clean)]
        for raw, pos, kind in links:
            status, hits = (md_resolver if kind == 'markdown' else resolver).resolve(path, raw, kind)
            # These literal tokens explain syntax in meta documents; report them
            # as documentation hygiene rather than missing knowledge targets.
            placeholder = (kind == 'wiki' and status == 'missing' and raw == 'wikilink' and (path in {'知识库/purpose.md', '知识库/schema.md', '知识库/log.md', '团队规范/技术规范/ai-wiki-maintain-skill.md'} or fm.get('type') == 'meta'))
            counts[kind + '_' + ('placeholder' if placeholder else status)] += 1
            line = clean.count('\n', 0, pos) + 1
            if placeholder:
                issue('documentation_placeholder', path, raw, line, 'warning')
            elif status in ('missing', 'ambiguous'):
                issue(kind + '_' + status, path, raw, line, 'error', candidates=hits)
            elif status == 'resolved':
                graph[path].update(h for h in hits if h.endswith('.md') and h != path)
                if kind == 'wiki':
                    wiki_links.append((path, hits[0]))
        if path.startswith('知识库/wiki/') and fm.get('type') != 'meta':
            for field in ('type', 'title', 'tags', 'status', 'created'):
                if not fm.get(field):
                    issue('missing_frontmatter_field', path, field)
            if not fm.get('sources'):
                issue('missing_sources', path, 'No populated sources field; alternate source_citations/body citations require separate review')
        for field in ('sources', 'related'):
            seen = set()
            for value in as_list(fm.get(field)):
                if not isinstance(value, str):
                    continue
                matches = WIKI.findall(value)
                if matches:
                    targets = matches
                elif field == 'sources':
                    targets = [value]
                else:
                    targets = []
                for raw in targets:
                    status, hits = resolver.resolve(path, raw)
                    key = tuple(hits) if status == 'resolved' else raw
                    if key in seen:
                        issue('duplicate_' + field, path, raw)
                    seen.add(key)
                    if field == 'related' and hits == [path]:
                        issue('self_related', path, raw, severity='error')
                    if field == 'sources':
                        if status == 'missing' and not matches and '/' not in raw and not pathlib.PurePosixPath(raw).suffix:
                            status = 'unstructured'
                        source_rows.append(dict(file=path, reference=raw, status=status, targets=hits))
                        if status in ('missing', 'ambiguous') and not matches:
                            issue('source_' + status, path, raw, severity='error', candidates=hits)
                        elif status == 'unstructured':
                            issue('source_unstructured', path, raw)
    wiki = sorted(p for p in docs if p.startswith('知识库/wiki/'))
    inbound = collections.Counter(dst for src, dst in set(wiki_links) if src in wiki and dst in wiki and src != dst)
    orphan = [p for p in wiki if not inbound[p]]
    entry = '知识库/README.md' if '知识库/README.md' in docs else 'README.md'
    reachable, pending = set(), [entry]
    while pending:
        p = pending.pop()
        if p not in reachable:
            reachable.add(p)
            pending.extend(graph[p] - reachable)
    unreachable = sorted(set(wiki) - reachable)
    titles = collections.defaultdict(list)
    hashes = collections.defaultdict(list)
    for path in wiki:
        title = metadata[path].get('title')
        if isinstance(title, str):
            titles[re.sub(r'\s+', ' ', title).strip().casefold()].append(path)
        body = re.sub(r'\s+', ' ', docs[path].split('---', 2)[-1]).strip()
        hashes[hashlib.sha256(body.encode()).hexdigest()].append(path)
    duplicate_titles = [v for v in titles.values() if len(v) > 1]
    duplicate_bodies = [v for v in hashes.values() if len(v) > 1]
    for group in duplicate_titles:
        issue('duplicate_title_review', group[0], 'Same title is a review signal, not proof that content should merge', candidates=group)
    entity_summary = {}
    entities_path = root / '知识库/wiki/.entities.json'
    if entities_path.exists():
        e = json.loads(entities_path.read_text(encoding='utf-8'))
        entities = e.get('entities', [])
        ids = collections.Counter(v['id'] for v in entities)
        for key, n in ids.items():
            if n > 1:
                issue('duplicate_entity_id', '知识库/wiki/.entities.json', key, severity='error')
        dangling = [(v['id'], r['to']) for v in entities for r in v.get('relationships', []) if r.get('to') not in ids]
        for src, dst in dangling:
            issue('missing_entity_target', '知识库/wiki/.entities.json', src + ' -> ' + dst, severity='error')
        entity_files = set()
        for v in entities:
            f = v.get('attributes', {}).get('file')
            if f:
                status, hits = resolver.resolve('知识库/wiki/.entities.json', f)
                if status != 'resolved':
                    issue('entity_file_' + status, '知识库/wiki/.entities.json', f, severity='error', candidates=hits)
                else:
                    entity_files.update(hits)
        entity_summary = dict(count=len(entities), relationships=sum(len(v.get('relationships', [])) for v in entities),
                              types=dict(collections.Counter(v.get('type') for v in entities)),
                              relationship_types=dict(collections.Counter(r.get('type') for v in entities for r in v.get('relationships', []))),
                              wiki_files_without_entity=sorted(set(wiki) - entity_files), dangling_targets=len(dangling))
    source_stats = collections.Counter(r['status'] for r in source_rows)
    paper_dirs = collections.defaultdict(list)
    for p in paths:
        if p.startswith('知识库/sources/papers/') and len(p.split('/')) >= 5:
            paper_dirs[p.split('/')[3]].append(p)
    source_availability = {name: {'pdfs': sorted(p for p in members if p.lower().endswith('.pdf')), 'markdown': sorted(p for p in members if p.endswith('.md'))} for name, members in sorted(paper_dirs.items())}
    return dict(scope=dict(root=str(root), inventory_used=bool(inventory), inventory_blob_count=len(tree_blobs),
                           known_file_count=len(paths), markdown_content_checked=len(docs), inventory_only_markdown=len([p for p in paths if p.endswith('.md') and p not in docs]),
                           limitations=['No external URL fetches', 'Inventory assumes absent local paths are unmaterialized, not deletions', 'No heading/block anchor validation', 'No PDF identity, licensing or semantic fact verification', 'No diagram parsing/rendering', 'Conservative top-level scalar/list frontmatter reader; not full YAML']),
                counts=dict(counts), issues=issues, issue_counts=dict(collections.Counter(i['code'] for i in issues)),
                wiki=dict(pages=len(wiki), types=dict(collections.Counter(metadata[p].get('type', '<missing>') for p in wiki)),
                          statuses=dict(collections.Counter(metadata[p].get('status', '<missing>') for p in wiki)),
                          frontmatter_field_coverage={f: sum(f in metadata[p] for p in wiki) for f in ('sources', 'confidence', 'source_checked', 'related', 'updated')},
                          readme_entry=entry, readme_unreachable=unreachable, zero_wiki_inbound=orphan,
                          duplicate_titles=duplicate_titles, identical_normalized_bodies=duplicate_bodies),
                sources=dict(reference_status_counts=dict(source_stats), references=source_rows, paper_directories=source_availability), entities=entity_summary)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', nargs='?', default='.')
    p.add_argument('--inventory', help='Complete GitHub recursive tree JSON, to check absent local files by path only')
    p.add_argument('--format', choices=['text', 'json'], default='text')
    args = p.parse_args()
    result = audit(args.root, args.inventory)
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('Read-only structural audit')
        print(json.dumps(result['scope'], ensure_ascii=False, indent=2))
        print('Link occurrences:', json.dumps(result['counts'], ensure_ascii=False))
        print('Issues:', json.dumps(result['issue_counts'], ensure_ascii=False))
        for item in result['issues']:
            print('{severity}: {file}:{line}: {code}: {detail}'.format(line=item.get('line', ''), **{k:v for k,v in item.items() if k != 'line'}))
        print('Wiki graph:', json.dumps(result['wiki'], ensure_ascii=False, indent=2))
    return 1 if any(i['severity'] == 'error' for i in result['issues']) else 0


if __name__ == '__main__':
    sys.exit(main())
