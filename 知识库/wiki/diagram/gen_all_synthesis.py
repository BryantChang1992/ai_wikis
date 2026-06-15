#!/usr/bin/env python3
"""Batch generate synthesis architecture diagrams in fireworks-tech-graph Style 1"""
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

STYLE1_PREFIX = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <style>
    text {{ font-family: 'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', 'Microsoft JhengHei', 'SimHei', sans-serif; }}
  </style>
  <defs>
{arrows_defs}
  </defs>
  <rect width="{w}" height="{h}" fill="#ffffff"/>
'''

STYLE1_ARROW_COLORS = {
    'blue': '#2563eb',
    'green': '#16a34a',
    'red': '#dc2626',
    'purple': '#9333ea',
    'orange': '#f97316',
    'gray': '#6b7280',
}

STYLE1_TINT_BG = {
    'blue': '#eff6ff',
    'green': '#f0fdf4',
    'red': '#fef2f2',
    'purple': '#faf5ff',
    'orange': '#fff7ed',
    'teal': '#f0fdfa',
}

STYLE1_TINT_STROKE = {
    'blue': '#bfdbfe',
    'green': '#bbf7d0',
    'red': '#fecaca',
    'purple': '#ddd6fe',
    'orange': '#fed7aa',
    'teal': '#ccfbf1',
}

def make_arrow_defs(colors_needed):
    """Generate <marker> defs for needed colors"""
    lines = []
    for c in colors_needed:
        color = STYLE1_ARROW_COLORS[c]
        lines.append(f'    <marker id="arrow-{c}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">')
        lines.append(f'      <polygon points="0 0, 10 3.5, 0 7" fill="{color}"/>')
        lines.append(f'    </marker>')
    return '\n'.join(lines)

def tinted_box(x, y, w, h, color):
    """Return SVG lines for a tinted background box"""
    return [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{STYLE1_TINT_BG[color]}" stroke="{STYLE1_TINT_STROKE[color]}" stroke-width="1.5"/>'
    ]

def white_box(x, y, w, h):
    return [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#d1d5db" stroke-width="1.5"/>'
    ]

def label(x, y, text, size=13, color='#111827', weight='600', anchor='middle'):
    return f'  <text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{text}</text>'

def sublabel(x, y, text, size=11, anchor='middle'):
    return f'  <text x="{x}" y="{y}" fill="#6b7280" font-size="{size}" text-anchor="{anchor}">{text}</text>'

def arrow(x1, y1, x2, y2, color='blue'):
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{STYLE1_ARROW_COLORS[color]}" stroke-width="1.5" marker-end="url(#arrow-{color})"/>'

def section_label(x, y, text, color='blue'):
    c = STYLE1_ARROW_COLORS[color]
    return f'  <text x="{x}" y="{y}" fill="{c}" font-size="12" font-weight="700">{text}</text>'

def write_svg(filename, w, h, arrows_defs, body_lines):
    out = os.path.join(OUTPUT_DIR, filename)
    prefix = STYLE1_PREFIX.format(w=w, h=h, arrows_defs=arrows_defs)
    content = prefix + '\n'.join(body_lines) + '\n</svg>\n'
    with open(out, 'w') as f:
        f.write(content)
    return out


# =============================================================================
# 1. Doris OLAP Architecture
# =============================================================================
def gen_doris():
    w, h = 900, 540
    colors = ['blue', 'green', 'purple', 'orange']
    lines = []

    # Title
    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Apache Doris — MPP OLAP Architecture</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">Real-time analytical database with F2E separation, MoW model, and vectorized execution</text>')

    # Layer 1: Data Ingestion
    lines.append(section_label(30, 78, '01 // DATA INGESTION', 'blue'))
    # boxes: Stream Load, Routine Load, Broker Load, MySQL Load, Canal/Sync
    ingests = [
        ('Stream Load', 'HTTP push', 'blue'),
        ('Routine Load', 'Kafka', 'blue'),
        ('Broker Load', 'HDFS/S3', 'blue'),
        ('Binlog Sync', 'Canal/CDC', 'blue'),
    ]
    for i, (name, desc, c) in enumerate(ingests):
        x = 30 + i * 215
        y = 92
        lines += tinted_box(x, y, 195, 48, c)
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))
        if i < 3:
            lines.append(arrow(x + 195, y + 24, x + 215, y + 24, 'blue'))

    # Arrow down
    lines.append(arrow(450, 140, 450, 168, 'blue'))

    # Layer 2: FE (Frontend)
    lines.append(section_label(30, 188, '02 // FRONTEND (Java FE)', 'green'))
    fe_boxes = [
        ('Query Planner', 'Nereids/CBO/MPP', 'green'),
        ('Catalog Mgr', 'metadata', 'green'),
        ('Coordinator', 'RPC dispatch', 'green'),
        ('Load Mgr', 'txn/progress', 'green'),
    ]
    for i, (name, desc, c) in enumerate(fe_boxes):
        x = 30 + i * 215
        y = 202
        lines += tinted_box(x, y, 195, 48, c)
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Arrow down
    lines.append(arrow(450, 250, 450, 278, 'purple'))

    # Layer 3: BE (Backend) + Storage
    lines.append(section_label(30, 298, '03 // BACKEND + STORAGE (C++ BE)', 'purple'))
    be_boxes = [
        ('Segment v2', 'col. storage', 'purple'),
        ('Compaction', 'CU/MoW merge', 'purple'),
        ('Vectorized Exec', 'SIMD/pipeline', 'purple'),
        ('Primary Key Idx', 'MoW upsert', 'purple'),
    ]
    for i, (name, desc, c) in enumerate(be_boxes):
        x = 30 + i * 215
        y = 312
        lines += tinted_box(x, y, 195, 48, c)
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Arrow down
    lines.append(arrow(450, 360, 450, 388, 'orange'))

    # Layer 4: Optimizations
    lines.append(section_label(30, 408, '04 // KEY OPTIMIZATIONS', 'orange'))
    opts = [
        ('MPP Plan', 'data shuffle'),
        ('CBO/Nereids', 'cost model'),
        ('Pipeline Exec', 'non-blocking'),
        ('Compaction CLI', 'MoW tuning'),
    ]
    for i, (name, desc) in enumerate(opts):
        x = 30 + i * 215
        y = 422
        lines += tinted_box(x, y, 195, 44, 'orange')
        lines.append(label(x + 98, y + 18, name, 11))
        lines.append(sublabel(x + 98, y + 34, desc, 9))

    # Legend
    lines.append(f'  <g transform="translate(30, 498)">')
    lines.append(f'    <rect x="0" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG["blue"]}" stroke="{STYLE1_TINT_STROKE["blue"]}" stroke-width="1"/>')
    lines.append(f'    <text x="20" y="12" fill="#6b7280" font-size="10">Ingestion</text>')
    lines.append(f'    <rect x="100" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG["green"]}" stroke="{STYLE1_TINT_STROKE["green"]}" stroke-width="1"/>')
    lines.append(f'    <text x="120" y="12" fill="#6b7280" font-size="10">Frontend</text>')
    lines.append(f'    <rect x="200" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG["purple"]}" stroke="{STYLE1_TINT_STROKE["purple"]}" stroke-width="1"/>')
    lines.append(f'    <text x="220" y="12" fill="#6b7280" font-size="10">Backend + Storage</text>')
    lines.append(f'    <rect x="340" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG["orange"]}" stroke="{STYLE1_TINT_STROKE["orange"]}" stroke-width="1"/>')
    lines.append(f'    <text x="360" y="12" fill="#6b7280" font-size="10">Optimizations</text>')
    lines.append(f'  </g>')

    return write_svg('doris-architecture.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 2. Fluss Architecture
# =============================================================================
def gen_fluss():
    w, h = 900, 520
    colors = ['blue', 'green', 'purple', 'orange']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Fluss — Next-Gen Streaming Platform</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">Kafka-compatible protocol + rebuilt storage kernel with Arrow/Parquet lakehouse layer</text>')

    # Layer 1: Client / Protocol
    lines.append(section_label(30, 80, '01 // CLIENT & PROTOCOL', 'blue'))
    clients = ['Kafka Client', 'Flink Connector', 'Flink SQL', 'REST Proxy']
    for i, name in enumerate(clients):
        x = 80 + i * 200
        y = 94
        lines += tinted_box(x, y, 172, 40, 'blue')
        lines.append(label(x + 86, y + 26, name, 12))

    lines.append(arrow(450, 134, 450, 158, 'blue'))

    # Layer 2: Coordinator
    lines.append(section_label(30, 178, '02 // COORDINATOR', 'green'))
    coord_parts = ['Metadata Mgr', 'ISR Controller', 'Leader Election', 'Topic Admin']
    for i, name in enumerate(coord_parts):
        x = 80 + i * 200
        y = 192
        lines += tinted_box(x, y, 172, 40, 'green')
        lines.append(label(x + 86, y + 26, name, 12))

    lines.append(arrow(450, 232, 450, 258, 'purple'))

    # Layer 3: Storage Kernel
    lines.append(section_label(30, 278, '03 // STORAGE KERNEL', 'purple'))
    store_parts = [
        ('LogSegment', 'KV dispatcher'),
        ('Arrow Format', 'columnar batch'),
        ('RocksDB Local', 'key lookup'),
        ('TieredStorage', 'S3/OSS'),
    ]
    for i, (name, desc) in enumerate(store_parts):
        x = 30 + i * 215
        y = 292
        lines += tinted_box(x, y, 195, 48, 'purple')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    lines.append(arrow(450, 340, 450, 368, 'orange'))

    # Layer 4: Lakehouse + Observability
    lines.append(section_label(30, 388, '04 // LAKEHOUSE & OBSERVABILITY', 'orange'))
    lake_parts = [
        ('Parquet Lake', 'data export'),
        ('Iceberg', 'table format'),
        ('Metrics', 'Prometheus'),
        ('Coordinator HA', 'ZooKeeper'),
    ]
    for i, (name, desc) in enumerate(lake_parts):
        x = 30 + i * 215
        y = 402
        lines += tinted_box(x, y, 195, 48, 'orange')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Legend
    lines.append(f'  <g transform="translate(30, 478)">')
    for i, (label_text, col) in enumerate([('Client', 'blue'), ('Coordinator', 'green'), ('Storage', 'purple'), ('Lakehouse', 'orange')]):
        lines.append(f'    <rect x="{i*100}" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG[col]}" stroke="{STYLE1_TINT_STROKE[col]}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*100+20}" y="12" fill="#6b7280" font-size="10">{label_text}</text>')
    lines.append(f'  </g>')

    return write_svg('fluss-architecture.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 3. InfluxDB Architecture
# =============================================================================
def gen_influxdb():
    w, h = 880, 520
    colors = ['blue', 'green', 'purple']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">InfluxDB Architecture Evolution — v1→v2→v3.0</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">From self-built TSM engine (v1/v2) to columnar cloud-native Parquet/Arrow/DataFusion (v3.0)</text>')

    # Row: v1/v2 vs v3
    # Left column: v1/v2
    lines.append(section_label(30, 80, 'v1 / v2 — Self-built Engine', 'blue'))
    v12 = [('Line Protocol', 'write API'), ('WAL', 'durability'), ('TSM Engine', 'col. compr.'), ('TSI Index', 'tag lookup'), ('Shard/Retention', 'TTL policy')]
    for i, (name, desc) in enumerate(v12):
        y = 94 + i * 58
        lines += tinted_box(30, y, 380, 48, 'blue')
        lines.append(label(220, y + 20, name, 12))
        lines.append(sublabel(220, y + 36, desc, 10))

    # Right column: v3.0
    lines.append(section_label(470, 80, 'v3.0 — Cloud-Native', 'green'))
    v3 = [('Parquet Writer', 'open format'), ('Arrow Flight', 'columnar I/O'), ('DataFusion', 'query engine'), ('Catalog/Iceberg', 'table mgmt'), ('Compactor', 'merge-on-read')]
    for i, (name, desc) in enumerate(v3):
        y = 94 + i * 58
        lines += tinted_box(470, y, 380, 48, 'green')
        lines.append(label(660, y + 20, name, 12))
        lines.append(sublabel(660, y + 36, desc, 10))

    # Transition arrow
    lines.append(arrow(420, 260, 460, 260, 'purple'))
    lines.append(f'  <text x="440" y="252" fill="{STYLE1_ARROW_COLORS["purple"]}" font-size="9" text-anchor="middle">arch</text>')
    lines.append(f'  <text x="440" y="274" fill="{STYLE1_ARROW_COLORS["purple"]}" font-size="9" text-anchor="middle">shift</text>')

    # Bottom: Common Cloud Layer
    lines.append(section_label(30, 410, 'Shared Infrastructure — Object Storage + Ingester + Query Router', 'purple'))
    infra = [('Ingester', 'write fan-in'), ('Object Store', 'S3/compat'), ('Querier', 'query fan-out'), ('Router', 'load balance')]
    for i, (name, desc) in enumerate(infra):
        x = 30 + i * 215
        y = 424
        lines += tinted_box(x, y, 195, 48, 'purple')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Legend
    lines.append(f'  <g transform="translate(30, 496)">')
    colors_info = [('v1/v2 TSM', 'blue'), ('v3.0 Cloud', 'green'), ('Shared', 'purple')]
    for i, (label_txt, col) in enumerate(colors_info):
        lines.append(f'    <rect x="{i*150}" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG[col]}" stroke="{STYLE1_TINT_STROKE[col]}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*150+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('influxdb-architecture.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 4. LSM-Tree New Progress (2026)
# =============================================================================
def gen_lsm_new():
    w, h = 860, 520
    colors = ['blue', 'green', 'purple', 'red', 'orange']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">LSM-Tree 2026 New Progress — Silo + Fluss + 10 Wiki Cards</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">From single-node LSM to distributed compaction scheduling (Silo) + streaming storage (Fluss RocksDB)</text>')

    # Top: Classic LSM (single-node)
    lines.append(section_label(30, 80, '01 // CLASSIC LSM (Single-Node)', 'blue'))
    classic = ['Write→WAL', 'MemTable', 'L0→L1...LK', 'Compaction', 'Bloom Filter']
    for i, name in enumerate(classic):
        x = 30 + i * 165
        y = 94
        lines += tinted_box(x, y, 148, 40, 'blue')
        lines.append(label(x + 74, y + 26, name, 11))

    # Arrow to middle
    lines.append(f'  <line x1="430" y1="134" x2="430" y2="168" stroke="{STYLE1_ARROW_COLORS["purple"]}" stroke-width="1.5" marker-end="url(#arrow-purple)"/>')
    lines.append(f'  <text x="440" y="158" fill="{STYLE1_ARROW_COLORS["purple"]}" font-size="9">extend to distributed</text>')

    # Middle: Two threads
    lines.append(section_label(30, 188, '02 // DISTRIBUTED EXTENSIONS', 'purple'))

    # Thread A: Silo
    lines.append(section_label(30, 212, 'Silo (FAST 2026) — Global Compaction Scheduler', 'red'))
    silo_parts = [('Central Planner', 'global view'), ('SST Migration', 'offload write'), ('Lease-based', 'fault-tolerant'), ('Write Amp ↓30%', 'benchmark')]
    for i, (name, desc) in enumerate(silo_parts):
        x = 30 + i * 210
        y = 226
        lines += tinted_box(x, y, 190, 48, 'red')
        lines.append(label(x + 95, y + 20, name, 11))
        lines.append(sublabel(x + 95, y + 36, desc, 9))

    # Thread B: Fluss RocksDB
    lines.append(section_label(30, 296, 'Fluss (Apache) — Streaming Storage with RocksDB', 'orange'))
    fluss_parts = [('LogSegment', 'KV dispatcher'), ('RocksDB WAL', 'durability'), ('Tiered Compact', 'L0→S3'), ('Arrow Batch', 'col. read')]
    for i, (name, desc) in enumerate(fluss_parts):
        x = 30 + i * 210
        y = 310
        lines += tinted_box(x, y, 190, 48, 'orange')
        lines.append(label(x + 95, y + 20, name, 11))
        lines.append(sublabel(x + 95, y + 36, desc, 9))

    # Bottom: 10 Wiki Cards summary
    lines.append(section_label(30, 386, '03 // WIKI CARD COVERAGE — 10 cards', 'green'))
    cards = ['LSM-Tree', 'Compaction', 'RUM Conjecture', 'Write Amp', 'Auto-Tune', 'Silo', 'Fluss WAL', 'RocksDB', 'Index', 'HW Adapt']
    for i, name in enumerate(cards):
        row = i // 5
        col = i % 5
        x = 30 + col * 166
        y = 400 + row * 42
        lines += white_box(x, y, 152, 34)
        lines.append(label(x + 76, y + 22, name, 10, '#374151', '500'))

    # Legend
    lines.append(f'  <g transform="translate(30, 492)">')
    color_list = [('Classic LSM', 'blue'), ('Silo', 'red'), ('Fluss', 'orange'), ('Wiki Cards', 'green')]
    for i, (label_txt, col) in enumerate(color_list):
        lines.append(f'    <rect x="{i*140}" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG[col]}" stroke="{STYLE1_TINT_STROKE[col]}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*140+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('lsm-tree-2026-progress.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 5. OLAP vs TSDB Panorama
# =============================================================================
def gen_olap_tsdb():
    w, h = 880, 500
    colors = ['blue', 'green', 'purple', 'orange']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">OLAP vs. Time-Series Database — Domain Comparison</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">Doris (OLAP) vs. InfluxDB (TSDB) — different design paradigms, shared columnar trends</text>')

    # Two-column layout
    # OLAP Column
    lines.append(section_label(30, 82, 'OLAP — MPP Importer-Query Model', 'blue'))
    olap_rows = [
        ('Semantic Model', 'star/snowflake schema'),
        ('Data Model', 'Aggregate/Unique/Duplicate'),
        ('Query Engine', 'MPP + vectorized + CBO'),
        ('Storage', 'Segment v2 columnar'),
        ('Write Model', 'batch append + MoW update'),
        ('Use Case', 'multi-dim ad-hoc analysis'),
    ]
    for i, (name, desc) in enumerate(olap_rows):
        y = 96 + i * 48
        lines += tinted_box(30, y, 380, 40, 'blue')
        lines.append(label(220, y + 18, name, 11))
        lines.append(sublabel(220, y + 32, desc, 9))

    # TSDB Column
    lines.append(section_label(470, 82, 'TSDB — Time-Ordered Query Model', 'green'))
    tsdb_rows = [
        ('Data Model', 'measurement + tags'),
        ('Write Model', 'time-ordered append'),
        ('Query Engine', 'DataFusion pushdown'),
        ('Storage', 'TSM → Parquet col.'),
        ('Compression', 'timestamp delta + Gorilla'),
        ('Use Case', 'metrics / monitoring'),
    ]
    for i, (name, desc) in enumerate(tsdb_rows):
        y = 96 + i * 48
        lines += tinted_box(470, y, 380, 40, 'green')
        lines.append(label(660, y + 18, name, 11))
        lines.append(sublabel(660, y + 32, desc, 9))

    # Horizontal comparison arrows
    for i in range(6):
        y = 116 + i * 48
        lines.append(f'  <line x1="415" y1="{y}" x2="462" y2="{y}" stroke="#9333ea" stroke-width="1" stroke-dasharray="4,3"/>')

    # Bottom: Convergence
    lines.append(section_label(30, 410, 'Convergence Trend → Both moving toward columnar + cloud-native', 'purple'))
    conv = [('Columnar Storage', 'Arrow/Parquet'), ('Query Federation', 'Unified SQL'), ('S3/Tiered Store', '∞ scale'), ('Real-Time', 'stream/materialize')]
    for i, (name, desc) in enumerate(conv):
        x = 30 + i * 215
        y = 424
        lines += tinted_box(x, y, 195, 40, 'purple')
        lines.append(label(x + 98, y + 18, name, 11))
        lines.append(sublabel(x + 98, y + 32, desc, 9))

    # Legend
    lines.append(f'  <g transform="translate(30, 484)">')
    color_list = [('OLAP (Doris)', 'blue'), ('TSDB (InfluxDB)', 'green'), ('Convergence', 'purple')]
    for i, (label_txt, col) in enumerate(color_list):
        lines.append(f'    <rect x="{i*170}" y="0" width="14" height="14" rx="3" fill="{STYLE1_TINT_BG[col]}" stroke="{STYLE1_TINT_STROKE[col]}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*170+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('olap-tsdb-comparison.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 6. Distributed Consistency System
# =============================================================================
def gen_consistency():
    w, h = 880, 530
    colors = ['blue', 'green', 'purple', 'orange', 'red']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Distributed Data Systems — Consistency Landscape</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">Three pillars: Transaction Models · Event Horizon · Storage-Compute Separation</text>')

    # Pillar 1: Transaction
    lines.append(section_label(30, 82, '01 // TRANSACTION MODELS', 'blue'))
    txn = [('ACID', '2PC/Paxos'), ('Snapshot Iso.', 'MVCC/Truetime'), ('Serializable', 'Calvin/OCC'), ('Read Committed', 'lock-based')]
    for i, (name, desc) in enumerate(txn):
        x = 30 + i * 215
        y = 96
        lines += tinted_box(x, y, 195, 48, 'blue')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Pillar 2: Event Horizon
    lines.append(section_label(30, 174, '02 // EVENT HORIZON — Asymmetric Dependencies', 'green'))
    eh_parts = [('Causal Order', 'Lamport clock'), ('Global Barriers', 'Flink watermark'), ('Write-Skew', 'serializable check'), ('Prior/After', 'event graph')]
    for i, (name, desc) in enumerate(eh_parts):
        x = 30 + i * 215
        y = 188
        lines += tinted_box(x, y, 195, 48, 'green')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Pillar 3: Storage-Compute Split
    lines.append(section_label(30, 266, '03 // STORAGE-COMPUTE SEPARATION', 'purple'))
    sc_parts = [('Shared-Disk', 'Aurora/Neon'), ('Shared-Nothing', 'FoundationDB'), ('Disagg Mem', 'RDMA pool'), ('Object Store', 'S3 primary')]
    for i, (name, desc) in enumerate(sc_parts):
        x = 30 + i * 215
        y = 280
        lines += tinted_box(x, y, 195, 48, 'purple')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Cross-cutting: Consensus & Clock
    lines.append(section_label(30, 358, '04 // CROSS-CUTTING: Consensus + Clocks', 'orange'))
    cc_parts = [('Raft', 'leader replication'), ('Paxos', 'majority quorum'), ('TrueTime', 'Google Spanner'), ('Hybrid LC', 'HLC/HLClock')]
    for i, (name, desc) in enumerate(cc_parts):
        x = 30 + i * 215
        y = 372
        lines += tinted_box(x, y, 195, 48, 'orange')
        lines.append(label(x + 98, y + 20, name, 12))
        lines.append(sublabel(x + 98, y + 36, desc, 10))

    # Systems at bottom
    lines.append(section_label(30, 450, '05 // REPRESENTATIVE SYSTEMS', 'red'))
    systems = ['Spanner', 'CockroachDB', 'TiDB', 'FoundationDB', 'Aurora', 'Neon', 'YugabyteDB']
    for i, name in enumerate(systems):
        x = 30 + i * 118
        y = 464
        lines += white_box(x, y, 104, 30)
        lines.append(label(x + 52, y + 20, name, 10, '#374151', '500'))

    # Legend
    lines.append(f'  <g transform="translate(30, 512)">')
    color_list = [('Txn Models', 'blue'), ('Event Horizon', 'green'), ('S-C Split', 'purple'), ('Consensus', 'orange'), ('Systems', 'gray')]
    for i, (label_txt, col) in enumerate(color_list):
        bg = STYLE1_TINT_BG.get(col, '#f9fafb')
        st = STYLE1_TINT_STROKE.get(col, '#d1d5db')
        lines.append(f'    <rect x="{i*140}" y="0" width="14" height="14" rx="3" fill="{bg}" stroke="{st}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*140+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('consistency-landscape.svg', w, h, make_arrow_defs(list(colors)+['gray']), lines)


# =============================================================================
# 7. Distributed Tx & Consistency New Progress (2026)
# =============================================================================
def gen_tx_consistency_2026():
    w, h = 880, 520
    colors = ['blue', 'green', 'purple', 'red']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Distributed Tx & Consistency — 2026 New Progress</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">SIGMOD/CIDR/FAST 2026 papers: CockroachDB · Aurora · Rosé · Agent-First</text>')

    # CockroachDB
    lines.append(section_label(30, 82, 'CockroachDB — Leader Lease & Global Txn', 'blue'))
    lines += tinted_box(30, 96, 820, 64, 'blue')
    lines.append(f'  <text x="50" y="118" fill="#111827" font-size="12" font-weight="600">Parallel Commit · Uncertainty Interval · Range Lease · Query Liveness</text>')
    lines.append(f'  <text x="50" y="136" fill="#6b7280" font-size="10">Clock-bound waits + read-your-writes consistency without global clock</text>')

    # Aurora
    lines.append(section_label(30, 188, 'Amazon Aurora — Shuffle Sharding & DPTM', 'green'))
    lines += tinted_box(30, 202, 820, 64, 'green')
    lines.append(f'  <text x="50" y="224" fill="#111827" font-size="12" font-weight="600">Distributed Transaction Manager · Shuffle Sharding for fault isolation · Storage quorum</text>')
    lines.append(f'  <text x="50" y="242" fill="#6b7280" font-size="10">Shared-disk architecture with logical replication, avoiding two-phase commit overhead</text>')

    # Rosé
    lines.append(section_label(30, 294, 'Rosé — Optimistic Reads with Watermarks', 'purple'))
    lines += tinted_box(30, 308, 820, 64, 'purple')
    lines.append(f'  <text x="50" y="330" fill="#111827" font-size="12" font-weight="600">Single-writer + multi-reader optimistic · Watermark-based read visibility · Version chain</text>')
    lines.append(f'  <text x="50" y="348" fill="#6b7280" font-size="10">Separates read and write paths; readers never block, writers use watermarks for safe reads</text>')

    # Agent-First
    lines.append(section_label(30, 400, 'Agent-First Design — Consistency for AI Workloads', 'red'))
    lines += tinted_box(30, 414, 820, 64, 'red')
    lines.append(f'  <text x="50" y="436" fill="#111827" font-size="12" font-weight="600">Agent-first consistency — eventual with bounded staleness · Causal delivery for agent chains</text>')
    lines.append(f'  <text x="50" y="454" fill="#6b7280" font-size="10">Prioritizes availability + low latency over strict serializability; session guarantees for agents</text>')

    # Legend
    lines.append(f'  <g transform="translate(30, 498)">')
    color_list = [('CockroachDB', 'blue'), ('Aurora', 'green'), ('Rosé', 'purple'), ('Agent-First', 'red')]
    for i, (label_txt, col) in enumerate(color_list):
        bg = STYLE1_TINT_BG[col]
        st = STYLE1_TINT_STROKE[col]
        lines.append(f'    <rect x="{i*170}" y="0" width="14" height="14" rx="3" fill="{bg}" stroke="{st}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*170+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('tx-consistency-2026-progress.svg', w, h, make_arrow_defs(colors), lines)


# =============================================================================
# 8. Stream Processing Evolution
# =============================================================================
def gen_stream_evolution():
    w, h = 880, 480
    colors = ['blue', 'green', 'purple', 'orange']
    lines = []

    lines.append(f'  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Stream Processing Evolution — 1992→2022 (3 Generations)</text>')
    lines.append(f'  <text x="30" y="50" fill="#6b7280" font-size="11">DSMS → Dataflow → Event-Driven Microservices — based on Fragkoulis et al. Survey</text>')

    # Gen 1: DSMS
    lines.append(section_label(30, 82, 'GEN 1: DSMS (2000–2010) — "Database Inverted"', 'blue'))
    g1 = [('STREAM', 'Stanford CQL'), ('Aurora/Borealis', 'MIT/Brown'), ('TelegraphCQ', 'Berkeley'), ('System S', 'IBM streams')]
    for i, (name, desc) in enumerate(g1):
        x = 30 + i * 215
        y = 96
        lines += tinted_box(x, y, 195, 40, 'blue')
        lines.append(label(x + 98, y + 18, name, 11))
        lines.append(sublabel(x + 98, y + 32, desc, 9))

    lines.append(arrow(450, 136, 450, 158, 'green'))

    # Gen 2: Dataflow
    lines.append(section_label(30, 178, 'GEN 2: Dataflow (2011–2022) — Distributed Processing', 'green'))
    g2 = [('Storm', 'record-at-a-time'), ('Flink', 'checkpoint/barrier'), ('Spark Str.', 'micro-batch'), ('Kafka Str.', 'topic-table')]
    for i, (name, desc) in enumerate(g2):
        x = 30 + i * 215
        y = 192
        lines += tinted_box(x, y, 195, 40, 'green')
        lines.append(label(x + 98, y + 18, name, 11))
        lines.append(sublabel(x + 98, y + 32, desc, 9))

    lines.append(arrow(450, 232, 450, 258, 'purple'))

    # Gen 3: Emerging
    lines.append(section_label(30, 278, 'GEN 3: Emerging (2022–) — Event-Driven + Microservices', 'purple'))
    g3 = [('Serverless', 'auto-scale'), ('Streaming DB', 'RisingWave/Materialize'), ('Data Mesh', 'domain ownership'), ('Agent Stream', 'AI-driven')]
    for i, (name, desc) in enumerate(g3):
        x = 30 + i * 215
        y = 292
        lines += tinted_box(x, y, 195, 40, 'purple')
        lines.append(label(x + 98, y + 18, name, 11))
        lines.append(sublabel(x + 98, y + 32, desc, 9))

    # Cross-cutting concerns
    lines.append(section_label(30, 360, 'CROSS-CUTTING CONCERNS', 'orange'))
    cc = [('Out-of-Order', 'watermarks'), ('State Mgmt', 'RocksDB back'), ('Fault Tolerance', 'checkpoint'), ('Elasticity', 'reconfig'), ('Dataflow Model', 'Beam')]
    for i, (name, desc) in enumerate(cc):
        x = 30 + i * 170
        y = 374
        lines += white_box(x, y, 155, 36)
        lines.append(label(x + 78, y + 14, name, 10, '#374151', '600'))
        lines.append(sublabel(x + 78, y + 28, desc, 8))

    # Legend
    lines.append(f'  <g transform="translate(30, 440)">')
    color_list = [('Gen1 DSMS', 'blue'), ('Gen2 Dataflow', 'green'), ('Gen3 Emerging', 'purple'), ('Concerns', 'gray')]
    for i, (label_txt, col) in enumerate(color_list):
        bg = STYLE1_TINT_BG.get(col, '#f9fafb')
        st = STYLE1_TINT_STROKE.get(col, '#d1d5db')
        lines.append(f'    <rect x="{i*160}" y="0" width="14" height="14" rx="3" fill="{bg}" stroke="{st}" stroke-width="1"/>')
        lines.append(f'    <text x="{i*160+20}" y="12" fill="#6b7280" font-size="10">{label_txt}</text>')
    lines.append(f'  </g>')

    return write_svg('stream-processing-evolution.svg', w, h, make_arrow_defs(['blue','green','purple','gray']), lines)


# =============================================================================
# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    diagrams = [
        gen_doris(),
        gen_fluss(),
        gen_influxdb(),
        gen_lsm_new(),
        gen_olap_tsdb(),
        gen_consistency(),
        gen_tx_consistency_2026(),
        gen_stream_evolution(),
    ]
    print("Generated SVGs:")
    for d in diagrams:
        print(f"  {d}")
    print(f"Done. {len(diagrams)} diagrams.")
