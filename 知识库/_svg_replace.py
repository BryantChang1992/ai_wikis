#!/usr/bin/env python3
"""
Replace ASCII art code blocks (with box drawing characters) 
with semantically equivalent inline SVG.
Only processes fenced code blocks that contain box-drawing chars.
"""
import re
import os

def gen_svg_wal(lines):
    """WAL write path flow"""
    title = "写入路径"
    svg = '''<svg viewBox="0 0 800 220" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="13">
  <defs>
    <marker id="arrow-wal" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="400" y="20" text-anchor="middle" fill="currentColor" font-size="13">{title}</text>
  <!-- Box 1: User SQL -->
  <rect x="10" y="40" width="120" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="70" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">User SQL</text>
  <text x="70" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">请求</text>
  <!-- Arrow 1→2 -->
  <line x1="130" y1="65" x2="180" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-wal)"/>
  <!-- Box 2: WAL -->
  <rect x="182" y="40" width="130" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="247" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">WAL 日志</text>
  <text x="247" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">(顺序写)</text>
  <!-- Arrow 2→3 -->
  <line x1="312" y1="65" x2="362" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-wal)"/>
  <!-- Box 3: Buffer Pool -->
  <rect x="364" y="40" width="150" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="439" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">内存 Buffer</text>
  <text x="439" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Pool</text>
  <!-- Arrow 3→4 -->
  <line x1="514" y1="65" x2="564" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-wal)"/>
  <!-- Box 4: Data Pages -->
  <rect x="566" y="40" width="140" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="636" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">数据页</text>
  <text x="636" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">(异步刷盘)</text>
  <!-- Vertical line down from WAL -->
  <line x1="247" y1="90" x2="247" y2="115" stroke="currentColor" stroke-width="1.5"/>
  <text x="247" y="110" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="12">fsync()</text>
  <line x1="247" y1="115" x2="247" y2="125" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-wal)"/>
  <!-- Box 5: Disk Log -->
  <rect x="160" y="130" width="175" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="247" y="148" text-anchor="middle" fill="currentColor" dominant-baseline="middle">磁盘日志</text>
  <text x="247" y="168" text-anchor="middle" fill="currentColor" dominant-baseline="middle">← 持久化完成，事务可提交</text>
</svg>'''
    return svg

def gen_svg_2pc_seq(lines):
    """2PC success sequence diagram"""
    svg = '''<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="350" y="16" text-anchor="middle" fill="currentColor" font-size="13">时序列（成功场景）</text>
  <!-- Coordinator column -->
  <text x="30" y="40" fill="currentColor" font-weight="bold">Coordinator</text>
  <line x1="50" y1="45" x2="50" y2="190" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>
  <!-- Participant A column -->
  <text x="280" y="40" fill="currentColor" font-weight="bold">Participant A</text>
  <line x1="290" y1="45" x2="290" y2="190" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>
  <!-- Participant B column -->
  <text x="530" y="40" fill="currentColor" font-weight="bold">Participant B</text>
  <line x1="540" y1="45" x2="540" y2="190" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>
  <!-- Prepare arrows -->
  <line x1="50" y1="60" x2="285" y2="60" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc1)"/>
  <line x1="50" y1="75" x2="535" y2="75" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc1)"/>
  <text x="170" y="55" text-anchor="middle" fill="currentColor" font-size="12">── Prepare ──▶</text>
  <text x="300" y="70" text-anchor="middle" fill="currentColor" font-size="12">── Prepare ──▶</text>
  <!-- Yes arrows -->
  <line x1="290" y1="90" x2="55" y2="90" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc2)"/>
  <line x1="540" y1="105" x2="55" y2="105" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc2)"/>
  <text x="170" y="85" text-anchor="middle" fill="currentColor" font-size="12">◀── Yes ──</text>
  <text x="300" y="100" text-anchor="middle" fill="currentColor" font-size="12">◀── Yes ──</text>
  <!-- Commit arrows -->
  <line x1="50" y1="120" x2="285" y2="120" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc1)"/>
  <line x1="50" y1="135" x2="535" y2="135" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc1)"/>
  <text x="170" y="115" text-anchor="middle" fill="currentColor" font-size="12">── Commit ──▶</text>
  <text x="300" y="130" text-anchor="middle" fill="currentColor" font-size="12">── Commit ──▶</text>
  <!-- ACK arrows -->
  <line x1="290" y1="150" x2="55" y2="150" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc2)"/>
  <line x1="540" y1="165" x2="55" y2="165" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-2pc2)"/>
  <text x="170" y="145" text-anchor="middle" fill="currentColor" font-size="12">◀── ACK ──</text>
  <text x="300" y="160" text-anchor="middle" fill="currentColor" font-size="12">◀── ACK ──</text>
</svg>'''
    return svg

def gen_svg_saga(lines):
    """SAGA coordination modes"""
    svg = '''<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <defs>
    <marker id="arrow-saga" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-saga2" markerWidth="8" markerHeight="6" refX="0" refY="3" orient="auto">
      <path d="M8,0 L0,3 L8,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="140" y="20" text-anchor="middle" fill="currentColor" font-size="12" font-weight="bold">编排模式 (Choreography)</text>
  <text x="460" y="20" text-anchor="middle" fill="currentColor" font-size="12" font-weight="bold">管控模式 (Orchestration)</text>
  <!-- Left side: Choreography -->
  <rect x="30" y="35" width="110" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="85" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service A</text>
  <rect x="30" y="105" width="110" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="85" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service C</text>
  <rect x="170" y="35" width="110" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="225" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service B</text>
  <rect x="170" y="105" width="110" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="225" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service D</text>
  <line x1="140" y1="50" x2="168" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-saga)"/>
  <line x1="225" y1="65" x2="86" y2="105" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-saga)"/>
  <line x1="85" y1="105" x2="223" y2="105" stroke="currentColor" stroke-width="1.5"/>
  <text x="155" y="100" text-anchor="middle" fill="currentColor" font-size="11">◀─────▶</text>
  <!-- Right side: Orchestration -->
  <rect x="370" y="35" width="90" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="415" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Orchestrator</text>
  <rect x="340" y="105" width="70" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="375" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">A</text>
  <rect x="420" y="105" width="70" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="455" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">B</text>
  <rect x="500" y="105" width="70" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="535" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">C</text>
  <line x1="385" y1="65" x2="375" y2="103" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-saga)"/>
  <line x1="415" y1="65" x2="455" y2="103" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-saga)"/>
  <line x1="445" y1="65" x2="535" y2="103" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-saga)"/>
  <text x="375" y="85" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">|</text>
  <text x="455" y="85" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">|</text>
  <text x="535" y="85" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">|</text>
</svg>'''
    return svg

def gen_svg_txn_msg(lines):
    """Transactional message flow"""
    svg = '''<svg viewBox="0 0 500 280" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <defs>
    <marker id="arrow-txn" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="250" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">生产者流程</text>
  <!-- Step 1 -->
  <rect x="90" y="30" width="200" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="190" y="53" text-anchor="middle" fill="currentColor" dominant-baseline="middle">1. 发送半消息</text>
  <line x1="290" y1="48" x2="340" y2="48" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <rect x="342" y="30" width="150" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="417" y="48" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Broker</text>
  <text x="417" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">(消息不可见)</text>
  <!-- Arrow down -->
  <line x1="190" y1="66" x2="190" y2="90" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <!-- Step 2 -->
  <rect x="90" y="95" width="200" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="190" y="118" text-anchor="middle" fill="currentColor" dominant-baseline="middle">2. 执行本地事务</text>
  <!-- Branch down -->
  <line x1="190" y1="131" x2="125" y2="155" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <line x1="190" y1="131" x2="255" y2="155" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <text x="100" y="150" text-anchor="middle" fill="currentColor" font-size="12">Commit</text>
  <text x="260" y="150" text-anchor="middle" fill="currentColor" font-size="12">Rollback</text>
  <!-- Down from commit/rollback -->
  <line x1="125" y1="165" x2="125" y2="180" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <line x1="255" y1="165" x2="255" y2="180" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-txn)"/>
  <rect x="30" y="185" width="175" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="117" y="208" text-anchor="middle" fill="currentColor" dominant-baseline="middle">消息可见</text>
  <rect x="230" y="185" width="175" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="317" y="208" text-anchor="middle" fill="currentColor" dominant-baseline="middle">消息删除</text>
  <!-- Step 3 -->
  <line x1="117" y1="221" x2="117" y2="230" stroke="currentColor" stroke-width="1"/>
  <rect x="30" y="235" width="420" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="240" y="253" text-anchor="middle" fill="currentColor" dominant-baseline="middle">3. Broker 定期回查（未决事务）</text>
  <text x="240" y="263" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">→ 调用 Producer 的 check → 决定 Commit 或 Rollback</text>
</svg>'''
    return svg

def gen_svg_prewrite(lines):
    """Percolator Prewrite + Commit boxes"""
    svg = '''<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="300" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Percolator 事务流程</text>
  <!-- Phase 1: Prewrite -->
  <rect x="20" y="30" width="560" height="64" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="30" y="48" fill="currentColor" font-size="12" font-weight="bold">Phase 1: Prewrite（预写）</text>
  <text x="40" y="64" fill="currentColor" font-size="12">1. 从 TSO 获取 start_ts</text>
  <text x="40" y="80" fill="currentColor" font-size="12">2. 选一个 key 作为 primary，其余为 secondary</text>
  <!-- Phase 2: Commit -->
  <rect x="20" y="108" width="560" height="64" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="30" y="126" fill="currentColor" font-size="12" font-weight="bold">Phase 2: Commit</text>
  <text x="40" y="142" fill="currentColor" font-size="12">1. 从 TSO 获取 commit_ts</text>
  <text x="40" y="158" fill="currentColor" font-size="12">2. 对 primary 写 write 列(commit_ts + start_ts) ← 此操作成功标志事务提交</text>
</svg>'''
    return svg

def gen_svg_truetime(lines):
    """Spanner TrueTime architecture"""
    svg = '''<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="300" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Spanner 架构要点</text>
  <!-- TrueTime box -->
  <rect x="200" y="30" width="200" height="36" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="300" y="53" text-anchor="middle" fill="currentColor" dominant-baseline="middle">TrueTime API</text>
  <text x="410" y="48" fill="currentColor" font-size="11">← GPS + Atomic Clocks</text>
  <line x1="300" y1="66" x2="300" y2="88" stroke="currentColor" stroke-width="1.5"/>
  <line x1="300" y1="88" x2="170" y2="88" stroke="currentColor" stroke-width="1.5"/>
  <line x1="300" y1="88" x2="430" y2="88" stroke="currentColor" stroke-width="1.5"/>
  <!-- Zone A -->
  <rect x="30" y="100" width="260" height="50" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="160" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Zone A (Paxos)</text>
  <text x="160" y="140" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Spanserver...</text>
  <!-- Zone B -->
  <rect x="310" y="100" width="260" height="50" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="440" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Zone B (Paxos)</text>
  <text x="440" y="140" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Spanserver...</text>
  <!-- Line from TrueTime to both zones -->
  <line x1="300" y1="88" x2="160" y2="98" stroke="currentColor" stroke-width="1"/>
  <line x1="300" y1="88" x2="440" y2="98" stroke="currentColor" stroke-width="1"/>
  <!-- Arrow between zones -->
  <line x1="160" y1="125" x2="308" y2="125" stroke="currentColor" stroke-width="1.5"/>
  <text x="235" y="122" text-anchor="middle" fill="currentColor" font-size="12">◄─ 2PC ─►</text>
  <!-- Bottom line -->
  <line x1="160" y1="150" x2="160" y2="170" stroke="currentColor" stroke-width="1"/>
  <line x1="440" y1="150" x2="440" y2="170" stroke="currentColor" stroke-width="1"/>
  <line x1="160" y1="170" x2="440" y2="170" stroke="currentColor" stroke-width="1.5"/>
  <text x="300" y="185" text-anchor="middle" fill="currentColor" font-size="12">跨 Paxos Group 事务</text>
</svg>'''
    return svg

def gen_svg_calvin(lines):
    """Calvin three phases"""
    svg = '''<svg viewBox="0 0 600 210" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="300" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Calvin 架构流程</text>
  <!-- Phase 1 -->
  <rect x="30" y="30" width="540" height="48" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="40" y="48" fill="currentColor" font-size="12" font-weight="bold">Phase 1: Sequencing（排序层）</text>
  <text x="50" y="66" fill="currentColor" font-size="12">所有事务请求汇聚到 Sequencer；Sequencer 给每个事务分配全局唯一顺序（批处理）</text>
  <!-- Arrow -->
  <line x1="300" y1="78" x2="300" y2="92" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-cal)"/>
  <!-- Phase 2 -->
  <rect x="30" y="96" width="540" height="48" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="40" y="114" fill="currentColor" font-size="12" font-weight="bold">Phase 2: Scheduling（调度层）</text>
  <text x="50" y="132" fill="currentColor" font-size="12">每个分区独立地按照全局顺序执行事务；无需 2PC！多分区事务直接以相同顺序在各分区执行</text>
  <!-- Arrow -->
  <line x1="300" y1="144" x2="300" y2="158" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-cal)"/>
  <!-- Phase 3 -->
  <rect x="30" y="162" width="540" height="40" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="40" y="180" fill="currentColor" font-size="12" font-weight="bold">Phase 3: Storage（存储层）</text>
  <text x="50" y="194" fill="currentColor" font-size="12">每个分区的存储节点持久化结果；确定性执行保证多副本一致</text>
</svg>'''
    return svg

def gen_svg_innodb(lines):
    """MySQL InnoDB architecture"""
    svg = '''<svg viewBox="0 0 420 230" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <defs>
    <marker id="arrow-inn" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="210" y="16" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">InnoDB 架构概览</text>
  <!-- Server Layer -->
  <rect x="60" y="26" width="300" height="36" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="210" y="48" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Server Layer — SQL Parser → Optimizer</text>
  <line x1="210" y1="62" x2="210" y2="76" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-inn)"/>
  <!-- InnoDB Engine outer box -->
  <rect x="40" y="80" width="340" height="140" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="55" y="98" fill="currentColor" font-size="12">InnoDB Engine</text>
  <!-- Buffer Pool inner box -->
  <rect x="60" y="105" width="160" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="140" y="122" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Buffer Pool (内存)</text>
  <!-- Pages inner -->
  <rect x="75" y="130" width="60" height="18" rx="3" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="105" y="143" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">Pages</text>
  <!-- Undo Log inner -->
  <rect x="145" y="130" width="60" height="18" rx="3" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="175" y="143" text-anchor="middle" fill="currentColor" dominant-baseline="middle" font-size="11">Undo Log</text>
  <!-- Redo Log Buffer -->
  <rect x="230" y="105" width="130" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="295" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Redo Log Buffer</text>
  <line x1="295" y1="135" x2="295" y2="148" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-inn)"/>
  <!-- ib_logfile -->
  <rect x="230" y="152" width="130" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="295" y="172" text-anchor="middle" fill="currentColor" dominant-baseline="middle">ib_logfile (磁盘)</text>
</svg>'''
    return svg

def gen_svg_heap_tuple(lines):
    """PostgreSQL Heap Tuple"""
    svg = '''<svg viewBox="0 0 480 120" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="240" y="16" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">表元组（Heap Tuple）</text>
  <rect x="30" y="28" width="420" height="80" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="50" y="48" fill="currentColor" font-size="12">t_xmin: 插入/创建该元组的事务 ID</text>
  <text x="50" y="66" fill="currentColor" font-size="12">t_xmax: 删除/更新该元组的事务 ID</text>
  <text x="50" y="84" fill="currentColor" font-size="12">t_ctid: 指向新版本的指针（更新时）</text>
  <text x="50" y="100" fill="currentColor" font-size="12">t_infomask: 标志位</text>
</svg>'''
    return svg

def gen_svg_xid(lines):
    """PostgreSQL XID Wraparound"""
    svg = '''<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">
  <text x="300" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">XID 空间逻辑视图（环形）</text>
  <text x="570" y="30" fill="currentColor" font-size="12" text-anchor="end">2^31-1</text>
  <line x