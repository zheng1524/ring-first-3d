# 一次性任务｜旧Codex创建独立GitHub仓库（不是科学执行Task）

## 授权范围
用户已决定：人工在RA、PM和Codex之间传递报告/任务；Codex负责Git增量上传；建立**新的私有** `zheng1524/ring-first-3d`，**版本冻结后再选择性上传原有三维科研资产**。不对现有`polyp-resarch`及`new-polyp-dxy`写入，不拷贝旧22GiB实验目录，不移动原始数据。

## 需要执行
1. 阅读本包`COLLAB_STANDARD_v1.3.md`，用只读命令复核旧审计现状；检查新库名是否已存在；记录旧root、HEAD、旧3D untracked/ignored范围和关键源资产哈希。当前审计参考：`/home/liu/polyp_research/ring_anchor_3d`，旧宿主HEAD为`4483e25...`，不能冒充新3D版本。
2. 创建独立目录`/home/liu/ring_first_3d/`和本地Git库（默认main）。**只把本包的`README.md`、`AGENTS.md`、`COLLAB_STANDARD_v1.3.md`、三个启动提示词、`.gitignore`和小清单纳入首次种子提交**。写`BOOTSTRAP_ONLY`，不要称为算法可复现基线。不要在旧3D目录内git init。
3. 检查`gh auth status`（不输出凭据）；若具备授权且目标库未存在，使用`gh repo create zheng1524/ring-first-3d --private --source=. --remote=origin --push`创建并推送；若鉴权或API失败，停止远端操作，告知用户在GitHub创建**空的私有仓库**，再按确认的远端地址推送；禁止改为旧仓库公开分支或强推。
4. 读回远端README和commit SHA，报告真实仓库地址、可见性、首次commit/branch、上传文件列表和失败。只有实际读回成功才标`REMOTE_BOOTSTRAP_PASS`。
5. 创建`BASELINE-3D-001`**迁移计划**但本次不得直接执行：列出最新Ring-First/HERO/点云/Mask/Mesher/Hull源码、运行依赖、复现命令与哈希，分离本地大工件；标注20261024 Hull已执行但未认证。待用户审批计划后，按显式文件清单将真正需要的历史3D源码和精选关键图表逐批迁移，完成独立重跑并标baseline tag。**不可整库镜像、复制老仓库main或覆盖旧研究文件。**

本轮只形成一个`BOOTSTRAP_REPORT.md`，简短报告实测通过项/失败项；禁止科研模型运行。

## 首次建库CLI示例（条件满足才运行）
```bash
mkdir -p /home/liu/ring_first_3d
cd /home/liu/ring_first_3d
# 从初始化包只复制允许的小文档，并明确检查它们后再运行：
git init -b main
git add README.md AGENTS.md COLLAB_STANDARD_v1.3.md PROMPT_RA.md PROMPT_PM.md PROMPT_CODEX.md BOOTSTRAP_OLD_CODEX.md BASELINE_IMPORT_CHECKLIST.md HANDOFF_TEMPLATE.md PACKAGE_MANIFEST.json .gitignore
git diff --cached --stat
git commit -m 'chore: bootstrap ring-first 3d collaboration v1.3'
gh auth status
gh repo create zheng1524/ring-first-3d --private --source=. --remote=origin --push
```
如果最后一步失败，保留本地提交，不重复使用不同库名创建远端，不清理现有文件；向用户报告错误与最短人工操作。
