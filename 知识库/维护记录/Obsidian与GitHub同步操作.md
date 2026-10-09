# Obsidian 与 GitHub 同步操作

适用于用户实际 Obsidian vault 的 Git checkout。GitHub 的更新和云端校验不证明桌面文件已更新；不能用新的云端 clone 代替桌面检查。

## 检查身份与工作区

1. 确认 Obsidian 当前打开的 vault 路径与 Git 仓库根；核对 `git remote -v` 是否对应 `BryantChang1992/ai_wikis`，查看当前分支，不默认把别的 vault 当目标。
2. 读取 `git status --short` 和 `git diff`/已暂存 diff，保留用户未提交修改及 `.obsidian` 个性设置。不要运行 reset --hard、clean 或自动 stash 后遗忘。
3. `git fetch origin` 后读取 `git rev-parse HEAD`、`git rev-parse origin/master` 和 `git rev-list --left-right --count HEAD...origin/master`。比较的是实际本地与新取回的远端，而非旧缓存。

## 根据状态处理

- 工作区干净、仅落后：在确认目标分支正确后执行 `git merge --ff-only origin/master`。
- 本地领先或双方分叉：先列出双方提交与差异，保留用户提交，按本次授权合并；无法安全判定的内容冲突交给用户，不强推。
- 工作区有修改：先展示重叠文件；不要覆盖或把所有私有内容提交到公开仓库。使用明确路径和可恢复的保存方式，冲突处理后复查。
- fetch/auth/连接失败：记录具体失败与上次可核验状态，不能宣称已同步。

## 完成验证

同步后重新读取远端与本地 HEAD、ahead/behind 和工作区状态，检查本次关键文件实际内容。在 Obsidian 中确认打开的是该 vault；若有未提交的用户笔记，说明“提交一致但工作区仍有本地修改”，不能称全部文件一致。Git 忽略文件不在远端同步保证内。

本流程不安装或启用后台同步插件、守护进程或定时任务。持续同步若需要新配置，须另行明确范围。不要向公开库写本机路径、账户、凭据或私人笔记。
