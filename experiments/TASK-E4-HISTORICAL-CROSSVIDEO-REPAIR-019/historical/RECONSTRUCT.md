# 历史回放目录重建

完整的 019/020 回放树（94 MB，含 1.8 MB×2 的 observations JSON 与全部历史 metrics）**未纳入 Git**，
因为它完全可由历史提交重建：

```bash
git fetch origin 5636aaebd61a3d53b69f528692c4c7095df46508
git worktree add --detach /tmp/rf019 5636aaebd61a3d53b69f528692c4c7095df46508
mkdir -p historical/replay_G01 && cd historical/replay_G01
git -C /tmp/rf019 archive 5636aaebd61a3d53b69f528692c4c7095df46508 \
  experiments/TASK-E4-RING-POLYP-REGISTRATION-019 \
  experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020 | tar -x
# 恢复历史软链接（020 -> 019）
ln -sfn ../../TASK-E4-RING-POLYP-REGISTRATION-019/landmarks/CROSS_004.npz \
  experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020/landmarks/CROSS_004.npz
```

`symlink -> ../../TASK-E4-RING-POLYP-REGISTRATION-019/...`（相对路径，从 `020/landmarks/` 上两级）。
验证：`resolve()` 指向 019 原件、SHA256 `1839a9fc8f948b79…`、153 个地标。

`source_subset/` 保留了本轮实际执行过的关键源码副本与 RANSAC 输出，便于不联网时核对。
