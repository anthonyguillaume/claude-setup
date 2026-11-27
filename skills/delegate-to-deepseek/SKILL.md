---
name: delegate-to-deepseek
description: Delegate mechanical, LOW-CONTEXT work units to DeepSeek (translations, isolated CRUD, docs, short scripts, lint fixes, test-run summaries, read-only scans) and verify the result independently. Never auth, authorization, data isolation, audit, crypto, secrets, architecture or final review. Skip when DEEPSEEK_MODE=off.
---

# delegate-to-deepseek - 主 Agent 派工准则

“主 Agent”指负责决策、整合与最终验收的上层 agent。

## 1. 不可突破的边界

- 用户显式要求派 / 不派、指定执行者或执行方式时，优先服从用户。
- 权限、安全、隐私、敏感信息和非授权写入边界不可绕过。
- `DEEPSEEK_MODE=off` 时不要派工。
- DeepSeek 读取的文件内容会发送到配置的 API endpoint；敏感工作区不得派工。
- coding 能力固定为 Read / Write / Edit / Bash / Glob / Grep / NotebookEdit；readonly 固定为 Read / Glob / Grep。不得通过 task、steering 或其它参数提权。
- coding Bash 是受边界约束的 trusted-host Bash，不是操作系统级沙箱。
- 派工结果必须由主 Agent 独立验证，失败由主 Agent 收口。
- 出现文件 mutation、取消、断连或 MCP 重启后，先调用 `get_deepseek_recovery()`，核验实际文件，再用精确 transaction IDs 调用 `acknowledge_deepseek_mutations(...)`；未确认前不要重试 mutation delegation。

## 2. API 选择

| 需求 | API |
|---|---|
| coding，直接等结果 | `delegate_to_deepseek(task, context="", model="flash")` |
| 纯静态文件分析，直接等结果 | `delegate_to_deepseek_readonly(task, context="", model="flash")` |
| coding，需要 steering / status / cancel | `start_deepseek(task, context="", model="flash")` |
| readonly，需要 steering / status / cancel | `start_deepseek_readonly(task, context="", model="flash")` |
| 查询后台任务 | `get_deepseek_status(job_id)` |
| 追加/修正后台指令 | `send_deepseek_message(job_id, message)` |
| 取消后台任务 | `cancel_deepseek(job_id)` |
| 获取最终结果 | `get_deepseek_result(job_id)` |
| 查询 mutation recovery | `get_deepseek_recovery()` |
| 确认已核验 mutation | `acknowledge_deepseek_mutations(transaction_ids)` |

只读、搜索、review 已存在文件且整个任务不执行命令/写文件时用 readonly；其余或不确定时用 coding。readonly job 后续需要 Bash 或写文件时，结束/取消后重新启动 coding job，不能 steering 提权。

## 3. 模型路由

`model` 只允许 `flash` 或 `pro`；不传时使用 `flash`。

- **Flash**：默认通用子代理，约 **Sonnet / Terra 档**。用于正常 coding、review、调查、重构、测试、批处理和常规多文件任务。
- **Pro**：困难任务子代理，约 **Opus / Sol 档**。用于复杂 debugging、架构级推理、困难多文件推理，或 Flash 已明显不足后的升级。
- 没有明确困难信号时保持 Flash；不要因为 Pro 可用就默认 Pro。
- 主 Agent 只选择 `flash/pro`，不要尝试控制 reasoning effort；thinking 档位由用户配置决定。
- background job 启动时冻结模型、reasoning effort 与能力。需要换模型时结束/取消当前 job，再新建 job。

## 4. 默认派工策略 (ai-team: faible contexte uniquement)

Règle ai-team, prioritaire sur l'ancienne version de cette section (voir aussi `rules/team.md` du plugin ai-team).

**Déléguer à Flash, seulement si la tâche demande peu de contexte :**

- traductions, extraction, renommages en lot sur des fichiers listés
- CRUD isolé, un composant ou un endpoint dont tous les fichiers sont donnés
- documentation, scripts courts, correctifs de lint
- exécution d'une suite de tests et résumé des échecs
- scans et inventaires en lecture seule (readonly)

**Ne jamais déléguer :**

- authentification et session, autorisation et isolation des données, audit
- cryptographie, secrets, gestion de clés
- architecture, choix techniques, arbitrages entre règles, revue finale
- toute tâche qui oblige DeepSeek à lire beaucoup de code : son MCP fait grossir le budget au carré de l'historique et il échoue (leçon de bricktales, 2026-10-15)

**Reste chez Claude :** ce qui précède, les micro-changements, les causes racines incertaines, ce qui dépend du CLAUDE.md ou de conventions non transmises. En cas de doute, la tâche reste chez Claude.

## 5. 派工时机

尽量在主 Agent 大量读取项目源码之前决定是否派工，避免主 Agent 和 DeepSeek 重复加载同一批上下文。

派工决策前优先使用 Glob / LS / 目录树、只读 Bash（如 `ls`、`find`、`wc -l`、`git status`）和必要的外部 WebSearch / WebFetch。避免仅为了决定“要不要派”而先 Read/Grep 大量源码；若主 Agent 已经拥有相关上下文，直接利用即可。

## 6. 派工粒度

优先派**完整逻辑单元**，不要把一个 feature 拆成大量微任务。合适的单元应尽量满足：目标清晰、输入/输出边界明确、可独立验证、所需 context 能一次性给齐。

主 Agent 负责识别单元、定义接口和最终整合；DeepSeek 负责单元内部的 Read / Implement / Test 循环。如果子任务必须频繁回来询问主 Agent 或依赖前一个子任务的临时结果，通常应合并。

## 7. task / context 怎么写

DeepSeek 看不到主对话历史、主 Agent 私有记忆或未显式提供的项目约定。调用时给足完成任务所需的信息，但不要放 API key、凭证或不应发送到外部 API 的敏感数据。

`task` 至少写清：目标、范围/路径（已知时）、边界、可验证成功标准。

`context` 只补必要信息：技术栈/版本、命名/schema/接口约定、已知项目规则、外部文档关键结论、已知坑或失败现象。

普通任务省略 `model`；困难任务明确升级：

```text
mcp__deepseek__delegate_to_deepseek(
  task="<目标 + 范围 + 成功标准>",
  context="<必要上下文>",
  model="pro"  # 普通任务删除此行，默认 Flash
)
```

## 8. 外部知识 pre-flight

DeepSeek 没有 web 工具。任务依赖最新或不熟悉的框架/API、小众依赖、协议/spec、SaaS API、错误码或 breaking change 时，主 Agent 先查官方/可靠资料，把**摘要**放进 `context` 再派工。常识性内容无需额外搜索。

## 9. 派工后验收

DeepSeek 自报完成不等于完成。主 Agent 至少：

1. 查看关键 diff / 产物。
2. 检查 schema、接口、边界和数量级。
3. 能运行测试/静态检查时运行。
4. mutation 任务按 recovery 协议核验并 acknowledge。

小问题主 Agent 直接修；明显遗漏但仍适合委派时给明确反馈重试；Flash 能力不足可新建 Pro 任务；大范围错误、权限问题或连续失败则停止派工并接管。

## 10. Fallback 与用户控制

| 情况 | 处理 |
|---|---|
| MCP / API 未配置或不可用 | 主 Agent 接管 |
| capability/tool not allowed | 不绕过权限；接管或让 operator 调整配置 |
| busy / workspace already owned | 处理现有 job 后再派，不并发写同一 workspace |
| 超 max_turns / 任务过大 | 按独立逻辑单元拆分 |
| Flash 质量不足 | 验证后新建 Pro 任务 |
| 连续两次质量差 | 本会话停止主动派工 |
| 用户说“派给 DS / DeepSeek”或 `/ds` | 强制派，默认 Flash；明显困难可 Pro |
| 用户说“你自己干 / 别派” | 不派 |
| `DEEPSEEK_MODE=off` / pure 模式 | 不派 |
