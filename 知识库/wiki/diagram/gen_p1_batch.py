#!/usr/bin/env python3
"""P1 concept card diagrams — fireworks-tech-graph Style 1"""
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
AC = {'blue':'#2563eb','green':'#16a34a','red':'#dc2626','purple':'#9333ea','orange':'#f97316','gray':'#6b7280'}
TG = {'blue':'#eff6ff','green':'#f0fdf4','red':'#fef2f2','purple':'#faf5ff','orange':'#fff7ed','teal':'#f0fdfa','gray':'#f9fafb'}
TS = {'blue':'#bfdbfe','green':'#bbf7d0','red':'#fecaca','purple':'#ddd6fe','orange':'#fed7aa','teal':'#ccfbf1','gray':'#e5e7eb'}

def make_svg(w, h, arrows, lines, fn):
    ads = ''.join(f'    <marker id="a-{c}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">\n      <polygon points="0 0, 10 3.5, 0 7" fill="{AC[c]}"/>\n    </marker>\n' for c in arrows)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n  <style>\n    text {{ font-family: "Helvetica Neue",Helvetica,Arial,"PingFang SC","Microsoft YaHei","Microsoft JhengHei","SimHei",sans-serif; }}\n  </style>\n  <defs>\n{ads}  </defs>\n  <rect width="{w}" height="{h}" fill="#ffffff"/>\n'
    svg += '\n'.join(lines) + '\n</svg>\n'
    with open(os.path.join(OUTPUT_DIR, fn), 'w') as f: f.write(svg)
    return os.path.join(OUTPUT_DIR, fn)

def tb(x,y,w,h,c): return [f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{TG[c]}" stroke="{TS[c]}" stroke-width="1.5"/>']
def wb(x,y,w,h): return [f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#d1d5db" stroke-width="1.5"/>']
def lb(x,y,t,sz=13,c='#111827',w='600',a='middle'): return f'  <text x="{x}" y="{y}" fill="{c}" font-size="{sz}" font-weight="{w}" text-anchor="{a}">{t}</text>'
def sb(x,y,t,sz=11,a='middle'): return f'  <text x="{x}" y="{y}" fill="#6b7280" font-size="{sz}" text-anchor="{a}">{t}</text>'
def ar(x1,y1,x2,y2,c='blue',d=None):
    ds = f' stroke-dasharray="{d}"' if d else ''
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{AC[c]}" stroke-width="1.5"{ds} marker-end="url(#a-{c})"/>'
def sc(x,y,t,c='blue'): return f'  <text x="{x}" y="{y}" fill="{AC[c]}" font-size="12" font-weight="700">{t}</text>'

# ============ 1. RUM Conjecture ============
def gen_rum():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">LSM-Tree RUM Conjecture</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Read · Update · Memory — optimize two, at the cost of the third</text>')
    # Triangle
    L+=tb(280,90,200,60,'blue'); L.append(lb(380,116,'Read',16)); L.append(sb(380,136,'Bloom Filter · Fence Pointers',10))
    L+=tb(60,350,200,60,'green'); L.append(lb(160,376,'Update (Write)',16)); L.append(sb(160,396,'Batch Write · Sequential',10))
    L+=tb(500,350,200,60,'red'); L.append(lb(600,376,'Memory (Space)',16)); L.append(sb(600,396,'Compression · SST Bloat',10))
    L.append(f'  <line x1="380" y1="150" x2="160" y2="350" stroke="#d1d5db" stroke-width="1.5" stroke-dasharray="6,4"/>')
    L.append(f'  <text x="240" y="260" fill="#6b7280" font-size="10" text-anchor="middle">Bloom Filter tradeoff</text>')
    L.append(f'  <line x1="380" y1="150" x2="600" y2="350" stroke="#d1d5db" stroke-width="1.5" stroke-dasharray="6,4"/>')
    L.append(f'  <text x="530" y="260" fill="#6b7280" font-size="10" text-anchor="middle">Fence Pointer tradeoff</text>')
    L.append(f'  <line x1="160" y1="350" x2="500" y2="350" stroke="#d1d5db" stroke-width="1.5" stroke-dasharray="6,4"/>')
    L.append(f'  <text x="330" y="340" fill="#6b7280" font-size="10" text-anchor="middle">Compression Ratio tradeoff</text>')
    L.append(sc(30,435,'Design Points','purple'))
    for i,(n,d) in enumerate([('RocksDB','read-write'),('LevelDB','read-space'),('Cassandra','write-space'),('WiscKey','KV separation')]):
        x=30+i*185; L+=wb(x,448,165,24); L.append(lb(x+82,463,f'{n}: {d}',10,'#374151','500'))
    return make_svg(760,480,[],L,'rum-conjecture.svg')

# ============ 2. Write Amplification ============
def gen_write_amp():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">LSM-Tree Write Amplification</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Total bytes written to disk / bytes inserted — grows with level depth</text>')
    for i,(n,d,c) in enumerate([('Insert','1 KB','blue'),('WAL','1 KB seq','green'),('MemTable','1 KB mem','purple'),('L0 Flush','1 KB','orange'),('L0→L1','~10 KB','red'),('L1→L2','~10×','red')]):
        x=20+i*132; L+=tb(x,80,118,52,c); L.append(lb(x+59,100,n,10)); L.append(sb(x+59,116,d,9))
        if i<5: L.append(ar(x+118,106,x+132,106,'gray'))
    L.append(sc(30,160,'Amplification Accumulation','red'))
    for i,(n,d,c) in enumerate([('App','1×','blue'),('WAL','1×','green'),('L0 Flush','~1×','orange'),('L0→L1','~10×','red'),('L1→L2','10×/level','red')]):
        x=20+i*165; L+=tb(x,176,148,48,c); L.append(lb(x+74,198,n,10)); L.append(sb(x+74,214,d,9))
        if i<4: L.append(f'  <text x="{x+155}" y="{200}" fill="#ef4444" font-size="14">+</text>')
    L.append(sc(30,258,'Mitigation','green'))
    for i,(n,d) in enumerate([('Tiered Merge','reduce freq'),('Universal','sort-then-merge'),('KV Separation','values in log'),('Zoned NS','HW alignment')]):
        x=30+i*200; L+=tb(x,276,182,48,'green'); L.append(lb(x+91,298,n,11)); L.append(sb(x+91,314,d,9))
    L.append(f'  <g transform="translate(30,360)">')
    for i,(t,c) in enumerate([('Write Path','blue'),('Amplification','red'),('Mitigation','green')]):
        L.append(f'    <rect x="{i*140}" y="0" width="14" height="14" rx="3" fill="{TG[c]}" stroke="{TS[c]}" stroke-width="1"/>')
        L.append(f'    <text x="{i*140+20}" y="12" fill="#6b7280" font-size="10">{t}</text>')
    L.append(f'  </g>')
    return make_svg(820,390,['gray'],L,'lsm-write-amplification.svg')

# ============ 3. Silo ============
def gen_silo():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Silo — Distributed LSM Compaction Scheduler (FAST 2026)</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">From per-node independent compaction to global scheduling with SST migration</text>')
    L.append(sc(30,82,'Problem: Per-Node Compaction','red'))
    for i,(n,d,c) in enumerate([('Node N','hot spot','red'),('Node M','idle','green'),('Node K','light load','green')]):
        x=30+i*250; L+=tb(x,96,220,40,c); L.append(lb(x+110,116,n,12)); L.append(sb(x+110,128,d,9))
    L.append(ar(410,138,410,166,'blue')); L.append(f'  <text x="420" y="160" fill="#2563eb" font-size="9">central scheduling</text>')
    L.append(sc(30,186,'Silo Architecture','blue'))
    itms=[('Global Planner','tracks all LSM trees\npriority scheduling','blue'),('SST Migration','migrate SSTs to\ntarget merge node','blue'),('Anti-Hog','detect hog nodes\nrate-limit compaction','blue'),('Pro-Hog','proactive compact\nwrite-heavy nodes','blue')]
    for i,(n,d,c) in enumerate(itms):
        x=30+i*200; L+=tb(x,204,180,72,c); L.append(lb(x+90,224,n,11))
        for j,dl in enumerate(d.split('\n')): L.append(sb(x+90,244+j*14,dl,8))
    L.append(sc(30,318,'Key Results','green'))
    for i,(n,d) in enumerate([('Write Amp ↓','~30%'),('Throughput ↑','~2× on skew'),('Tail Lat ↓','P99 drop'),('Balance','CPU even')]):
        x=30+i*200; L+=tb(x,336,180,44,'green'); L.append(lb(x+90,358,n,11)); L.append(sb(x+90,372,d,9))
    L.append(sc(30,410,'Integration: Lease-based HA for coordinator failover','purple'))
    L+=tb(30,424,760,32,'purple'); L.append(lb(410,445,'Lease protocol → central coordinator fails over without data loss',10,'#374151','500'))
    return make_svg(820,470,['blue','gray'],L,'silo-compaction-scheduling.svg')

# ============ 4. Log-as-the-Database ============
def gen_log_db():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Log-as-the-Database Pattern</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Immutable append-only log as source of truth, materialized views for reads</text>')
    L.append(sc(30,82,'Traditional DB','red'))
    L.append(sc(430,82,'Log-as-DB','green'))
    for i,(n,d,col) in enumerate([('Write → Pages','random writes','red'),('Buffer Pool','dirty pages','red'),('WAL','crash recovery','red'),('Log → Compaction','merge by key','green'),('Log → MV','materialized view','green'),('MV Query','point read','green')]):
        row=i%3; xo=30 if col=='red' else 430; yc=96+row*52; xc=xo+170
        L+=tb(xo,yc,340,44,col); L.append(lb(xc,yc+20,n,11)); L.append(sb(xc,yc+36,d,9))
    L.append(ar(375,200,422,200,'purple'))
    L.append(sc(30,280,'Systems Using This Pattern','purple'))
    for i,(n,d) in enumerate([('Kafka','event sourcing'),('Flink','changelog'),('Materialize','SQL MV'),('RisingWave','streaming DB'),('Fluss','Arrow Lake')]):
        x=30+i*155; L+=tb(x,298,140,44,'purple'); L.append(lb(x+70,318,n,11)); L.append(sb(x+70,334,d,9))
    L.append(f'  <g transform="translate(30,380)">')
    for i,(t,c) in enumerate([('Traditional','red'),('Log-as-DB','green'),('Systems','purple')]):
        L.append(f'    <rect x="{i*140}" y="0" width="14" height="14" rx="3" fill="{TG[c]}" stroke="{TS[c]}" stroke-width="1"/>')
        L.append(f'    <text x="{i*140+20}" y="12" fill="#6b7280" font-size="10">{t}</text>')
    L.append(f'  </g>')
    return make_svg(800,410,['purple','gray'],L,'log-as-the-database.svg')

# ============ 5. CockroachDB Leader Lease ============
def gen_crdb_lease():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">CockroachDB Leader-Lease Architecture</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Multi-range scalable lease: 10K+ ranges with efficient leader election</text>')
    L.append(sc(30,82,'Raft Foundation','blue'))
    for i,(n,d) in enumerate([('Node A (Leader)','propose'),('Node B (Follower)','replicate'),('Node C (Follower)','ack')]):
        x=30+i*240; L+=tb(x,98,210,40,'blue'); L.append(lb(x+105,118,n,11)); L.append(sb(x+105,130,d,9))
    L.append(sc(30,168,'Lease Mechanism','green'))
    for i,(n,d) in enumerate([('Range Lease','time-bounded lease for key range'),('Range Gossip','lease status via gossip')]):
        x=30+i*400; L+=tb(x,186,370,68,'green'); L.append(lb(x+185,208,n,11))
        L.append(sb(x+185,228,d,9))
    L.append(sc(30,284,'Multi-range Scaling','purple'))
    for i,(n,d) in enumerate([('Range A','holder: N1'),('Range B','holder: N2'),('Range C','holder: N3'),('Range D','holder: N1')]):
        x=30+i*200; L+=tb(x,300,180,44,'purple'); L.append(lb(x+90,320,n,11)); L.append(sb(x+90,338,d,9))
    L.append(sc(30,370,'Benefit: Load distribution → each node is leader for ~1/3 of ranges','orange'))
    L+=tb(30,384,760,32,'orange'); L.append(lb(410,405,'Query routing to leaseholder avoids multi-hop Raft reads',10,'#374151','500'))
    return make_svg(820,430,['gray'],L,'cockroachdb-leader-lease.svg')

# ============ 6. Doris Evolution ============
def gen_doris_evolution():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Doris Architecture Evolution — Palo 1.0 → v3.0</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">From tightly-coupled Shared-Nothing to disaggregated Storage-Compute Separation</text>')
    for era,y0,items,col in [
        ('Palo 1.0 (2017)',82,[('FE+BE\nsame node','local disk'),('MySQL\nProtocol','frontend'),('BDB-JE\nmetadata','embedded'),('No MoW\nappend only','batch load')],'red'),
        ('Doris 1.x (2020–2022)',200,[('FE/BE\nseparate','FE stateless'),('Nereids\nCBO','cost optimizer'),('Segment v2\ncolumnar','zone map idx'),('MoW Upsert','DELETE_BITMAP')],'orange'),
        ('Doris 2.0/3.0 (2023–)',318,[('FE/Compute\nstateless','auto-scale'),('Meta Svc\nFoundationDB','replace BDB-JE'),('Shared\nStorage S3','remote data'),('Cloud\nNative','K8s deploy')],'green')]:
        L.append(sc(30,y0,era,col))
        for i,(n,d) in enumerate(items):
            x=30+i*200; L+=tb(x,y0+14,182,52,col); L.append(lb(x+91,y0+34,n.split('\n')[0],10)); L.append(sb(x+91,y0+52,d,9))
        if col!='green': L.append(ar(420,y0+66,420,y0+80,'blue'))
    L.append(f'  <g transform="translate(30,410)">')
    for i,(t,c) in enumerate([('Palo 1.0','red'),('Doris 1.x','orange'),('Doris 2.0+','green')]):
        L.append(f'    <rect x="{i*150}" y="0" width="14" height="14" rx="3" fill="{TG[c]}" stroke="{TS[c]}" stroke-width="1"/>')
        L.append(f'    <text x="{i*150+20}" y="12" fill="#6b7280" font-size="10">{t}</text>')
    L.append(f'  </g>')
    return make_svg(840,440,['blue','gray'],L,'doris-architecture-evolution.svg')

# ============ 7. InfluxDB Read/Write Path ============
def gen_influx_rw():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">InfluxDB Write &amp; Read Path</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Write: Line Protocol → WAL → TSM cache → Parquet. Read: TSI Index → Bloom → Cache → Arrow</text>')
    L.append(sc(30,82,'Write Path (Time-Ordered)','blue'))
    for i,(n,d) in enumerate([('Line Protocol','measurement,tags fields ts'),('WAL Append','sequential durability'),('Cache → TSM','dict compress → file'),('Parquet (v3)','Arrow Flight write')]):
        L+=tb(30,96+i*66,370,52,'blue'); L.append(lb(50,116+i*66,n,12,a='start')); L.append(sb(50,132+i*66,d,9,a='start'))
        if i<3: L.append(ar(400,122+i*66,434,122+i*66,'blue'))
    L.append(sc(440,82,'Read Path','purple'))
    for i,(n,d) in enumerate([('TSI Index','tag → seriesID lookup'),('Bloom Filter','TSM existence check'),('Cache Read','WAL + TSM block cache'),('Parquet Read','Arrow + DataFusion')]):
        L+=tb(440,96+i*66,370,52,'purple'); L.append(lb(460,116+i*66,n,12,a='start')); L.append(sb(460,132+i*66,d,9,a='start'))
    L.append(f'  <g transform="translate(30,390)">')
    for i,(t,c) in enumerate([('Write Path','blue'),('Read Path','purple'),('v3.0 Arrow','green')]):
        L.append(f'    <rect x="{i*160}" y="0" width="14" height="14" rx="3" fill="{TG[c]}" stroke="{TS[c]}" stroke-width="1"/>')
        L.append(f'    <text x="{i*160+20}" y="12" fill="#6b7280" font-size="10">{t}</text>')
    L.append(f'  </g>')
    return make_svg(820,420,['blue','gray'],L,'influxdb-read-write-path.svg')

# ============ 8. Dataflow Model ============
def gen_dataflow():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Dataflow Model — Windowing, Watermarks &amp; Triggers</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Unified model underpinning Apache Beam, Flink, and modern stream processing</text>')
    L.append(sc(30,80,'Windowing','blue'))
    for i,(n,d) in enumerate([('Fixed','aligned, N-min intervals'),('Sliding','N min, M min slide'),('Session','activity-gap based'),('Global','single per key')]):
        x=30+i*200; L+=tb(x,94,182,48,'blue'); L.append(lb(x+91,114,n,11)); L.append(sb(x+91,132,d,9))
    L.append(sc(30,170,'Watermarks','orange'))
    for i,(n,d) in enumerate([('Event Time','source timestamp'),('W(t)','max seen - lateness'),('Late Data','< W(t) → side output')]):
        x=30+i*260; L+=tb(x,184,240,48,'orange'); L.append(lb(x+120,204,n,11)); L.append(sb(x+120,222,d,9))
        if i<2: L.append(ar(x+240,208,x+260,208,'orange'))
    L.append(sc(30,262,'Triggers','green'))
    for i,(n,d) in enumerate([('Processing Time','every N sec'),('Element Count','every N elements'),('Watermark','when W advances'),('Composite','OR/AND of triggers')]):
        x=30+i*200; L+=tb(x,276,182,48,'green'); L.append(lb(x+91,296,n,11)); L.append(sb(x+91,314,d,9))
    L.append(sc(30,360,'Accumulation Modes','purple'))
    for i,(n,d) in enumerate([('Discarding','reset per pane'),('Accumulating','retract + re-emit'),('Acc & Retract','correct past')]):
        x=30+i*260; L+=tb(x,374,240,48,'purple'); L.append(lb(x+120,394,n,11)); L.append(sb(x+120,412,d,9))
    return make_svg(820,450,['orange','gray'],L,'dataflow-model.svg')

# ============ 9. Fluss vs Kafka Architecture ============
def gen_fluss_arch():
    L=[]
    L.append('  <text x="30" y="32" fill="#111827" font-size="16" font-weight="700">Fluss vs Kafka — Architecture Comparison</text>')
    L.append('  <text x="30" y="50" fill="#6b7280" font-size="11">Kafka-compatible protocol on rebuilt storage kernel with Arrow/Parquet lakehouse</text>')
    # Kafka
    L.append(sc(30,82,'Kafka 2.7.2','red'))
    kf=[('Producer API','batch send','red'),('Broker','partition leader + ISR','red'),('Log Segment','.log + .index + .timeindex','red'),('Consumer','pull + offset commit','red'),('ZooKeeper','metadata + controller','red')]
    for i,(n,d,c) in enumerate(kf):
        L+=tb(30,96+i*60,350,48,c); L.append(lb(205,116+i*60,n,11)); L.append(sb(205,132+i*60,d,9))
    # Fluss
    L.append(sc(440,82,'Fluss (Next-Gen)','green'))
    fs=[('Fluss Client','wire-compat with Kafka','green'),('Coordinator','ISR + metadata + routing','green'),('LogSegment','Arrow batch + Parquet','green'),('TieredStorage','L0→S3 automatic','green'),('Lakehouse','Iceberg catalog + query','green')]
    for i,(n,d,c) in enumerate(fs):
        L+=tb(440,96+i*60,380,48,c); L.append(lb(630,116+i*60,n,11)); L.append(sb(630,132+i*60,d,9))
    # Vertical mapping arrows
    for i in range(5):
        y=120+i*60; L.append(f'  <line x1="385" y1="{y}" x2="432" y2="{y}" stroke="#9333ea" stroke-width="1" stroke-dasharray="4,3"/>')
        L.append(f'  <text x="409" y="{y-6}" fill="#9333ea" font-size="7" text-anchor="middle">→</text>')
    # Bottom: differentiation
    L.append(sc(30,410,'Key Differentiation','purple'))
    diffs=[('Arrow Col.','batch format'),('Parquet Lake','open table'),('Tiered Store','∞ retention'),('Native Flink','SQL engine')]
    for i,(n,d) in enumerate(diffs):
        x=30+i*200; L+=tb(x,426,182,44,'purple'); L.append(lb(x+91,448,n,11)); L.append(sb(x+91,464,d,9))
    return make_svg(860,490,['gray'],L,'fluss-vs-kafka-architecture.svg')

# MAIN
if __name__ == '__main__':
    diagrams = [gen_rum(), gen_write_amp(), gen_silo(), gen_log_db(), gen_crdb_lease(),
                gen_doris_evolution(), gen_influx_rw(), gen_dataflow(), gen_fluss_arch()]
    for d in diagrams: print(f'  {d}')
    print(f'\nDone. {len(diagrams)} diagrams.')
