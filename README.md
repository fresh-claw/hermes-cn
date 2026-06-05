# Hermes Desktop 中文增强包

面向 Hermes Desktop、Hermes Agent TUI 和 CLI 的中文增强入口。

官网入口：<https://useai.live/hermes/>

## 一键安装

Windows PowerShell：

```powershell
irm https://cdn.jsdelivr.net/gh/fresh-claw/hermes-cn@main/install.ps1 | iex
```

macOS / Linux / WSL2：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/fresh-claw/hermes-cn@main/install.sh | bash -s -- --include-desktop
```

macOS 也可以下载 `install.command` 后双击执行。

## 平台策略

| 平台 | 推荐方式 | 说明 |
| --- | --- | --- |
| Windows | PowerShell | 补官方桌面端，再调用中文增强安装器 |
| macOS | Bash 或 `install.command` | 生成官方 Hermes.app，再补中文增强 |
| Linux | Bash | 生成官方桌面端，再补中文增强 |

## 翻译范围

- 官方语言配置：`display.language=zh`
- CLI：`hermes_cli/*.py`
- TUI：`ui-tui/src/**/*.ts`、`ui-tui/src/**/*.tsx`
- 网关：`gateway/platforms/*.py`
- ACP：`acp_adapter/*.py`
- 平台插件：`plugins/platforms/*`
- 桌面版关联：官方桌面 App 共享同一 Hermes 核心、配置、会话、技能和 TUI 后端

## 不改的内容

- 模型生成内容
- 第三方工具返回文本
- 用户文件
- API Key
- 官方安装包签名

## 版本

- 桌面入口：2026.06.05.2
- 中文包：2026.05.29.1
- 官方 Hermes Agent：v0.15.2

## 上游

Hermes Agent 是 NousResearch 的 MIT 开源项目：<https://github.com/NousResearch/hermes-agent>
