# ai_wikis 维护入口

本仓库是公开技术知识库。操作知识库前先读 `知识库/purpose.md`、`知识库/schema.md`、`知识库/README.md` 和 `知识库/维护记录/待核验与知识缺口.md`，并读 `知识库/动态管理规则.md`；先用 `知识库/阅读优先级.md` 定位当前主入口，再按任务定位来源和相关页。执行步骤见 `团队规范/技术规范/ai-wiki-maintain-skill.md`。

- 本文件只约束这个仓库，不要求修改任何外部助手配置、任务或私人资料。
- 原始资料不改写；阅读分析和 Wiki 允许基于证据纠错。用户编辑、稳定路径、公开 URL 和同步清单必须保留。
- 摄取要更新关联概念及综述；查询中的可复用发现在授权范围内回写；结构 Lint 不能代替原文审阅。
- 社区 v2、confidence、实体 JSON 是可选扩展。不得机械打分、按年龄降级/遗忘，或把第三方实现当 Karpathy 官方规范。
- 禁止把私人对话、内部资料或凭据写进这个公开仓库。原文/PDF/译文的再分发许可单独核对。
- 本库使用 `README.md` 作总索引、`log.md` 作追加日志；新维护报告进入 `知识库/维护记录/`。
- 检查命令：`python3 scripts/lint_wiki.py`；检查器测试：`python3 -m unittest discover -s scripts -p 'test_lint_wiki.py'`。未运行或未覆盖的验证必须如实说明。
- 只提交明确改动的文件；不得 `git add -A`、强制重置用户改动、强推或自动新建同步任务。推送后核对远端；桌面 vault 同步另行检查。

## 动态维护执行

- 公开产物确实复用知识页后，使用 `scripts/manage_wiki.py record-use` 记录公开证据；不记录私人聊天或臆造访问次数。同一产物不同修订不能重复增加使用次数。
- 生命周期变化先审阅，再用 decision/restore 追加记录。reference/superseded/merged 只改变主入口投影并保留规范目标，不让脚本删除原件或正文。
- 摄取、查询沉淀或维护完成前运行 `python3 scripts/maintain_wiki.py --root .`，再运行同命令加 `--check`；完整测试为 `python3 -m unittest discover -s scripts -p 'test_*.py'`。检查与生成物差异同本次内容一起提交。
- 生成阅读排序不修改 confidence、技术审核状态或 source_checked；只在实际执行命令时更新，没有新增后台调度。
