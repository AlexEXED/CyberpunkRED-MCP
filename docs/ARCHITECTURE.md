# Cyberpunk RED MCP Server — 完整设计方案

> 版本: 1.0 | 日期: 2026-05-04 | 状态: 待实现

---

## 目录

1. [概述](#1-概述)
2. [技术背景：什么是 MCP Server](#2-技术背景什么是-mcp-server)
3. [项目结构](#3-项目结构)
4. [数据层设计](#4-数据层设计)
    - 4.1 [规则数据（rules/）](#41-规则数据-rules)
    - 4.2 [随机表数据（random_tables/）](#42-随机表数据-random_tables)
    - 4.3 [索引文件](#43-索引文件)
    - 4.4 [加载策略](#44-加载策略)
5. [工具接口规范](#5-工具接口规范)
    - 5.1 `roll` — 通用骰子
    - 5.2 `search_rules` — 规则速查
    - 5.3 `roll_table` — 随机表掷骰
6. [模块划分与职责](#6-模块划分与职责)
7. [实施路线图](#7-实施路线图)
8. [边界与约束](#8-边界与约束)
9. [附录 A — 数据源实录](#附录-a--数据源实录)
10. [附录 B — 随机表分类方案](#附录-b--随机表分类方案)

---

## 1. 概述

在本地搭建一个 **Python MCP Server**，通过 stdio 协议与 WorkBuddy（或任意 MCP 客户端）通信，为赛博朋克 RED 单人/主持游戏提供两类工具：

### 跑团工具（日常使用）

| 工具 | 用途 | 数据依赖 | 使用频次 |
|------|------|----------|---------|
| `roll` | 掷骰子 | 无 | 高频（纯计算） |
| `search_rules` | 规则速查 | 7分类 486条 | 按需 |
| `roll_table` | 随机表掷骰 | 37表 + 神谕 + 士气 | **每轮必用** |

### 数据管理工具（维护使用）

| 工具 | 用途 | 触发场景 |
|------|------|---------|
| `prepare_extension` | 预处理第三方文档（PDF/Word/Excel） | 导入前的文件提取 |
| `import_extension` | 导入经审核的扩展包 | 确认后执行导入 |
| `list_sources` | 查看已加载的数据源层级 | 排查/审计 |
| `set_source_priority` | 设置规则优先级 | 切换 core/solo/third_party 覆盖关系 |

**核心设计原则**：
- 启动即全部加载到内存（数据总量 ~297KB）
- 零外部网络依赖，完全离线可用
- 基于成熟开源方案：**FastMCP 3.x**（MCP 框架）+ **dice 4.0**（骰子引擎）
- 数据预构建为 JSON，不运行时解析任何 Markdown
- **三层规则模型在工具层强制执行**，不依赖人工记忆

---

## 2. 技术背景：什么是 MCP Server

### 2.1 MCP 协议是做什么的

**Model Context Protocol (MCP)** 是 AI 应用调用外部工具的标准化协议。类比：

- 就像 USB 定义了外设如何连接电脑，MCP 定义了 AI 如何连接工具
- WorkBuddy 是 MCP **客户端**（内含腾讯文档 MCP、文件 MCP 等）
- 我们写的是 MCP **服务端**，给 WorkBuddy 添加「赛博朋克专用」的能力

### 2.2 我们选择的通信方式：stdio

```
WorkBuddy (MCP Client)  ──[stdio stdin/stdout]──>  Python 进程 (MCP Server)
```

优点：
- **零配置**：WorkBuddy 负责启动 Python 进程，不需要管理端口
- **自动生命周期**：WorkBuddy 关闭时进程自动终止
- **最短路程**：同一台机器，没有网络延迟

### 2.3 如何注册到 WorkBuddy

WorkBuddy 的 MCP 配置文件（`.workbuddy/mcp.json` 或全局配置）中添加一条记录：

```json
{
  "mcpServers": {
    "cyberpunk-red": {
      "command": "python",
      "args": ["C:/Users/Administrator/WorkBuddy/CyberpunkRED/mcp_server/server.py"],
      "cwd": "C:/Users/Administrator/WorkBuddy/CyberpunkRED/mcp_server"
    }
  }
}
```

之后 WorkBuddy 会自动启动 `server.py`，通过 `list_tools()` 注册的所有工具将出现在所有对话中，AI 可以像调用腾讯文档 MCP 一样调用它们。

---

## 3. 项目结构

```
C:/Users/Administrator/WorkBuddy/CyberpunkRED/
├── mcp_server/                          # MCP 项目根目录
│   │
│   ├── server.py                        # MCP 入口 + 7个工具（FastMCP 装饰器）
│   ├── loader.py                        # JSON 数据加载器
│   ├── requirements.txt                 # 依赖：fastmcp>=3.2.0, dice>=4.0.0
│   │
│   ├── data/                            # ★ 已构建的数据目录
│   │   ├── rules/                       # 规则速查数据（7 分类，486 条）
│   │   │   ├── index.json               # 规则分类目录
│   │   │   ├── injuries.json            # B1+B2+B3 合表（26条）
│   │   │   ├── combat.json              # B4+B5+B6 合表（85条）
│   │   │   ├── vehicles.json            # B7（14条）
│   │   │   ├── netrunner.json           # C1+C2+C3+C4 合表（54条）
│   │   │   ├── skills.json              # D1（66条）
│   │   │   ├── services.json            # D2+D3+D4+D5 合表（98条）
│   │   │   └── equipment.json           # rules/4 提取（140条）
│   │   │
│   │   └── random_tables/               # 随机表数据（37 表 + 神谕 + 士气）
│   │       ├── table_index.json         # 随机表目录索引（39 张表）
│   │       └── cyber.json               # 随机表源数据（94KB，原样复制）
│   │
│   └── ARCHITECTURE.md                  # 本文件
│
├── scripts/                             # 数据构建脚本
│   ├── build_rule_data.py               # BCD 合表转换
│   ├── build_equipment_data.py          # 装备提取
│   └── build_table_index.py             # 随机表索引生成
│
└── rules/                               # 规则参考 MD（只读，数据源）
```

---

## 4. 数据层设计

### 4.1 规则数据（rules/）

> **状态：已构建。** 由 `scripts/build_rule_data.py` 和 `scripts/build_equipment_data.py` 自动生成。

#### 数据来源

- **BCD artifacts**：`.workbuddy/shared/artifacts/` 下的 16 个 JSON（B1-B7, C1-C4, D1-D5）
- **装备数据**：`rules/4-装备与赛博组件.md` 脚本提取

#### 文件清单（7 分类，486 条记录）

| 文件 | 数据来源 | 记录数 | 说明 |
|------|---------|--------|------|
| `injuries.json` | B1 + B2 + B3 | 26 | 伤势状态 + 严重伤势(身体/头部) |
| `combat.json`   | B4 + B5 + B6 | 85 | 战斗动作 + 远程DV矩阵 + 掩体耐久 |
| `vehicles.json` | B7 | 14 | 载具属性 |
| `netrunner.json`| C1 + C2 + C3 + C4 | 54 | 程序 + 黑冰 + 交互界面 + 网络建筑 |
| `skills.json`   | D1 | 66 | 66 技能映射 |
| `services.json` | D2 + D3 + D4 + D5 | 98 | 服务价格 + 住房 + 街头药物 + 夜市物品 |
| `equipment.json` | rules/4 提取 + 2-战斗规则.md 补充 | 143 | 武器/护甲/装备/赛博组件/弹药/配件 |

#### 统一记录格式

每条记录保留原始中文字段名，额外添加 3 个下划线前缀元数据字段：

```json
{
  "武器类型": "突击步枪",
  "距离范围": "101-200米/码",
  "DV值": 20,
  "备注": "",
  "数据来源": "2-战斗规则.md",

  "_source": "core",
  "_source_file": "2-战斗规则.md",
  "_category": "combat"
}
```

**元数据字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `_source` | string | 规则层级：`core`（核心规则书）/ `solo`（单人模式）/ `third_party`（第三方） |
| `_source_file` | string | 原始来源文件名 |
| `_category` | string | MCP 分类键，对应文件名（不含 .json） |
| `_applies_when` | object | 条件触发规则（Phase 1 暂未使用） |

> `equipment.json` 额外使用 `_item_type` 字段区分子表类别（如 `赛博组件_赛博光学`、`异种武器`）。

#### index.json 格式

```json
[
  {
    "category": "injuries",
    "file": "injuries.json",
    "description": "伤势状态与严重伤势",
    "count": 26,
    "fields": ["状态名称", "效果描述", "严重度", "伤势名称", "数据来源"]
  },
  {
    "category": "combat",
    "file": "combat.json",
    "description": "战斗动作、远程DV矩阵、掩体耐久",
    "count": 85,
    "fields": ["动作名称", "武器类型", "距离范围", "DV值", "数据来源"]
  }
]
```

### 4.2 随机表数据（random_tables/）

> **状态：已构建。** `cyber.json` 从 `solo/cyber.json` 原样复制，`table_index.json` 由 `scripts/build_table_index.py` 生成。

#### 数据来源

`solo/cyber.json`（94KB，37 张标准随机表 + 神谕概率表 + 士气表）。

**MVP 方案：单文件不拆分。** 原因：全部加载到内存，拆文件无运行时收益。

#### 文件清单

| 文件 | 大小 | 内容 |
|------|------|------|
| `cyber.json` | 94KB | 37 张随机表 + 神谕(5行) + 士气(5行)，原样复制 |
| `table_index.json` | 5KB | 表名 → 骰子规格/行数/类型 的查找索引 |

#### table_index.json 格式

```json
[
  {
    "id": "verb",
    "name": "动词",
    "dice": "1d100",
    "type": "simple",
    "count": 100
  },
  {
    "id": "oracle_closed",
    "name": "封闭式提问概率表",
    "dice": "1d100",
    "type": "oracle",
    "count": 5
  },
  {
    "id": "morale",
    "name": "士气与战斗意志表",
    "dice": "1d10",
    "type": "morale",
    "count": 5
  }
]
```

**`type` 取值：**
- `"simple"` — 标准随机表（cyber.json 的 tables 键）
- `"oracle"` — 神谕概率分布表（特殊查询逻辑）
- `"morale"` — 士气表（特殊查询逻辑）

#### 已知缺口

`9-单人模式_随机表.md` 中的"形容词"表（100 条，1d100）缺失于 cyber.json。不阻塞 MVP，后续补入。

#### 延迟项

ARCHITECTURE.md 原方案中将随机表拆分为 7 个分类文件（oracle.json, words.json, locations.json 等，覆盖 111 张表），此方案延迟到 Phase 3+——仅在 37 表不够用时考虑。

#### 两种表格格式

> 注：以下示例反映 `cyber.json` 的**实际**结构（键名 `rows` + `text`）。

**格式 A — 简单单列表（占绝大多数）**

标题行包含骰子规格（如 `1d100`、`1d10`、`2d6`），每行一个掷骰结果。

cyber.json 实际结构：
```json
{
  "动词": {
    "dice": "1d100",
    "rows": [
      {"min": 1, "max": 1, "text": "警戒"},
      {"min": 2, "max": 2, "text": "自动武器"}
    ]
  }
}
```

**格式 A 变体 — 范围值表**

行内使用范围标记（如 `1–5`、`6–10`）。

```json
{
  "光景": {
    "dice": "1d100",
    "rows": [
      {"min": 1, "max": 5, "text": "龟裂的霓虹招牌疯狂闪烁"},
      {"min": 6, "max": 10, "text": "堆满废弃物的肮脏小巷"}
    ]
  }
}
```

**格式 B — 概率分布表（罕见，仅神谕 + 士气）**

多列 + 每列有独立范围。

Markdown 原文：
```
| 概率 | 否（无并发症） | 否（复杂） | 是（有并发症） | 是 |
| 必然 | 1–5 | 6–10 | 11–15 | 16–100 |
```

JSON 转换结果：
```json
{
  "name": "封闭式提问概率表",
  "dice": "1d100",
  "type": "probability",
  "columns": ["概率", "否（无并发症）", "否（复杂）", "是（有并发症）", "是"],
  "rows": [
    {
      "label": "必然",
      "ranges": [
        {"column": "否（无并发症）", "min": 1, "max": 5},
        {"column": "否（复杂）", "min": 6, "max": 10},
        {"column": "是（有并发症）", "min": 11, "max": 15},
        {"column": "是", "min": 16, "max": 100}
      ]
    }
  ]
}
```

概率表查询逻辑：给定掷骰值 → 找到命中的行（label）→ 返回该行 + 命中的列。用户可能需要再次掷骰进入子项。

#### 骰子类型统计

| 骰子 | 出现次数 | 典型用途 |
|------|---------|---------|
| 1d100 | 55 | 标准随机表 |
| 1d10  | 42 | NPC情绪、小规模随机 |
| 2d10  | 11 | 物品/名称组合 |
| 2d6   | 8  | 帮派/势力规模 |
| 1d6   | 5  | 小范围随机 |
| 3d10  | 1  | 罕见组合 |

#### 表名去重方案

数据中存在**重复表名**（如"势力与派系"出现3次、"企业名录"出现4次）。解决方式：

1. **首选匹配**：`table_index.json` 中每条记录带 `id`（自动生成 hash）
2. **用户模糊匹配**：如果 `table_name` 匹配到多个，返回列表供 AI 选择
3. **上下文敏感**：AI 可以在第二次调用中传入带编号的结果

示例重复处理：

```json
{
  "name": "企业名录",
  "id": "ent_01",
  "parent": "势力与派系",
  "context": "企业区/高档区",
  "file": "factions.json"
}
```

#### 按大类分文件方案

| 输出文件 | 包含范围 | 约计 |
|---------|---------|------|
| `oracle.json` | 神谕机制、士气与战斗意志 | 2 张概率表 |
| `words.json` | 动词/名词/形容词/光景/声响/气味 | 6 张简单表 |
| `locations.json` | 地点与场景、夜城区划、场所 | ~20 张表 |
| `npc.json` | NPC情绪/职业/名字/角色职业分类 | ~40 张表 |
| `factions.json` | 势力/派系/企业/帮派/关系网 | ~15 张表 |
| `items.json` | 物品/奇物 | ~8 张表 |
| `encounters.json` | 遭遇/事件/情节 | ~20 张表 |

**关键考虑**：`npc.json` 最大（~40 张表），但因随机表是热数据，每轮查询都需快速定位，所以按语义分类是最合理的折中。

### 4.3 索引文件

#### table_index.json

```json
[
  {
    "id": "verb_01",
    "name": "动词",
    "file": "words.json",
    "dice": "1d100",
    "type": "simple",
    "count": 100
  },
  {
    "id": "noun_01",
    "name": "名词",
    "file": "words.json",
    "dice": "1d100",
    "type": "simple",
    "count": 100
  },
  {
    "id": "oracle_main",
    "name": "封闭式提问概率表",
    "file": "oracle.json",
    "dice": "1d100",
    "type": "probability",
    "count": 5,
    "columns": ["概率", "否（无并发症）", "否（复杂）", "是（有并发症）", "是"]
  }
]
```

### 4.4 加载策略

**启动时全部加载到内存**。原因：

- 数据总量估算：
  - 规则数据：~195KB（486条）
  - 随机表数据：~94KB（37表 + 神谕 + 士气）
  - 索引文件：~8KB
  - **总计 ~297KB**
- Python 加载 ~300KB JSON 耗时 < 50ms
- 简化代码：不需要懒加载、缓存失效、并发控制
- 所有查询都是纯内存操作，无文件 I/O

**数据结构**（loader.py 加载后）：

```python
# 内存中的数据结构
mcp_server_state = {
  "rules_index": [ {"category": "injuries", ...}, ... ],  # 7 个分类
  "rules_data": {
    "injuries": [ {...}, {...}, ... ],  # 26 条
    "combat": [ {...}, {...}, ... ],     # 85 条
    "equipment": [ {...}, {...}, ... ],  # 143 条
    ...
  },
  "table_index": [ {id, name, dice, type, count}, ... ],  # 39 条
  "tables": {
    "动词": { "dice": "1d100", "rows": [{"min":1,"max":1,"text":"警戒"}, ...] },
    ...
  },
  "oracle": { "必然": {...}, "很可能": {...}, ... },  # 5 级概率
  "morale": [ {...}, {...}, ... ]  # 5 种敌人类型
}
```

---

## 5. 工具接口规范

### 5.1 `roll` — 通用骰子

**输入参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `expression` | string | 是 | 骰子表达式 | `"2d6+3"` |

**支持的表达式语法**：

```
<count>d<sides>[+/-<modifier>]
```

| 有效示例 | 说明 |
|---------|------|
| `"1d100"` | 标准的百分骰 |
| `"2d6+3"` | 两颗六面骰加 3 |
| `"1d10-1"` | 一颗十面骰减 1 |
| `"3d10"` | 三颗十面骰 |
| `"1d6"` | 一颗六面骰 |

约束：
- `count`: 正整数，1-100
- `sides`: 正整数，2-1000
- `modifier`: 整数，-1000 到 +1000
- 不支持 `d%`（用 `1d100` 代替）
- 不支持 `4d6v1`（取最高/最低需要额外工具）

**输出**：

```json
{
  "expression": "2d6+3",
  "rolls": [4, 2],
  "modifier": 3,
  "total": 9,
  "success": true
}
```

错误输出：

```json
{
  "success": false,
  "error": "无效的骰子表达式: 预计格式 NdX[+/-M]"
}
```

### 5.2 `search_rules` — 规则速查

**输入参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `query` | string | 是 | 搜索关键词 | `"霰弹"` 或 `"死亡豁免"` |
| `category` | string | 否 | 限定表（可选） | `"combat"` 或 `null` |

`category` 可选值：`"injuries"`, `"combat"`, `"vehicles"`, `"netrunner"`, `"skills"`, `"services"`, `"equipment"`

**搜索算法**：

1. 如果指定了 `category`，只搜索对应表；否则搜索全部 7 个表
2. 匹配规则：大小写不敏感的**子串匹配**，对每条记录的**所有字段**（字符串类型）逐一检查
3. 排序逻辑：
   - 精确匹配（字段值 == query）> 开头匹配（字段值 startsWith query）> 包含匹配（includes query）
4. 返回上限：10 条

**输出**：

```json
{
  "query": "霰弹",
  "category": null,
  "total_matches": 3,
  "results": [
    {
      "source": "combat",
      "match_field": "武器类型",
      "match_value": "霰弹枪（独头弹）",
      "record": {
        "武器类型": "霰弹枪（独头弹）",
        "距离范围": "0-6米/码",
        "DV值": 13,
        "数据来源": "2-战斗规则.md"
      }
    },
    {
      "source": "combat",
      "match_field": "武器类型",
      "match_value": "爆裂霰弹枪",
      "record": {
        "武器类型": "爆裂霰弹枪",
        "距离范围": "0-6米/码",
        "DV值": 13,
        "数据来源": "2-战斗规则.md"
      }
    }
  ]
}
```

**提示词模板**（供 AI 开发者参考）：

```
# 搜索规则
/search_rules 参数: query="狙击步枪", category="combat"

# 搜索所有规则
/search_rules 参数: query="死亡豁免"
```

### 5.3 `roll_table` — 随机表掷骰

**输入参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `table_name` | string | 是 | 表名（支持模糊） | `"动词"` 或 `"光景"` |
| `roll` | number | 否 | 手动指定掷骰值 | `42` |

**查找逻辑**：

1. **精确匹配**：`table_name` 与 `table_index.json` 中的某条 `name` 字段完全相等
2. **模糊匹配**：未找到精确匹配时，在所有表名中搜索子串匹配
3. **多结果处理**：如果模糊匹配返回多条（如搜"企业名录"可能命中 4 条），返回候选列表让 AI 选择

**掷骰逻辑**（格式 A — 简单表）：

```python
def roll_table_simple(rows, dice_spec, manual_roll=None):
    if manual_roll:
        roll = manual_roll
    else:
        roll = roll_dice(dice_spec)  # 根据 dice_spec 如 "1d100" 自动掷骰
    
    # 在 rows 中找到 min <= roll <= max 的条目
    # rows 已按 min 排序，可以用二分查找优化
    result = binary_search(rows, roll)
    return result
```

**掷骰逻辑**（格式 B — 概率表）：

```python
def roll_table_probability(rows, columns, manual_roll=None):
    # 1. 第一层：找到命中的行
    # 2. 返回命中的行 label + 所有列的范围，由 AI 决策是否需要再掷
    # 3. 例如：roll=7, 必然行: "否(无并发症)" [1,5], "否(复杂)" [6,10], ...
    #    命中 "否(复杂)" 列
```

**输出**（格式 A — 简单表）：

```json
{
  "table_name": "动词",
  "dice": "1d100",
  "roll": 42,
  "result": "故障",
  "type": "simple"
}
```

**输出**（格式 B — 概率表）：

```json
{
  "table_name": "封闭式提问概率表",
  "dice": "1d100",
  "roll": 7,
  "result": {
    "row_label": "必然",
    "hit_column": "否（复杂）",
    "all_columns": {
      "否（无并发症）": {"min": 1, "max": 5},
      "否（复杂）": {"min": 6, "max": 10},
      "是（有并发症）": {"min": 11, "max": 15},
      "是": {"min": 16, "max": 100}
    }
  },
  "type": "probability"
}
```

**输出**（多结果 — 模糊匹配）：

```json
{
  "error": "ambiguous",
  "query": "企业名录",
  "matches": [
    {"id": "corp_01", "name": "企业名录", "context": "企业区/高档区"},
    {"id": "corp_02", "name": "企业名录", "context": "中等区/社区"},
    {"id": "corp_03", "name": "企业名录", "context": "郊区"},
    {"id": "corp_04", "name": "企业名录", "context": "企业区/高档区"}
  ]
}
```

**提示词模板**：

```
# 掷一个标准随机表
/roll_table 参数: table_name="动词"

# 手动指定结果（用于重掷或预设）
/roll_table 参数: table_name="光景 S", roll=23
```

### 5.4 第三方扩展导入体系

#### 设计哲学

用户拿到的第三方规则不会是 JSON——是 PDF、Word、Excel、纯文本。导入链路分两层：

- **MCP 工具层**（`prepare_extension` + `import_extension`）：做机械性工作——文件读取、格式转换、数据校验、写入存储
- **AI Skill 层**（`third-party-import` skill）：做需要判断力的工作——内容分类、字段映射、覆盖/扩展决策、人工确认

这样设计的原因：不同模型能力差异大，但只要能读 Skill 指令就能走流程。机械性逻辑锁在工具里不出错，判断性逻辑由 AI+人协作完成。

#### 完整导入链路

```
用户提供原始文件（PDF/Word/Excel/Markdown/纯文本）
    │
    ▼
┌───────────────────────────────────────────┐
│ Step 1: prepare_extension（MCP工具）       │
│   - 识别文件类型                           │
│   - 提取原始文本/表格                      │
│   - 输出：提取结果 + 内容摘要              │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Step 2: AI Skill 引导（对话式）            │
│   - 展示提取内容摘要给用户                 │
│   - 引导用户判断内容类型：                 │
│     · 规则表格？→ 走 rules 路径           │
│     · 随机表？  → 走 tables 路径          │
│     · 叙事文本？→ 不导入，存为参考文档     │
│     · 混合？   → 拆分后分别处理           │
│   - 引导字段映射：                         │
│     · 原文列名 → 我们的标准字段名          │
│     · 确认 _item_type / _category          │
│   - 引导覆盖/扩展决策：                    │
│     · 这个表是替代核心规则还是新增？        │
│     · 覆盖哪张核心表？                     │
│   - 输出：结构化 JSON（草稿）              │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Step 3: 人工审核                           │
│   - AI 展示 JSON 草稿供用户确认            │
│   - 用户可修改/删除/补充                   │
│   - 确认后进入下一步                       │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ Step 4: import_extension（MCP工具）        │
│   - 注入元数据（_source / _source_file）   │
│   - 处理 override/extend 逻辑             │
│   - 写入 extensions/ 目录                  │
│   - 重建内存索引                           │
│   - 返回导入报告                           │
└───────────────────────────────────────────┘
```

#### 5.4.1 `prepare_extension` — 文档预处理工具

**用途**：读取原始文档，提取文本/表格，输出结构化的预处理结果供 AI Skill 消费。

**输入参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `file_path` | string | 是 | 原始文档路径 | `"/path/to/2070扩展.pdf"` |
| `extract_mode` | string | 否 | `"auto"` / `"tables_only"` / `"text_only"` | `"auto"` |

**支持的文件格式**：

| 格式 | 提取方式 | 依赖 |
|------|---------|------|
| `.pdf` | 文本 + 表格（双通道） | WorkBuddy 内置 PDF 读取 |
| `.docx` | 段落 + 表格 | python-docx（轻量） |
| `.xlsx` / `.csv` | 直接作为表格 | openpyxl / 标准库 csv |
| `.md` | 直接解析 Markdown 表格 | 标准库 re |
| `.txt` | 纯文本 | 标准库 |

**输出**：

```json
{
  "file": "2070扩展.pdf",
  "format": "pdf",
  "pages": 45,
  "extracted": {
    "tables": [
      {
        "page": 12,
        "headers": ["武器名", "伤害", "价格", "特殊"],
        "rows": 8,
        "sample": [["等离子步枪", "6d6", "5000", "穿甲"]],
        "suggested_type": "rules"
      }
    ],
    "text_sections": [
      {
        "page": 3,
        "heading": "新增赛博组件",
        "content_preview": "以下赛博组件为2070时代新增...",
        "suggested_type": "rules"
      }
    ],
    "random_tables": [
      {
        "page": 30,
        "name": "2070遭遇表",
        "dice": "1d10",
        "rows": 10,
        "suggested_type": "tables"
      }
    ]
  },
  "summary": "发现 3 个规则表格(共 25 行)、2 个文本段落、1 个随机表(10 行)"
}
```

> `prepare_extension` 只做提取和初步分类（`suggested_type`），不做最终决策。最终决策由 AI Skill 引导用户完成。

#### 5.4.2 AI Skill: `third-party-import`

**Skill 定义**（存储在 `.workbuddy/skills/` 或项目级 skill）：

```yaml
name: third-party-import
description: 引导用户将第三方TRPG规则文档导入MCP数据层
triggers:
  - "导入规则"
  - "添加扩展"
  - "import extension"
```

**Skill 引导流程**：

```
阶段 1 → 文档预处理
  AI: "请提供要导入的文件路径。"
  → 调用 prepare_extension(file_path)
  → 展示提取摘要

阶段 2 → 内容分类确认
  AI: "我在文档中发现了以下内容：
    - 第12页: 武器表格 (8行) → 建议归入 rules/equipment
    - 第30页: 遭遇随机表 (10行) → 建议归入 tables
    - 第3页: 赛博组件描述文本 → 建议手工整理
    请确认或修改分类。"
  → 用户确认/调整

阶段 3 → 字段映射
  AI: "武器表格的列名是 [武器名, 伤害, 价格, 特殊]，
    我们的标准字段是 [武器种类, 单发伤害, 价格, 特殊属性]。
    映射关系：
      武器名 → 武器种类
      伤害 → 单发伤害
      价格 → 价格
      特殊 → 特殊属性
    是否正确？"
  → 用户确认/修改

阶段 4 → 覆盖/扩展决策
  AI: "这 8 条武器记录是：
    (A) 新增武器（核心规则书里没有的）→ extend 模式
    (B) 替代核心武器表（2070版本替换原版）→ override 模式
    请选择。"
  → 用户选择

阶段 5 → 生成 JSON 草稿 + 人工审核
  AI: "以下是生成的 JSON，请审核：
    [展示 JSON]
    确认无误后我将执行导入。"
  → 用户确认

阶段 6 → 执行导入
  → 调用 import_extension(source_name, data_type, file_path, mode)
  → 展示导入报告
```

> **为什么用 Skill 而不是硬编码**：不同模型的理解力不同，Skill 的步骤描述可以调整详细程度。强模型可以跳步，弱模型需要每步确认。流程本身是固定的，但对话粒度是灵活的。

#### 5.4.3 `import_extension` — 导入第三方扩展包

**用途**：将经过预处理和人工确认的 JSON 数据导入 MCP Server。这是链路终端，不是入口。

**输入参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `source_name` | string | 是 | 扩展包标识（用作 `_source` 值） | `"2070手册"` |
| `data_type` | string | 是 | `"rules"` 或 `"tables"` | `"rules"` |
| `file_path` | string | 是 | JSON 文件路径 | `"/path/to/2070_weapons.json"` |
| `mode` | string | 是 | `"extend"`（追加） 或 `"override"`（覆盖同名） | `"extend"` |

**扩展包 JSON 格式要求**：

规则扩展包：
```json
[
  {
    "武器种类": "等离子步枪",
    "技能": "重型武器",
    "单发伤害": "6d6",
    "_item_type": "远程武器_长枪类",
    "_overrides": null
  }
]
```

随机表扩展包：
```json
{
  "赛博空间场景": {
    "dice": "1d10",
    "rows": [
      {"min": 1, "max": 3, "text": "数据洪流"},
      {"min": 4, "max": 6, "text": "冰壁迷宫"}
    ],
    "_overrides": null
  },
  "任务类型": {
    "dice": "1d100",
    "rows": ["..."],
    "_overrides": "任务类型"
  }
}
```

**处理流程**：

```
import_extension(source_name, data_type, file_path, mode)
  │
  ├── 1. 验证 JSON 格式
  │
  ├── 2. 为每条记录注入元数据
  │     _source = source_name
  │     _source_file = 文件名
  │     _category = 自动推断或指定
  │
  ├── 3. 覆盖模式处理
  │     if mode == "override":
  │       找到同名记录，标记 _overridden_by = source_name
  │       新记录标记 _overrides = 原记录标识
  │     elif mode == "extend":
  │       直接追加，无覆盖标记
  │
  ├── 4. 写入对应数据文件
  │     rules → data/rules/extensions/{source_name}.json
  │     tables → data/random_tables/extensions/{source_name}.json
  │
  ├── 5. 重建内存索引
  │
  └── 6. 返回导入报告
```

**输出**：

```json
{
  "source": "2070手册",
  "type": "rules",
  "mode": "extend",
  "imported": 15,
  "overridden": 0,
  "new_categories": ["cyberware_2070"],
  "version": "1.1"
}
```

**扩展数据存储结构**：

```
data/
├── rules/
│   ├── injuries.json          ← core（不动）
│   ├── equipment.json         ← core（不动）
│   └── extensions/            ← 第三方扩展（按来源隔离）
│       ├── 2070手册.json
│       └── 自制房规.json
│
└── random_tables/
    ├── cyber.json             ← core（不动）
    └── extensions/
        └── 2070手册.json
```

> **关键设计**：core 文件永远不被修改。扩展数据放在 `extensions/` 子目录，按 source_name 隔离。加载时按优先级合并：`core → solo → third_party`。

### 5.5 `list_sources` — 查看数据源层级

**输入参数**：无（或可选 `category` 过滤）

**输出**：

```json
{
  "sources": [
    {
      "name": "core",
      "priority": 0,
      "rules_count": 486,
      "tables_count": 37,
      "files": ["injuries.json", "combat.json", "..."]
    },
    {
      "name": "2070手册",
      "priority": 10,
      "rules_count": 15,
      "tables_count": 3,
      "mode": "extend",
      "overrides": ["任务类型"]
    }
  ],
  "active_priority": "2070手册 > core",
  "total_rules": 501,
  "total_tables": 40
}
```

### 5.6 `set_source_priority` — 设置源优先级

**输入参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_name` | string | 是 | 源标识 |
| `enabled` | bool | 否 | 启用/禁用该源（默认 true） |
| `priority` | int | 否 | 优先级数值（越大越优先） |

**用途**：
- 临时禁用某个第三方扩展：`set_source_priority("2070手册", enabled=false)`
- 调整覆盖顺序：`set_source_priority("自制房规", priority=20)`
- 回退到纯核心规则：禁用所有非 core 源

**输出**：

```json
{
  "source": "2070手册",
  "enabled": false,
  "priority": 10,
  "affected_rules": 15,
  "affected_tables": 3
}
```

### 5.7 随机表版本锁定与偏移量支持

#### 版本锁定机制

`cyber.json` 的 `meta` 字段包含版本信息：

```json
{
  "meta": {
    "version": "1.1",
    "row_hash": "a3f7c2...",
    "locked_at": "2026-05-04T20:00:00+08:00",
    "source": "core"
  }
}
```

- `version`：语义版本号，行排序变更时必须升级
- `row_hash`：所有表行的顺序 hash（SHA256 前 8 位），用于校验行序是否被篡改
- 偏移量记录（如剧本存档）绑定 `version + row_hash`，版本不匹配时工具会告警

#### roll_table 返回值预留偏移量字段

```json
{
  "table_name": "关系",
  "dice": "1d100",
  "roll": 90,
  "result": "敌对者",
  "result_index": 18,
  "result_min": 86,
  "result_max": 95,
  "type": "simple",
  "source": "core",
  "table_version": "1.1"
}
```

> `result_index`（行序号）+ `result_min/max`（范围）是偏移量计算的基础。`table_version` 用于校验偏移量记录的有效性。

---

## 6. 技术栈与模块划分

### 6.1 技术栈选型（2026-05-04 确定）

| 组件 | 选择 | 版本 | 角色 | 选型理由 |
|------|------|------|------|---------|
| **FastMCP** | MCP 框架 | 3.2.4 | 协议/注册/运行 | 装饰器自动推断 Schema，日下载百万，MCP 生态事实标准 |
| **dice** | 骰子引擎 | 4.0.0 | 表达式解析+掷骰 | 10年成熟，pyparsing正规文法，MIT，覆盖全部骰子语法 |
| **Python** | 运行时 | 3.13 | 宿主环境 | 已有环境 |

> **选型决策记录**：调研了 mcp-dice-roller、MCP-TTRPG、random-tables-mcp、dnd-rules-mcp 等开源方案，均不适用（详见 `.workbuddy/memory/2026-05-04.md`）。骰子解析曾自写 `scripts/roll.py`，发现 `dN-M` 格式崩溃 bug，确认自制不如开源库稳定。

### 6.2 模块划分（新方案：2 文件替代原 4 文件）

```
mcp_server/
├── server.py              # MCP 入口 + 7个工具定义
│   │
│   │  FastMCP 装饰器模式：
│   │  @mcp.tool  → roll()
│   │  @mcp.tool  → search_rules()
│   │  @mcp.tool  → roll_table()
│   │
│   │  数据管理工具：
│   │  @mcp.tool  → import_extension()
│   │  @mcp.tool  → list_sources()
│   │  @mcp.tool  → set_source_priority()
│   │
│   └── mcp.run()          # 启动 stdio 服务
│
├── loader.py              # 数据加载（启动时一次性 + 扩展导入后重建）
│   ├── load_rules(path) → dict[str, list[dict]]
│   ├── load_tables(path) → dict  {tables, oracle, morale}
│   ├── load_extensions(path) → 加载 extensions/ 子目录
│   ├── merge_by_priority(core, extensions) → 合并后的数据
│   └── load_index(path) → list[dict]
│
└── data/                  # 数据层
    ├── rules/             # core 规则（不动）
    │   ├── *.json
    │   └── extensions/    # 第三方扩展（按来源隔离）
    └── random_tables/     # core 随机表（不动）
        ├── cyber.json
        └── extensions/    # 第三方扩展
```

**与原方案对比**：

| 原方案（4 文件） | 新方案（2 文件） | 原因 |
|----------------|----------------|------|
| `server.py` — MCP 入口 | `server.py` — 入口 + 工具 | FastMCP `@mcp.tool` 装饰器吸收了 tools.py |
| `tools.py` — 工具逻辑 | **合并进 server.py** | 工具函数直接用装饰器注册，无需分离 |
| `dice.py` — 骰子解析 | **删除，用 `dice` 库** | 开源库 10 年成熟，零 bug 风险 |
| `loader.py` — 数据加载 | `loader.py` — 保留 | 数据加载逻辑独立于工具逻辑，值得分离 |

### 6.3 依赖声明

```
# requirements.txt
fastmcp>=3.2.0
dice>=4.0.0
```

> FastMCP 已包含 `mcp` SDK 作为传递依赖，不需要单独安装。

### 6.4 server.py 骨架（最终参考）

```python
from fastmcp import FastMCP
from loader import load_all
import dice as dice_lib
import re, os

# 启动时加载数据
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
state = load_all(DATA_DIR)

mcp = FastMCP("CyberpunkRED")

# ── 跑团工具 ──

@mcp.tool
def roll(expression: str) -> dict:
    """掷骰子，支持 1d10, 2d6+3, 1d100, d% 等标准表达式"""
    ...

@mcp.tool
def search_rules(query: str, category: str = None) -> dict:
    """规则速查，在结构化规则中搜索关键词（支持 7 个分类过滤）"""
    ...

@mcp.tool
def roll_table(table_name: str, roll: int = None) -> dict:
    """随机表掷骰，返回结果 + 行号/范围（偏移量计算用）"""
    ...

# ── 数据管理工具 ──

@mcp.tool
def import_extension(source_name: str, data_type: str, file_path: str, mode: str = "extend") -> dict:
    """导入第三方扩展包（规则或随机表），支持 extend/override 两种模式"""
    ...

@mcp.tool
def prepare_extension(file_path: str, extract_mode: str = "auto") -> dict:
    """预处理第三方文档（PDF/Word/Excel/Markdown），提取表格和文本供审核"""
    ...

@mcp.tool
def list_sources() -> dict:
    """查看已加载的数据源层级和优先级"""
    ...

@mcp.tool
def set_source_priority(source_name: str, enabled: bool = True, priority: int = None) -> dict:
    """设置数据源启用状态和优先级"""
    ...

if __name__ == "__main__":
    mcp.run()
    ...

if __name__ == "__main__":
    mcp.run()
```

### 6.5 模块依赖关系

```
server.py
  ├── fastmcp   ── MCP 协议（pip 安装）
  ├── dice      ── 骰子引擎（pip 安装）
  └── loader.py ── 只读文件系统，零外部依赖
```

---

## 7. 实施路线图

### Phase 0 — 数据地基（已完成 ✅ 2026-05-04）

**产出：** `mcp_server/data/` 下 9 个 JSON 文件，486 条规则 + 37 张随机表。

- [x] 编写 `scripts/build_rule_data.py` — BCD 合表（16 文件 → 6 规则 JSON + index.json）
- [x] 编写 `scripts/build_equipment_data.py` — 装备提取（rules/4 → 140 条 equipment.json）
- [x] 部署随机表（复制 cyber.json + 生成 table_index.json）
- [x] 全量验证（486 条规则元数据完整，~297KB 总量）
- [x] 更新 ARCHITECTURE.md 对齐实际

### Phase 1 — MCP Server 实现（目标：全部工具可用）

> 技术栈变更：原方案基于原生 `mcp` SDK（4文件~250行），现改用 **FastMCP 3.x + dice 4.0**（2文件~200行）。

**预估工作量**：2 个 Python 文件 + 1 个 requirements.txt，约 200 行

步骤：
1. 创建 `requirements.txt`（fastmcp>=3.2.0, dice>=4.0.0）
2. 写 `loader.py`：加载 7 规则 JSON + cyber.json → 内存 state
3. 写 `server.py`：FastMCP 入口，`@mcp.tool` 注册 7 个工具
   - 跑团工具：roll / search_rules / roll_table
   - 数据管理工具：prepare_extension / import_extension / list_sources / set_source_priority
   - `roll`：包装 `dice.roll()`，返回 {expression, rolls, modifier, total}
   - `search_rules`：全字段 `str(v)` 子串匹配，排序，截断 10 条
   - `roll_table`：精确→模糊→多结果匹配，自动掷骰
4. 注册到 WorkBuddy MCP 配置（`.workbuddy/mcp.json`）
5. 端到端测试：通过 WorkBuddy 对话调用全部工具

**验收标准**：
- [ ] WorkBuddy 启动 MCP Server 无报错
- [ ] `roll("1d100")` 返回 1-100
- [ ] `roll("2d6+3")` 返回 {rolls, modifier, total} 格式
- [ ] `search_rules("霰弹")` 命中 combat + equipment
- [ ] `search_rules("死亡豁免")` 命中 injuries
- [ ] `search_rules("皮下护甲", "equipment")` 限定分类搜索
- [ ] `roll_table("动词")` 返回随机动词
- [ ] `roll_table("封闭式")` 触发神谕查询
- [ ] `roll_table("企业")` 返回模糊匹配候选列表

### Phase 2 — 跑团体验优化
- [ ] 定义 GM 流程状态图（基于 N0-N10 路由节点）
- [ ] 实现条件过滤（杂兵 vs Boss 自动切换规则集，`_applies_when`）
- [ ] 剧本生成流程（N9+N8+N0 循环）
- [ ] 节拍图表 + 强者时钟集成

### Phase 3 — 扩展（远期）
- [ ] 第三方规则层支持（2070 手册等）
- [ ] 多角色管理
- [ ] 战役/模组存档系统
- [ ] 随机表扩展至 111 张（当前 37 张）

---

## 8. 边界与约束

### 8.1 不在本次范围内

- ❌ **剧本生成工具**（如完整的战役生成器）：冷数据，Phase 4 之后考虑
- ❌ **SmartSheet 云端同步**：MCP Server 是纯本地离线工具
- ❌ **角色卡管理**：角色数据不上云原则
- ❌ **Web 界面**：纯 API 工具，没有 UI
- ❌ **HTTP/SSE 模式**：只用 stdio

### 8.2 已知限制

- **骰子表达式**：不支持 `4d6v1`（取最高三个）等复杂表达式。Cyberpunk RED 不需要这些，但如果发现需要，可以在 dice.py 中扩展
- **概率表**：返回的是范围命中结果，是否需要进一步在子范围内二次掷骰由 AI 逻辑决定，MCP 工具只做一次查找
- **搜索性能**：全表线性扫描（每个表最多 70 条），无索引优化也极快
- **热更新**：数据变更需要重启 MCP Server（本地特性，不是问题）

### 8.3 错误处理策略

所有工具统一返回格式：

```json
{
  "success": false,
  "error": "错误描述"
}
```

具体错误场景：

| 工具 | 错误场景 | 错误信息 |
|------|---------|---------|
| `roll` | 无效表达式 | "无效的骰子表达式: 预计格式 NdX[+/-M]" |
| `roll` | 骰子数量超限 | "骰子数量不能超过 100" |
| `search_rules` | 无匹配 | "未找到匹配结果: query=xxx" |
| `search_rules` | 无效 category | "无效的规则类别: xxx，可选: injuries, combat, vehicles, netrunner, skills" |
| `roll_table` | 表名无匹配 | "未找到表名: xxx" |
| `roll_table` | 多结果 | 返回候选列表（非错误） |
| `roll_table` | 手动掷骰超出骰子范围 | "roll 值超出骰子范围" |

---

## 附录 A — 数据源实录

### A.1 BCD 批次数据（16文件 343条）+ 装备提取（143条）

> 注：以下记录数为实际验证值（2026-05-04），与原始设计文档的估算可能不同。

| 序号 | 文件名 | 记录数 | 说明 | 原始路径 |
|------|--------|--------|------|---------|
| 1 | B1_伤势状态.json | 4 | 轻伤/重伤/致命伤/死亡 | `.workbuddy/shared/artifacts/` |
| 2 | B2_严重伤势_身体.json | 11 | 身体部位严重伤势 |
| 3 | B3_严重伤势_头部.json | 11 | 头部严重伤势 |
| 4 | B4_动作列表.json | 18 | 战斗动作 |
| 5 | B5_远程DV值.json | 55 | 武器类型×距离的DV |
| 6 | B6_掩体耐久值.json | 12 | SP/HP |
| 7 | B7_载具表.json | 14 | 载具属性 |
| 8 | C1_程序表.json | 15 | 网行程序 |
| 9 | C2_黑冰表.json | 12 | 黑冰数据 |
| 10 | C3_交互界面能力.json | 9 | 交互界面能力 |
| 11 | C4_网络建筑部件.json | 18 | 网络建筑部件 |
| 12 | D1_66技能映射.json | 66 | 66技能关联属性 |
| 13 | D2_服务价格.json | 33 | 服务价格 |
| 14 | D3_住房选项.json | 11 | 住房 |
| 15 | D4_街头药物.json | 5 | 街头药物 |
| 16 | D5_夜市物品精选.json | 49 | 夜市物品 |
| — | equipment.json（rules/4提取）| 143 | 武器/护甲/装备/赛博组件/弹药/配件 |
| | **合计** | **486** | |

### A.2 随机表数据（111表 2954行）

| 大类 | 表数 | 骰子类型 | 格式 |
|------|------|---------|------|
| 神谕机制 | 2 | 1d100 | 概率分布 |
| 动词/名词/形容词 | 6 | 1d100 | 简单单列 |
| 地点与场景 | ~20 | 1d10, 1d100, 2d10 | 简单+范围 |
| 物品与奇物 | ~8 | 1d10, 2d10, 1d100 | 简单+范围 |
| NPC相关 | ~40 | 1d10, 1d6, 2d6, 1d100, 2d10 | 简单+范围 |
| 势力/派系/帮派 | ~15 | 1d10, 1d6, 2d6, 1d100 | 简单+范围 |
| 遭遇/事件 | ~20 | 1d10, 1d100 | 简单+范围 |

---

## 附录 B — 随机表分类方案

### B.1 细节说明

发现表名有重复（如"势力与派系"3次、"企业名录"4次、"帮派"2次），且某些标题下混杂了叙述性文字。JSON 化脚本需要：

1. 用 `####` 标题作为表名
2. 如果同一 `####` 标题出现多次，加后缀 `_1`, `_2` 或使用 `parent_context` 区分
3. 跳过非表格内容（纯叙述段落、空行、分隔线）
4. `table_index.json` 中为每条记录保存 `parent` 字段（上一级标题）用于上下文

### B.2 字段索引结构详情

```json
[
  {
    "id": "oracle_closed",
    "name": "封闭式提问概率表",
    "file": "oracle.json",
    "parent": "神谕机制参考表",
    "dice": "1d100",
    "type": "probability",
    "count": 5,
    "columns": ["概率", "否（无并发症）", "否（复杂）", "是（有并发症）", "是"]
  },
  {
    "id": "npc_occupation",
    "name": "角色职业",
    "file": "npc.json",
    "parent": "角色职业",
    "dice": "2d10",
    "type": "simple",
    "count": 30
  }
]
```

---

*本文档覆盖完整架构设计。核心关注点：数据层设计（预 JSON 化、格式标准、加载策略）、工具接口规范（输入/输出/错误）、模块划分与职责、实施路线图。所有技术决策基于 2026-05-04 之前完成的数据分析。*
