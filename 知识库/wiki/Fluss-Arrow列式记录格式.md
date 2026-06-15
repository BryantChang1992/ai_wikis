---
type: concept
title: "Fluss Arrow 列式记录格式"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/02-存储引擎模块.html"
tags:
  - "Fluss"
  - "Arrow"
  - "列式存储"
  - "记录格式"
  - "谓词下推"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-存储引擎]]"
  - "[[Fluss-KV存储-RocksDB]]"
  - "[[Fluss-客户端与计算集成]]"
diagram: "diagram/fluss-architecture.svg"

---

# Fluss Arrow 列式记录格式

## 定义

Fluss 使用 Apache Arrow 作为核心数据格式，替代了 Kafka 的行式 Key/Value 字节流（`byte[] key, byte[] value`）。这是 Fluss 与 Kafka 最根本的**数据模型差异**——从"通用字节流"转向"结构化列式数据"。

## 三种 LogFormat

| 格式 | 适用场景 | 特点 |
|------|---------|------|
| `ARROW` | 所有表类型（默认） | Arrow 列式，支持列裁剪、谓词下推 |
| `COMPACTED` | PK 表 changelog | 同 key 合并，减少 changelog 体积，加速 KV 恢复 |
| `INDEXED` | PK 表（点查优化） | 带索引的格式，加速 `Lookup` 操作 |

## 与 Kafka Record 的根本差异

| 维度 | Fluss Arrow Row | Kafka Record |
|------|----------------|-------------|
| **数据格式** | Arrow Vector（列式） | Key+Value bytes（行式） |
| **Schema** | ✅ 内建（通过 schema id 管理版本） | ❌ 服务端不解析 |
| **Schema Evolution** | ✅ 服务端支持（schema id 映射） | ❌ 客户端自行管理 |
| **序列化** | Arrow IPC（零拷贝列式） | 自定义二进制格式 |
| **压缩** | 整列压缩（相同类型数据压缩率更高） | `gzip`/`snappy`/`lz4`/`zstd`（行级压缩） |
| **列裁剪** | ✅ 只读需要的列，跳过其余 | ❌ 必须读完整 Record |
| **谓词下推** | ✅ Arrow 统计信息（列 min/max/null-count） | ❌ | 
| **向量化** | ✅ 天然支持 SIMD 批处理 | ❌ 逐行处理 |

## 为什么 Arrow 对 Fluss 至关重要

### 1. 列裁剪（Column Pruning）

查询 `SELECT name FROM users` 时，Fluss 只需读取 `name` 列的数据，完全跳过 `age`、`email` 等列。在宽表场景下（如 100 列的表），这可以减少 90%+ 的 IO。Kafka 必须读完整 Record 然后由客户端解析——IO 浪费在服务端无法避免。

### 2. 谓词下推（Predicate Pushdown）

`WHERE age > 18 AND city = 'Beijing'` 可以在 TabletServer 端直接过滤。Arrow 的列统计信息（min/max/null-count）使 Fluss 能够：
- **Partition 级剪枝**：如果某个 partition 的 age 列 max < 18，整个跳过
- **Segment 级剪枝**：如果某个 segment 的 city 列不包含 'Beijing'，跳过

Kafka 2.7.2 完全不支持服务端过滤。

### 3. 零拷贝 Flink 集成

```
Fluss Arrow Vector → Flink ArrowReader → Flink RowData（零列拷贝）
```

`FlussRowToFlinkRowConverter` 的核心路径是**指针偏移**而非数据复制——Arrow VectorSchemaRoot 的内存布局与 Flink 的 ColumnarRowData 可以直接映射。

### 4. Lake 层零拷贝

参见 [[Fluss-Lake层与湖仓融合]]。Lance 后端的写入路径：

```
Fluss Arrow batch → ShadedArrowBatchWriter → Lance 文件（零拷贝）
```

从 Fluss 内存到 Lake 文件，整个路径上没有一次序列化/反序列化。

## 写入批次类型

所有写入批次都对应一个 LogFormat：

| 批次类 | LogFormat | 说明 |
|--------|-----------|------|
| `ArrowLogWriteBatch` | ARROW | 标准 Arrow 列式写入 |
| `CompactedLogWriteBatch` | COMPACTED | 压缩格式，同 key 合并 |
| `IndexedLogWriteBatch` | INDEXED | 索引格式，加速点查 |

## 代价

Arrow 列式格式并非没有代价：
- **小批次写入效率更低**：列式格式需要积累足够数据才能高效压缩（类似 Parquet 的 row group）
- **单行点查开销更大**：点查一行需要访问多个列块，而行式存储一行在连续的 bytes 中
- **内存占用模式不同**：Arrow 使用 off-heap 内存（通过 `BufferAllocator`），需要额外的内存管理

Fluss 通过 `INDEXED` LogFormat 和 RocksDB KV 层来缓解点查场景的性能损失——点查走 RocksDB（行式索引），批量分析走 Arrow（列式扫描）。

---

> **关键洞察**：Arrow 是 Fluss "重计算、轻存储"设计哲学的基石。Kafka 的设计假设是"数据在服务端只是暂存，计算在客户端做"，所以服务端不需要理解数据格式。Fluss 的设计假设是"计算应该尽可能靠近数据"，所以 Arrow 的列式格式让服务端可以做列裁剪、谓词下推、向量化聚合——把更多计算工作从客户端转移到服务端。这在 Flink Source 的 Split 级别体现得最明显：Kafka Consumer 拉取时是"全部"或"按 partition 过滤"，Fluss Scanner 可以在 Segment 级别甚至 Row Group 级别进行数据过滤。
