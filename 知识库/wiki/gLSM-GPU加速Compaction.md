---
type: concept
title: "gLSM — GPU 加速 LSM-Tree Compaction"
sources: []
tags:
  - 存储引擎
  - LSM-Tree
  - Compaction
  - GPU
  - 硬件加速
  - 归并排序
created: 2026-07-02
updated: 2026-07-02
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-硬件适配]]"
  - "[[LSM-tree-KV-Survey-综述]]"
---
confidence: 0.8
confidence_rationale: "类型=concept; 来源×1; 4天前更新"


# gLSM — GPU 加速 LSM-Tree Compaction

## 一句话摘要

利用 GPU 大规模并行处理能力加速 LSM-tree 的核心瓶颈——归并排序 compaction，通过 CPU-GPU 流水线架构和批量合并策略，显著降低 compaction 延迟和写放大。

## 背景与动机

### Compaction 是 LSM-tree 的核心瓶颈

LSM-tree 的写路径将数据追加写入内存 MemTable，然后按层级 flush/compaction 到磁盘。每次 compaction 需要将多个有序 SSTable（Sorted String Table）进行多路归并排序，输出一个更大的有序 SSTable。

```
Compaction 过程:
  SSTable_1 (sorted)  -
  SSTable_2 (sorted)  ----► Multi-way Merge Sort --► SSTable_new (sorted)
  ...                  --
  SSTable_k (sorted)  -
```

**痛点**：
- Compaction 消耗大量 CPU（归并排序是 O(N log K) 比较密集操作）
- 写放大的根本来源——key 在各级之间反复被读写合并
- 当写入负载高时，compaction 跟不上 → write stall → P99 延迟尖刺
- 传统 CPU 归并受限于单核或有限多核的并行度

### 为什么用 GPU？

| GPU 优势 | 与 Compaction 的契合点 |
|----------|----------------------|
| 数千个并行计算核心 | 归并排序天然可并行（key 比较在 GPU threads 上并发执行） |
| 高内存带宽（HBM2/HBM3 可达 1-3 TB/s） | SSTable 数据批量加载到 GPU 显存，充分利用带宽 |
| SIMT 架构适合数据并行 | Merge sort 的每个比较-交换操作相互独立 |
| 相比 FPGA/ASIC 更通用 | 无需定制硬件，CUDA 生态成熟 |

## 核心创新

### 1. GPU 加速多路归并排序

将原本在 CPU 上执行的多路 `k-way merge` 卸载到 GPU：

```
传统 CPU Merge:
  k 个 SSTable → CPU 堆归并（O(N·log k) 比较） → 输出 SSTable
  
gLSM GPU Merge:
  k 个 SSTable → PCIe 传输 → GPU 显存 → GPU 并行归并 → PCIe 回传 → 写 SSTable
```

**GPU 并行归并的技术路线**：

| 方法 | 描述 | 取舍 |
|------|------|------|
| **并行 Bitonic Sort** | 将所有 chunk 合并 → GPU 全排序网络 | 适合均匀大小 chunk；GPU 内存占用高 |
| **GPU Merge Path** | 每个 GPU thread 独立确定自己在输出中的 partition | 减少全局同步，但不适合极度不均匀数据 |
| **分层归并（Hierarchical Merge）** | 先在 GPU 上做 batch-wise 归并，再做全局归并 | 更好地利用 GPU 共享内存层级 |
| **Radix Sort on GPU** | 整数 key 场景下，GPU radix sort 比比较排序更快 | 不适用于变长 key / 通用 comparator |

> gLSM 通常采用 **GPU Merge Path + Tiled Partition** 策略：将输入 SSTable 按 key 范围等分成多个 tile，每个 GPU block 独立处理一个 tile 的 merge，最大化并行度。

### 2. CPU-GPU 数据流水线

**核心问题**：PCIe 带宽（~32 GB/s per direction on PCIe 5.0 x16）远低于 GPU 显存带宽（~2 TB/s on H100），数据传输成为瓶颈。

**gLSM 流水线设计**：

```
阶段 1:  CPU 读 SSTable --► 缓冲 --► PCIe DMA 上传
阶段 2:                         GPU 归并排序 (并行)
阶段 3:  GPU 结果 ◄-- PCIe DMA 下传 ◄-- 写磁盘
         ↑_____________ 流水线并行 _____________↑
```

| 优化 | 说明 |
|------|------|
| **双缓冲 (Double Buffering)** | 当前 batch 在 GPU 计算时，下一 batch 通过 PCIe 上传 |
| **异步传输 (CUDA Streams)** | 使用多个 CUDA stream 同时进行上传/计算/下传 |
| **Heterogeneous 内存** | 利用 GPU Unified Memory 或直接内存访问降低拷贝 |

### 3. 大 Batch Compaction 优化

**核心思想**：单个 SSTable 太小则 PCIe 传输开销超过 GPU 加速收益。

```
Batch 大小 → GPU 加速比:
  小 batch (<1 MB):  GPU 开销 > CPU 直接 merge（传输占主导）
  中 batch (1-10 MB): GPU 与 CPU 持平
  大 batch (>10 MB): GPU 显著优于 CPU（计算占主导，摊销传输开销）
```

gLSM 的策略：
- 等待积累足够多的 SSTable 再触发 GPU compaction
- 小文件仍然走 CPU 路径（自适应决策）
- 可配置的 batch 大小阈值，根据 GPU 型号和 PCIe 带宽自适应

### 4. GPU 内存管理

| 挑战 | gLSM 方案 |
|------|----------|
| GPU 显存有限（16-80 GB HBM） | 分块加载，每次只加载部分 SSTable 的 chunk |
| 变长 key/value | GPU 上使用 offset 数组 + packed buffer 存储变长数据 |
| 输出结果大于输入（写放大） | 提前预估输出大小，流式写回 CPU 内存 |
| GPU OOM（Out of Memory） | 降级到纯 CPU compaction，保证不 crash |

**变长 key-value 的 GPU 内存布局**：

```
GPU Memory Layout:
  [key_offsets[N]] [key_data (packed)] [value_offsets[N]] [value_data (packed)]
       ↑ 定长数组         ↑ 变长数据          ↑ 定长数组          ↑ 变长数据
```

offset 数组方便 GPU threads 通过 `thread_id` 直接索引到具体 kv pair。

## 设计要点

### 整体架构

```
-----------------------------------------------------
|                    gLSM Engine                        |
|                                                       |
|  ----------   ----------   ---------------     |
|  | MemTable |--►| WAL/Log  |--►| Compaction    |     |
|  | (CPU)    |   | (CPU)    |   | Scheduler     |     |
|  ----------   ----------   ---------------     |
|                                         |             |
|                          --------------▼----------  |
|                          |   Compaction Router     |  |
|                          |   ------  ------    |  |
|                          |   | CPU  |  | GPU  |    |  |
|                          |   | Path |  | Path |    |  |
|                          |   ------  ------    |  |
|                          -------------------------  |
|                                           |           |
|                          ----------------▼--------  |
|                          |    GPU Pipeline          |  |
|                          |  Upload → Merge → Down   |  |
|                          -------------------------  |
-----------------------------------------------------
```

### Compaction Router 决策逻辑

```
if compaction_batch_size < GPU_THRESHOLD:
    → CPU merge path
elif GPU_memory_available < estimated_requirement:
    → CPU merge path (GPU OOM 保护)
elif key_type is not GPU_sortable:
    → CPU merge path (回退自定义 comparator)
else:
    → GPU merge path
```

### 自适应阈值

- `GPU_THRESHOLD` 默认 ~10 MB batch 大小
- 系统在运行中动态评估 GPU vs CPU 的实际吞吐量
- 如果 GPU 利用率持续低于阈值，自动回退 CPU

## 与其他硬件加速方案对比

| 维度 | gLSM (GPU) | FPGA 加速 | DPU/SmartNIC |
|------|-----------|----------|-------------|
| **加速目标** | Compaction（归并排序） | 特定数据路径（如哈希、压缩） | 网络 I/O / 存储协议卸载 |
| **并行度** | 数千核，数据级并行 | 流水线并行，自定义逻辑 | 专用数据通路 |
| **开发门槛** | 中等（CUDA/C++） | **高**（Verilog/VHDL） | 中等（P4/DPDK） |
| **部署成本** | GPU 服务器（已有 AI 基础设施可利用） | 定制硬件/FPGA 卡 | 专用网卡 |
| **灵活性** | ⭐⭐⭐⭐⭐ 通用可编程 | ⭐⭐ 硬件编程 | ⭐⭐⭐ 可配置 pipeline |
| **能效比** | ⭐⭐ 高功耗（~300-700W） | ⭐⭐⭐⭐ 低功耗 | ⭐⭐⭐⭐ 低功耗 |
| **延迟** | 中等（PCIe 往返 + GPU kernel） | **低**（无 PCIe 开销，inline 处理） | **极低**（数据路径内处理） |
| **适用场景** | 大规模集中 compaction | 实时流处理、过滤加速 | 存算分离网络层卸载 |
| **代表工作** | gLSM (ToS 2024) | 学术界 FPGA KV 原型 | DPFS/DPU-based storage |

> **核心结论**：GPU 适合**大规模批量合并**（计算密集型），FPGA 适合**inline 实时过滤**（低延迟流式），DPU 适合**网络/存储协议栈卸载**。三者不互斥，可组合使用。

## 局限性

### 1. PCIe 带宽天花板

- LSM-tree compaction 是**数据密集型**操作，吞吐受限于 PCIe 带宽
- GPU 计算再快，PCIe 传输瓶颈决定了整体加速比上限
- 实测中，小 SSTable 的 GPU compaction 甚至比 CPU 更慢

### 2. GPU 显存容量约束

- 单个 GPU 显存 16-80 GB，而大规模 LSM-tree 单次 compaction 可能涉及上百 GB 数据
- 分块处理引入额外的并发控制和调度开销
- 变长 key/value 进一步降低显存有效利用率

### 3. 不是所有 compaction 都适合 GPU

| 场景 | GPU 是否适合 |
|------|-------------|
| L0 → L1 compaction（小文件多） | ❌ 单个文件太小，传输开销大 |
| Lk → Lk+1 compaction（大文件少） | ✅ 数据量大，GPU 并行收益高 |
| 范围删除 (range delete) | ❌ 逻辑操作，不适合 GPU |
| 通用 comparator（非简单整数比较） | ❌ GPU 分支发散严重 |

### 4. 系统复杂度

- 需要维护两条 compaction 路径（CPU + GPU）及其自适应路由
- 错误处理和降级策略增加代码复杂度
- GPU 驱动/CUDA 版本依赖 → 部署灵活性降低
- 与 LSM-tree 现有特性（BlobDB、secondary index、WAL GC）的集成需要额外工程

### 5. 成本与利用率

- GPU 是昂贵的共享资源，如果只在 compaction 时使用，利用率低
- 生产环境中 GPU 往往已满载 AI 训练/推理任务
- 云环境中 GPU 实例比 CPU 实例贵 3-10 倍 → TCO 需要仔细评估

## 与其他 LSM 优化的关系

| 优化方向 | 关联概念 | gLSM 的影响 |
|----------|---------|------------|
| 合并性能 | [[LSM-Tree-合并优化]] — 流水线合并、VT-tree Stitching | gLSM 提供了**硬件维度的合并加速**，与流水线合并可叠加 |
| 硬件适配 | [[LSM-Tree-硬件适配]] — cLSM 多核、NoveLSM NVM | gLSM 填补了 **GPU 硬件适配**的空白 |
| 写放大 | [[LSM-Tree-写放大]] — Tiering/Leveling 策略 | GPU 加速让系统可以承受更激进的 leveling 策略（更好的空间利用率） |
| 自动调参 | [[LSM-Tree-自动调参]] — Dostoevsky 自适应合并 | GPU 路径选择是新的自动调参维度 |

## 未来展望

1. **CXL 共享内存**：CXL 3.0 共享 GPU 显存，消除 PCIe 数据拷贝——可能是 game changer
2. **多 GPU compaction**：利用 NVLink 互联的多 GPU 并行处理超大 compaction 任务
3. **GPU 与 KV 分离结合**：GPU 处理 key 归并，value 走独立 log 不参与合并（[[LSM-Tree-硬件适配]] § WiscKey）
4. **存算一体**：如果 SSD/NAND 内嵌计算单元，compaction 可以在存储层完成，无需搬数据

## 关键数字

| 指标 | 典型值 |
|------|--------|
| GPU compaction 加速比 | 2-8x（大 batch 场景，vs 单核 CPU） |
| CPU-GPU 数据传输开销 | ~0.5-2ms / GB（PCIe 4.0 x16） |
| GPU 归并排序吞吐 | 10-50 GB/s（HBM2e GPU） |
| 有效 batch 阈值 | >10 MB（低于此值 GPU 无优势） |
| GPU 功耗 | 300-700W（vs CPU ~200W） |

---

*论文: gLSM — GPU-Accelerated LSM-based Key-Value Store, ACM Transactions on Storage (ToS) 2024*
