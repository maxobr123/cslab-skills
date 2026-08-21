---
name: cslab-modulet-api
description: Use when CSLab module templates must be queried or changed over HTTP. Covers credential-gated login and refresh, template discovery and detail, backend variable verification, pyTemp generation, and authorized CRUD without exposing credentials.
---

# CSLab moduleT 模板接口

模板详情是模块属性、节点、`startFun` 和算法槽位的当前事实源。仅在开发任务确实需要后台
事实或开发者要求操作模板时使用本 Skill；普通代码阅读和已有本地资料查询不索取凭据。

## 访问门禁

1. 当前任务没有有效短期令牌或开发者明确提供的账号密码时，先说明服务器、目的及读写
   范围，再请求凭据；当前任务已提供时不重复询问。
2. 账号密码只授权登录，不授权新增、修改或删除模板。任何写操作都要另行确认目标、完整
   payload、影响和写入权限。
3. 凭据和令牌仅存当前进程内存，不写入 Skill、源码、配置、临时文件、日志、Shell 历史
   或 Git，也不在输出中展示。
4. 默认直接 HTTP 登录和调用 API；只有正式 HTTP 契约不可用、需要人工认证或开发者明确
   要求时才使用 UI。不得绕过验证码、MFA 或 SSO。
5. 模板详情 GET 可能执行归一化回写，只请求必要次数并在内存整理，不反复调用。

## 按需读取

| 当前任务 | 必须读取 |
|---|---|
| 登录、刷新、401/过期处理、并发请求 | [`references/auth-and-token.md`](references/auth-and-token.md) |
| 查询设备类型、模板列表/详情、解析属性节点和算法映射 | [`references/template-query-contract.md`](references/template-query-contract.md) |
| 新增后台变量、生成 pyTemp、POST/PUT/DELETE | [`references/template-maintenance.md`](references/template-maintenance.md) |
| 查询或取得新的后台模板变量 | [`references/backend-template-variables.md`](references/backend-template-variables.md) |

不要为一次任务默认读取全部 reference。当前模板的实际详情优先于历史目录；历史目录中的
同名冲突必须按模板范围保留，不能由 Agent 自行统一。

## 最短查询流程

1. 完成凭据门禁并按 `auth-and-token.md` 取得令牌。
2. 用列表接口收集全部匹配候选；多个候选交由开发者选择。
3. 只对选定模板读取详情，核对 `startFun`、四个算法槽位、`moduleProp` 和 `moduleNode`。
4. 报告变量名、含义、类型、默认值、方向、单位、shape、节点方向及当前待确认项。
5. 将详情 API 证实的新变量补入后台变量目录；不得把列表摘要或 Agent 推断写成事实。

## 新变量与写入门禁

算法需要 Skill 和模板中都不存在的契约变量时，先提醒开发者完成后台配置，并展示变量名、
类型、含义、作用、单位、shape、方向、数据来源、消费者和适用模板。详情 API 复核通过前
不得用于编码。禁止用 `**kwargs`、硬编码默认值、临时属性或未登记节点绕过模板。

Agent 代写后台前，开发者必须理解并明确同意技术方案，同时明确授权目标模板和完整
payload。写入成功响应不能代替详情 API 复核。

## 完成门禁

- 没有输出账号、密码、token、rtoken 或完整鉴权响应。
- 模板候选由开发者选择，算法路径、类名与 `startFun` 已核实。
- 属性和节点字段均来自详情响应，当前值与下拉候选没有混淆。
- 新增或修改内容经过详情 API 逐字段复核并同步变量目录。
- 未把网页服务器运行结果当成本地 `.py` 已加载的证据。
