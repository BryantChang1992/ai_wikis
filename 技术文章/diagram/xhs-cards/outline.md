# Xiaohongshu Infographic Series Outline

---
strategy: b
name: Information-Dense
style: notion
default_layout: dense
palette: macaron
image_count: 6
generated: 2026-06-13 23:30
---

## Image 1 of 6

**Position**: Cover
**Layout**: sparse
**Hook**: AI大模型公司的秘密武器
**Slug**: ai-data-pipeline-cover
**Filename**: 01-cover-ai-data-pipeline.png

**Text Content**:
- Title: 「AI吃的不是数据」
- Subtitle: 是经过管道的"营养液"
- Tag: 技术干货 · 数据工程

**Visual Concept**:
中心是一个管道/漏斗形状，左边是混乱的原始数据（几何碎片），右边是整齐的数据流输入GPU芯片。
手绘线条风格，macaron 柔和配色，大量留白，标题醒目。
管道元素暗示数据流水线。

**Swipe Hook**: 完整架构图见下一张👇

---

## Image 2 of 6

**Position**: Content
**Layout**: dense
**Core Message**: AI训练数据管道全景架构
**Slug**: pipeline-architecture
**Filename**: 02-content-pipeline-architecture.png

**Text Content**:
- Title: 「AI训练数据管道」
- Subtitle: 从原始数据到 GPU 的六层架构
- Points:
  - ① 数据源层：SDK埋点 + 日志 + 第三方API + 爬虫
  - ② 消息队列层：Kafka · 千万QPS · 持久化日志
  - ③ 流批一体清洗层：Flink · 校验/去重/脱敏/归一
  - ④ 存储+特征工程层：Iceberg/Hudi · 数据湖 · Point-in-Time Join
  - ⑤ 训练供给层：数据分片 · 预取缓存 · 列式存储
  - ⑥ GPU训练集群：H100 × N · 万亿参数
  - ⚠ 关键：GPU 空转 1 小时 ≈ 557 美元

**Visual Concept**:
自上而下的六层架构图，每层一个色块区域，层间用箭头连接。
notion 风格手绘线条，macaron 配色（奶油底色+柔和蓝/紫/绿分区）。
底部红色高亮 "GPU 空转 1 小时 = $557" 作为警示。

**Swipe Hook**: 管道出问题模型就"智障"了👇

---

## Image 3 of 6

**Position**: Content
**Layout**: dense
**Core Message**: 特征穿越——最隐蔽的数据毒药
**Slug**: feature-leakage
**Filename**: 03-content-feature-leakage.png

**Text Content**:
- Title: 「特征穿越」
- Subtitle: Feature Leakage — 最隐蔽的数据毒药
- Points:
  - ⚠ 什么是特征穿越：训练样本无意中使用了"未来信息"
  - 💥 真实案例：SQL join 条件时区错误 → 特征窗口漂移 24 小时
  - 📊 症状：训练集准确率 94% → 上线 2 周后完全失效
  - 🔍 根本原因：时间戳处理不一致（UTC vs 本地时区）
  - 🛡️ 防护：Point-in-Time Join · 时间窗口强制校验
  - 📌 铁律：每一条样本都要有精确的时间锚点

**Visual Concept**:
时间线图示：左边"过去"的样本用正常标签，右边"未来"的数据不该出现在特征中，但箭头错误地穿越了时间边界。
红色警示标记穿越点，notion 手绘风格，macaron 底色配红色高亮警告区域。

**Swipe Hook**: 还有一个更致命的问题👇

---

## Image 4 of 6

**Position**: Content
**Layout**: dense
**Core Message**: 数据延迟——GPU 饥渴，烧钱如流水
**Slug**: gpu-starvation
**Filename**: 04-content-gpu-starvation.png

**Text Content**:
- Title: 「GPU Starvation」
- Subtitle: 数据供给慢 1 秒，烧掉多少美元？
- Points:
  - ⚡ GPU 训练像赛车引擎，数据是燃料
  - 💸 H100 集群空转 1 小时 = ~557 美元/卡 × N 卡
  - 🔗 瓶颈来源：DataLoader 慢 · 网络 I/O 拥塞 · 解码耗时
  - 📦 解决方案：本地 SSD 预取 · 列式存储 Parquet/Lance · NVIDIA DALI
  - 🎯 目标：GPU 利用率 > 95%，数据等待时间 < 10% 训练步长
  - 📉 现实：很多团队 GPU 利用率只有 40-60%

**Visual Concept**:
左边一个满负荷运转的 GPU 芯片（绿色），右边一个空转等待的 GPU（红色），中间是断裂的数据管道。
管道断裂处有倒计时钞票飞走的图标。macaron 底色 + 红色警示区。

**Swipe Hook**: 数据质量本身也在悄悄塌缩👇

---

## Image 5 of 6

**Position**: Content
**Layout**: dense
**Core Message**: 数据漂移与质量塌缩——温水煮青蛙
**Slug**: data-drift
**Filename**: 05-content-data-drift.png

**Text Content**:
- Title: 「数据漂移 & 质量塌缩」
- Subtitle: 温水煮青蛙，发现时已来不及
- Points:
  - 📉 数据漂移：上游数据分布随时间缓慢变化
  - 🔄 线上 vs 离线数据偏差持续扩大（KL 散度 ↑）
  - ⏰ 凌晨3点行情数据停更 · 节假日用户行为突变 · 新版本协议不兼容
  - 📊 监控体系：Schema 一致性 · 数据量波动 · 分布漂移检测
  - 🚨 告警阈值：空值率 > 5% · 分布 P 值 < 0.01 · 延迟 > 30min
  - 💡 "管道就是模型的一部分"——数据质量问题 = 模型质量问题

**Visual Concept**:
一条逐渐变形的水管，左边是正常流动的数据流，右边逐渐扭曲、堵塞。
上方有监控仪表盘和告警指示灯。macaron 柔和底色，蓝紫灰渐变表示劣化过程。

**Swipe Hook**: 最后一句话总结👇

---

## Image 6 of 6

**Position**: Ending
**Layout**: sparse
**Core Message**: 管道即护城河
**Slug**: pipeline-moat
**Filename**: 06-ending-pipeline-moat.png

**Text Content**:
- Title: 「管道即护城河」
- Subtitle: Pipeline is the moat
- Points:
  - 大模型公司砸几百亿买算力
  - 但真正拉开差距的是数据管道
  - 好的管道让每一分算力都花在刀刃上
- CTA: 转发给做数据/ML的同学 | 评论区聊聊你的管道踩过什么坑？

**Visual Concept**:
中心是一座城堡（模型）被护城河（数据管道）环绕。管道中流动着彩色数据流。
城堡上方有盾牌图标。底部 CTA 文字 + 互动引导。
macaron 柔和底色，notion 手绘风格，温暖收尾。

---
