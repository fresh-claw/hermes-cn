# 汉化范围审计

## 官方已覆盖

- `locales/zh.yaml`：审批提示与部分网关静态消息。

## 当前中文增强覆盖

- `hermes_cli/*.py`
- `cli.py`
- `run_agent.py`
- `agent/*.py`
- `gateway/run.py`
- `gateway/platforms/*.py`
- `tui_gateway/server.py`
- `ui-tui/src/**/*.ts`
- `ui-tui/src/**/*.tsx`
- `acp_adapter/*.py`
- `plugins/platforms/*`
- `plugins/image_gen/krea/plugin.yaml`
- `plugins/web/xai/plugin.yaml`

## 桌面版处理方式

Hermes Desktop 与 CLI/TUI 使用同一 Hermes 核心、配置、会话、技能和后端。当前最优策略是保留官方桌面安装包，再用一键安装器补核心中文内容。

不默认改官方 macOS/Windows 安装包，原因是官方安装包包含签名和自动更新链路。直接改包会增加启动失败和更新失效风险。

## 后续可增强

当官方桌面源码发布稳定 tag 后，可以基于源码构建未签名中文测试包，覆盖：

- `apps/desktop/src`
- `apps/desktop/electron`
- `apps/bootstrap-installer/src`
- `apps/shared/src`
