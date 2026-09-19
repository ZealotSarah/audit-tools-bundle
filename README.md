# 飞检工具包

本项目用于统一打包和启动以下三个 Windows 本地飞检工具：

- 病历自动抽取工具
- 基金金额自动测算工具
- 文件批量编码工具

当前版本已经建立单窗口三标签页外壳。三个组件的业务源码和版本独立保存，病历抽取、基金测算以及实际文件重命名均通过独立 Worker 进程执行。设计基线、架构边界、迁移顺序和验收标准见 [整合包设计文档](docs/整合包设计文档.md)。

V0.3.0 起界面按 14 寸 Windows 笔记本适配：窗口使用任务栏之外的可用工作区，三个标签页支持小屏幕纵向滚动，文件批量编码页在内容过宽时同时支持横向滚动。

V0.4.0 已同步基金金额测算工具 V1.0.0：结果包含“人次”，保留公式缓存与保存校验，并支持“两项同时收取”及四种同时口径。

病历自动抽取 V1.9 与基金金额测算更新记录见 [两个工具更新整合计划](docs/两个工具更新整合计划_2026-09-14.md)。

## 开发运行

```powershell
python -m pip install -r requirements-build.txt
python run.py
python -m pytest -q
```

执行 `scripts\build_release.ps1` 可运行测试并构建 `onedir` 发布目录。安装 Inno Setup 6 后，执行 `scripts\build_installer.ps1` 可进一步生成 Windows 安装程序；`scripts\smoke_installer.ps1` 用于验证静默安装、程序启动、Worker 和卸载。

## Git 远端

项目通过 SSH 连接 GitHub：

```text
git@github.com:ZealotSarah/audit-tools-bundle.git
```
