---
type: concept
title: AutoMQ WAL 双布局升级与回滚边界
sources:
- '[[技术文章/博客同步/stream-storage-observer-2026-10-16]]'
- https://github.com/AutoMQ/automq/pull/3657
tags:
- 分布式系统
- 存储
created: '2026-10-17'
updated: '2026-10-17'
status: draft
related:
- '[[技术文章/博客同步/stream-storage-observer-2026-10-16]]'
---

# AutoMQ WAL 双布局升级与回滚边界

## 问题与机制
对象键前缀分片改变 WAL 对象布局；滚动升级时新旧读者和存量对象并存。先让全部节点具备双读能力、仍写旧布局，再切 version=1 写分片布局。切回 version=0 只改变后续写入，不会清除已存在的新布局对象。

## 取舍与限制
兼容能力必须覆盖整个对象留存期，不能把配置回退等同二进制可安全降级。移除 feature gate 后更依赖部署顺序约束。作者报告布局、恢复、trim 等测试，但未给 live S3 请求率/SlowDown 基准，不能推导生产性能收益。

## 阶段
截至 2026-10-16 报告窗口，代码合并及 nightly 集成与正式版本发布分开；新正式版本未确认。

本页从既有公开精读/观察报告提炼；不表示本次重新核读全部上游或运行实验。证据有效日期见来源报告。
