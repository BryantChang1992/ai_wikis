#!/usr/bin/env python3
"""
Convert ASCII art code blocks in Markdown files to inline SVG.
"""
import re, os

BASE = "/home/admin/.openclaw/workspace/agents/cto/work/ai_wikis/知识库"

# SVG templates as dict: {name: svg_content}
SVG = {}
SVG["wal"] = '<svg viewBox="0 0 800 220" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="13">'
SVG["wal"] += '<defs><marker id="aw" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["wal"] += '<text x="400" y="20" text-anchor="middle" fill="currentColor" font-size="13">写入路径</text>'
# Box1: User SQL
SVG["wal"] += '<rect x="10" y="40" width="120" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="70" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">User SQL</text><text x="70" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">请求</text>'
# Arrow 1->2
SVG["wal"] += '<line x1="130" y1="65" x2="180" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#aw)"/>'
# Box2: WAL
SVG["wal"] += '<rect x="182" y="40" width="130" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="247" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">WAL 日志</text><text x="247" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">(顺序写)</text>'
# Arrow 2->3
SVG["wal"] += '<line x1="312" y1="65" x2="362" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#aw)"/>'
# Box3: Buffer Pool
SVG["wal"] += '<rect x="364" y="40" width="150" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="439" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">内存 Buffer</text><text x="439" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Pool</text>'
# Arrow 3->4
SVG["wal"] += '<line x1="514" y1="65" x2="564" y2="65" stroke="currentColor" stroke-width="1.5" marker-end="url(#aw)"/>'
# Box4: Data Pages
SVG["wal"] += '<rect x="566" y="40" width="140" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="636" y="58" text-anchor="middle" fill="currentColor" dominant-baseline="middle">数据页</text><text x="636" y="78" text-anchor="middle" fill="currentColor" dominant-baseline="middle">(异步刷盘)</text>'
# Arrow down to fsync
SVG["wal"] += '<line x1="247" y1="90" x2="247" y2="115" stroke="currentColor" stroke-width="1.5"/><text x="247" y="110" text-anchor="middle" fill="currentColor" font-size="12">fsync()</text><line x1="247" y1="115" x2="247" y2="128" stroke="currentColor" stroke-width="1.5" marker-end="url(#aw)"/>'
# Box5: Disk Log
SVG["wal"] += '<rect x="160" y="133" width="175" height="50" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="247" y="151" text-anchor="middle" fill="currentColor" dominant-baseline="middle">磁盘日志</text><text x="247" y="171" text-anchor="middle" fill="currentColor" dominant-baseline="middle">← 持久化完成，事务可提交</text>'
SVG["wal"] += '</svg>'

SVG["2pc"] = '<svg viewBox="0 0 650 200" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["2pc"] += '<defs><marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker><marker id="al" markerWidth="8" markerHeight="6" refX="0" refY="3" orient="auto"><path d="M8,0 L0,3 L8,6Z" fill="currentColor"/></marker></defs>'
SVG["2pc"] += '<text x="325" y="16" text-anchor="middle" fill="currentColor" font-size="13">时序列（成功场景）</text>'
# Coord
SVG["2pc"] += '<text x="30" y="40" fill="currentColor" font-weight="bold">Coordinator</text><line x1="50" y1="45" x2="50" y2="195" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>'
# PA
SVG["2pc"] += '<text x="260" y="40" fill="currentColor" font-weight="bold">Participant A</text><line x1="270" y1="45" x2="270" y2="195" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>'
# PB
SVG["2pc"] += '<text x="500" y="40" fill="currentColor" font-weight="bold">Participant B</text><line x1="510" y1="45" x2="510" y2="195" stroke="currentColor" stroke-width="1" stroke-dasharray="3,3"/>'
# Prepare
SVG["2pc"] += '<line x1="50" y1="60" x2="265" y2="60" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar)"/><text x="160" y="56" text-anchor="middle" fill="currentColor" font-size="12">── Prepare →</text>'
SVG["2pc"] += '<line x1="50" y1="75" x2="505" y2="75" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar)"/><text x="280" y="71" text-anchor="middle" fill="currentColor" font-size="12">── Prepare →</text>'
# Yes
SVG["2pc"] += '<line x1="270" y1="92" x2="55" y2="92" stroke="currentColor" stroke-width="1.5" marker-end="url(#al)"/><text x="160" y="88" text-anchor="middle" fill="currentColor" font-size="12">← Yes ──</text>'
SVG["2pc"] += '<line x1="510" y1="107" x2="55" y2="107" stroke="currentColor" stroke-width="1.5" marker-end="url(#al)"/><text x="280" y="103" text-anchor="middle" fill="currentColor" font-size="12">← Yes ──</text>'
# Commit
SVG["2pc"] += '<line x1="50" y1="124" x2="265" y2="124" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar)"/><text x="160" y="120" text-anchor="middle" fill="currentColor" font-size="12">── Commit →</text>'
SVG["2pc"] += '<line x1="50" y1="139" x2="505" y2="139" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar)"/><text x="280" y="135" text-anchor="middle" fill="currentColor" font-size="12">── Commit →</text>'
# ACK
SVG["2pc"] += '<line x1="270" y1="156" x2="55" y2="156" stroke="currentColor" stroke-width="1.5" marker-end="url(#al)"/><text x="160" y="152" text-anchor="middle" fill="currentColor" font-size="12">← ACK ──</text>'
SVG["2pc"] += '<line x1="510" y1="171" x2="55" y2="171" stroke="currentColor" stroke-width="1.5" marker-end="url(#al)"/><text x="280" y="167" text-anchor="middle" fill="currentColor" font-size="12">← ACK ──</text>'
SVG["2pc"] += '</svg>'

SVG["saga"] = '<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["saga"] += '<defs><marker id="ar1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["saga"] += '<text x="145" y="18" text-anchor="middle" fill="currentColor" font-size="12" font-weight="bold">编排模式 (Choreography)</text><text x="450" y="18" text-anchor="middle" fill="currentColor" font-size="12" font-weight="bold">管控模式 (Orchestration)</text>'
SVG["saga"] += '<rect x="30" y="35" width="100" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="80" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service A</text>'
SVG["saga"] += '<rect x="30" y="100" width="100" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="80" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service C</text>'
SVG["saga"] += '<rect x="160" y="35" width="100" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="210" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service B</text>'
SVG["saga"] += '<rect x="160" y="100" width="100" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="210" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Service D</text>'
SVG["saga"] += '<line x1="130" y1="50" x2="158" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar1)"/>'
SVG["saga"] += '<line x1="210" y1="65" x2="82" y2="98" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar1)"/>'
SVG["saga"] += '<line x1="80" y1="100" x2="168" y2="100" stroke="currentColor" stroke-width="1"/><text x="145" y="96" text-anchor="middle" fill="currentColor" font-size="11">←──|──→</text>'
SVG["saga"] += '<rect x="370" y="35" width="90" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="415" y="55" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Orchestrator</text>'
SVG["saga"] += '<rect x="340" y="100" width="65" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="372" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">A</text>'
SVG["saga"] += '<rect x="415" y="100" width="65" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="447" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">B</text>'
SVG["saga"] += '<rect x="490" y="100" width="65" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="522" y="120" text-anchor="middle" fill="currentColor" dominant-baseline="middle">C</text>'
SVG["saga"] += '<line x1="385" y1="65" x2="372" y2="98" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar1)"/><line x1="415" y1="65" x2="447" y2="98" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar1)"/><line x1="445" y1="65" x2="522" y2="98" stroke="currentColor" stroke-width="1.5" marker-end="url(#ar1)"/>'
SVG["saga"] += '</svg>'

SVG["txn_msg"] = '<svg viewBox="0 0 500 280" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["txn_msg"] += '<defs><marker id="am" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["txn_msg"] += '<text x="250" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">生产者流程</text>'
SVG["txn_msg"] += '<rect x="80" y="30" width="200" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="180" y="53" text-anchor="middle" fill="currentColor" dominant-baseline="middle">1. 发送半消息</text>'
SVG["txn_msg"] += '<line x1="280" y1="48" x2="330" y2="48" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/>'
SVG["txn_msg"] += '<rect x="332" y="30" width="150" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="407" y="48" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Broker (消息不可见)</text>'
SVG["txn_msg"] += '<line x1="180" y1="66" x2="180" y2="90" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/>'
SVG["txn_msg"] += '<rect x="80" y="94" width="200" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="180" y="117" text-anchor="middle" fill="currentColor" dominant-baseline="middle">2. 执行本地事务</text>'
SVG["txn_msg"] += '<line x1="180" y1="130" x2="115" y2="155" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/><line x1="180" y1="130" x2="245" y2="155" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/>'
SVG["txn_msg"] += '<text x="90" y="150" text-anchor="middle" fill="currentColor">Commit</text><text x="260" y="150" text-anchor="middle" fill="currentColor">Rollback</text>'
SVG["txn_msg"] += '<line x1="115" y1="163" x2="115" y2="180" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/><line x1="245" y1="163" x2="245" y2="180" stroke="currentColor" stroke-width="1.5" marker-end="url(#am)"/>'
SVG["txn_msg"] += '<rect x="28" y="184" width="165" height="34" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="110" y="206" text-anchor="middle" fill="currentColor" dominant-baseline="middle">消息可见</text>'
SVG["txn_msg"] += '<rect x="228" y="184" width="165" height="34" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="310" y="206" text-anchor="middle" fill="currentColor" dominant-baseline="middle">消息删除</text>'
SVG["txn_msg"] += '<rect x="40" y="235" width="420" height="36" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="250" y="253" text-anchor="middle" fill="currentColor" dominant-baseline="middle">3. Broker 定期回查 → 决定 Commit / Rollback</text>'
SVG["txn_msg"] += '</svg>'

SVG["prewrite"] = '<svg viewBox="0 0 620 180" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["prewrite"] += '<text x="310" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Percolator 事务流程</text>'
SVG["prewrite"] += '<rect x="20" y="30" width="580" height="60" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="30" y="46" fill="currentColor" font-weight="bold">Phase 1: Prewrite（预写）</text><text x="40" y="62" fill="currentColor">1. 从 TSO 获取 start_ts | 选 primary | 写写冲突检测 | 写 data 列</text>'
SVG["prewrite"] += '<rect x="20" y="106" width="580" height="60" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="30" y="122" fill="currentColor" font-weight="bold">Phase 2: Commit</text><text x="40" y="138" fill="currentColor">1. 从 TSO 获取 commit_ts | 2. 对 primary 写 write 列(标志提交)</text><text x="40" y="154" fill="currentColor">3. 异步删除 primary lock | 4. 异步清理 secondary</text>'
SVG["prewrite"] += '</svg>'

SVG["truetime"] = '<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["truetime"] += '<text x="300" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Spanner 架构要点</text>'
SVG["truetime"] += '<rect x="200" y="30" width="200" height="36" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="300" y="53" text-anchor="middle" fill="currentColor" dominant-baseline="middle">TrueTime API</text><text x="405" y="48" fill="currentColor" font-size="11">← GPS + Atomic Clocks</text>'
SVG["truetime"] += '<line x1="300" y1="66" x2="300" y2="86" stroke="currentColor" stroke-width="1.5"/>'
SVG["truetime"] += '<rect x="30" y="96" width="250" height="50" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="155" y="116" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Zone A (Paxos) / Spanserver...</text>'
SVG["truetime"] += '<rect x="320" y="96" width="250" height="50" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="445" y="116" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Zone B (Paxos) / Spanserver...</text>'
SVG["truetime"] += '<line x1="300" y1="86" x2="155" y2="94" stroke="currentColor" stroke-width="1"/><line x1="300" y1="86" x2="445" y2="94" stroke="currentColor" stroke-width="1"/>'
SVG["truetime"] += '<line x1="155" y1="146" x2="155" y2="170" stroke="currentColor" stroke-width="1"/><line x1="445" y1="146" x2="445" y2="170" stroke="currentColor" stroke-width="1"/><line x1="155" y1="170" x2="445" y2="170" stroke="currentColor" stroke-width="1.5"/>'
SVG["truetime"] += '<text x="300" y="186" text-anchor="middle" fill="currentColor">跨 Paxos Group 事务</text><text x="290" y="117" text-anchor="middle" fill="currentColor" font-size="18">← 2PC →</text>'
SVG["truetime"] += '</svg>'

SVG["calvin"] = '<svg viewBox="0 0 620 210" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["calvin"] += '<defs><marker id="ac" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["calvin"] += '<text x="310" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">Calvin 架构流程</text>'
SVG["calvin"] += '<rect x="30" y="30" width="560" height="48" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="40" y="46" fill="currentColor" font-weight="bold">Phase 1: Sequencing（排序层）</text><text x="50" y="66" fill="currentColor">事务汇聚 → 分配全局唯一顺序 → 广播到所有 Scheduler</text>'
SVG["calvin"] += '<line x1="310" y1="78" x2="310" y2="92" stroke="currentColor" stroke-width="1.5" marker-end="url(#ac)"/>'
SVG["calvin"] += '<rect x="30" y="96" width="560" height="48" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="40" y="112" fill="currentColor" font-weight="bold">Phase 2: Scheduling（调度层）</text><text x="50" y="132" fill="currentColor">分区独立按全局顺序执行事务；无需 2PC</text>'
SVG["calvin"] += '<line x1="310" y1="144" x2="310" y2="158" stroke="currentColor" stroke-width="1.5" marker-end="url(#ac)"/>'
SVG["calvin"] += '<rect x="30" y="162" width="560" height="40" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="40" y="178" fill="currentColor" font-weight="bold">Phase 3: Storage（存储层）</text><text x="50" y="194" fill="currentColor">各分区持久化结果，确定性执行保证多副本一致</text>'
SVG["calvin"] += '</svg>'

SVG["innodb"] = '<svg viewBox="0 0 420 230" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["innodb"] += '<defs><marker id="ai" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["innodb"] += '<text x="210" y="16" text-anchor="middle" fill="currentColor" font-size="13">InnoDB 架构概览</text>'
SVG["innodb"] += '<rect x="60" y="26" width="300" height="36" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="210" y="48" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Server Layer — SQL Parser → Optimizer</text>'
SVG["innodb"] += '<line x1="210" y1="62" x2="210" y2="76" stroke="currentColor" stroke-width="1.5" marker-end="url(#ai)"/>'
SVG["innodb"] += '<rect x="40" y="80" width="340" height="140" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="55" y="98" fill="currentColor">InnoDB Engine</text>'
SVG["innodb"] += '<rect x="60" y="105" width="160" height="40" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="140" y="123" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Buffer Pool (内存)</text>'
SVG["innodb"] += '<rect x="70" y="128" width="60" height="18" rx="3" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="100" y="142" text-anchor="middle" fill="currentColor" font-size="11">Pages</text>'
SVG["innodb"] += '<rect x="145" y="128" width="60" height="18" rx="3" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="175" y="142" text-anchor="middle" fill="currentColor" font-size="11">Undo Log</text>'
SVG["innodb"] += '<rect x="230" y="105" width="130" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="295" y="125" text-anchor="middle" fill="currentColor" dominant-baseline="middle">Redo Log Buffer</text>'
SVG["innodb"] += '<line x1="295" y1="135" x2="295" y2="148" stroke="currentColor" stroke-width="1.5" marker-end="url(#ai)"/>'
SVG["innodb"] += '<rect x="230" y="152" width="130" height="30" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/><text x="295" y="172" text-anchor="middle" fill="currentColor" dominant-baseline="middle">ib_logfile (磁盘)</text>'
SVG["innodb"] += '</svg>'

SVG["heap"] = '<svg viewBox="0 0 480 120" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["heap"] += '<text x="240" y="16" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">表元组（Heap Tuple）</text>'
SVG["heap"] += '<rect x="30" y="28" width="420" height="80" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="50" y="48" fill="currentColor">t_xmin: 插入/创建该元组的事务 ID</text><text x="50" y="66" fill="currentColor">t_xmax: 删除/更新该元组的事务 ID</text><text x="50" y="84" fill="currentColor">t_ctid: 指向新版本的指针（更新时）</text><text x="50" y="100" fill="currentColor">t_infomask: 标志位</text>'
SVG["heap"] += '</svg>'

SVG["xid"] = '<svg viewBox="0 0 620 180" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["xid"] += '<text x="310" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">XID 空间逻辑视图（环形）</text>'
SVG["xid"] += '<text x="590" y="34" text-anchor="end" fill="currentColor">2^31-1</text><text x="60" y="50" fill="currentColor">过去</text><text x="310" y="50" text-anchor="middle" fill="currentColor" font-weight="bold">当前</text><text x="560" y="50" text-anchor="end" fill="currentColor">未来</text>'
SVG["xid"] += '<line x1="120" y1="55" x2="530" y2="55" stroke="currentColor" stroke-width="1.5"/><line x1="530" y1="55" x2="550" y2="50" stroke="currentColor" stroke-width="1.5"/><line x1="530" y1="55" x2="550" y2="60" stroke="currentColor" stroke-width="1.5"/>'
SVG["xid"] += '<rect x="20" y="65" width="580" height="36" rx="0" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="45" y="88" text-anchor="middle" fill="currentColor">...</text>'
SVG["xid"] += '<rect x="120" y="65" width="100" height="36" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="170" y="88" text-anchor="middle" fill="currentColor">Frozen</text>'
SVG["xid"] += '<rect x="280" y="65" width="100" height="36" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="330" y="88" text-anchor="middle" fill="currentColor">Current</text>'
SVG["xid"] += '<rect x="380" y="65" width="220" height="36" fill="transparent" stroke="currentColor" stroke-width="1.5"/>'
SVG["xid"] += '<line x1="520" y1="101" x2="520" y2="118" stroke="currentColor" stroke-width="1.5"/><text x="520" y="125" text-anchor="middle" fill="currentColor" font-size="11">0 (回卷点)</text>'
SVG["xid"] += '</svg>'

SVG["tidb"] = '<svg viewBox="0 0 460 220" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="12">'
SVG["tidb"] += '<defs><marker id="at" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6Z" fill="currentColor"/></marker></defs>'
SVG["tidb"] += '<text x="230" y="18" text-anchor="middle" fill="currentColor" font-size="13" font-weight="bold">TiDB/TiKV 架构分层</text>'
SVG["tidb"] += '<rect x="30" y="28" width="400" height="36" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/><text x="230" y="50" text-anchor="middle" fill="currentColor" dominant-baseline="middle
