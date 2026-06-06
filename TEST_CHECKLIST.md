# TEST_CHECKLIST — MCP Server 烟雾测试

> **目的**: 任何代码变更后，通过 stdio 实际调用 MCP Server 逐项验证。
> **方法**: 启动 server.py → AI 通过 MCP 工具调用 → 逐项检查返回值。
> **覆盖**: 3 跑团工具 + 分层搜索 + 扩展管理链路

---

## roll（骰子工具）

| # | 测试场景 | 输入 | 验证 |
|---|---------|------|------|
| 1 | 标准 d10 | `1d10` | 1-10 |
| 2 | 多骰 d6 | `3d6` | 3-18 |
| 3 | 带正修正 | `1d10+5` | 6-15 |
| 4 | 带负修正 | `2d6-3` | -1~9 |
| 5 | d100 | `1d100` | 1-100 |
| 6 | d% 简写 | `d%` | 1-100 |
| 7 | 无效表达式 | `abc` | error 返回 |

---

## search_rules（规则检索）

| # | 测试场景 | 输入 | 验证 |
|---|---------|------|------|
| 8 | 精确匹配 | `query="气手枪"` | 命中 1 条，equipment |
| 9 | 模糊包含 | `query="伤害"` | 多条命中，跨分类 |
| 10 | 分类过滤 | `query="手枪", category="equipment"` | 全部 equipment |
| 11 | 空查询拦截 | `query=""` | error 返回 |
| 12 | 无效分类 | `query="test", category="xxx"` | error + 有效分类列表 |
| 13 | 无匹配 | `query="xyz不存在的词"` | 0 条，非 error |
| 14 | 7 分类均可达 | 分别过滤 7 分类 | 每个分类有 >0 条 |

### 分层搜索（需预先导入扩展）

| # | 测试场景 | 验证 |
|---|---------|------|
| 15 | core 命中 | 查询 core 专属内容 |
| 16 | 扩展命中 | 查询扩展专属内容 |
| 17 | user 层命中 | 查询 user.json 中记录 |
| 18 | Replace 遮蔽 | 扩展覆盖 core 同 id → 返回扩展版，不返回 core 版 |
| 19 | 禁扩展后回退 | 禁用扩展 → 同 id 回到 core |
| 20 | source 标签 | 每条结果带 `_source` / `_source_file` |

---

## roll_table（随机表）

| # | 测试场景 | 输入 | 验证 |
|---|---------|------|------|
| 21 | 精确表名 | `"动词"` | 命中，带骰值+结果 |
| 22 | 模糊匹配 | `"住房"` | 命中或返回建议 |
| 23 | 表不存在 | `"不存在的表"` | error |
| 24 | 手动骰值 | `table_name="动词", roll_value=50` | 50 对应行 |
| 25 | 神谕 50/50 | `"神谕 50/50"` | d100 出目 + 结果 + range |
| 26 | 神谕必然 | `"神谕 必然"` | d100 + 大概率"是" |
| 27 | 神谕不可能 | `"神谕 不可能"` | d100 + 大概率"否" |
| 28 | 士气表 | `"士气"` | 列出 5 种敌人类型 |
| 29 | 偏移量计算 | `"动词"` 指定骰值 | result_index / min / max 正确 |

---

## 数据管理工具链路（已从跑团 MCP 移除，归档于 mcp_admin/）

> **注意**: v3.1 跑团 MCP 只有 3 个只读工具。管理工具待备团 MCP 重新实施。
> 以下为 **v2 测试记录保留**，备团 MCP 实施后更新。

| # | 测试场景 | 输入 | 验证 |
|---|---------|------|------|
| 30 | list_sources | 无参 | core + user 在列表中，优先级正确 |
| 31 | set_source_priority 禁用 | `source="user", enabled=False` | user 禁不掉（保护） |
| 32 | set_source_priority core | `source="core"` | core 禁不掉（保护） |
| 33 | prepare_extension (JSON) | 指向有效 JSON | 返回摘要 |
| 34 | prepare_extension (不存在) | 无效路径 | error |
| 35 | import_extension extend | 导入新包 | 写盘 + source_config 更新 |
| 36 | import_extension override | 同名导入 | 覆盖 |
| 37 | remove_extension core | `source="core"` | 拒绝 |
| 38 | remove_extension user | `source="user"` | 拒绝 |

---

## 端到端链路

| # | 测试场景 | 验证 |
|---|---------|------|
| 39 | 导入→检索→禁用→检索 | 扩展导入后 search_rules 命中 → 禁用扩展 → 不再命中（或回退 core） |
| 40 | 随机表手动骰值→偏移 | `roll_table("动词", roll_value=50)` → result_index 用于后续偏移计算 |
| 41 | 神谕链路 | `roll_table("神谕 50/50")` → AI 根据结果叙事 → 叙事后再次检定 |

---

## 使用方式

```bash
# 1. 启动 MCP Server
cd C:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP\mcp_server
C:\Users\Administrator\miniconda3\python.exe server.py

# 2. AI 通过 MCP 协议逐个调用工具
# 3. 逐项勾选本清单，记录失败项

# 验证后更新:
#   - 所有 PASS → 记录日期
#   - 有 FAIL → 在下方记录失败项及日志
```

---

## 执行记录

| 日期 | 执行者 | 版本 | 结果 | 备注 |
|------|--------|------|------|------|
| 2026-05-07 | Claude | v2 | 41/41 | 首次烟雾测试（测试文件已删） |
| - | - | - | - | - |

---

## 失败记录

> 记录格式: `[日期] #用例号 - 失败描述 - 日志摘要`
