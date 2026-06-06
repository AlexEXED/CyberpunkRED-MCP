# CPRED MCP Server

赛博朋克 RED TTRPG 的 AI 工具服务。采用 **双 MCP 架构**：跑团端只读 + 备团端写入（待实施）。

> **定位**: MCP 专职开发区。RPG 跑团测试在独立工作区，通过 `_shared/FEEDBACK.md` 弱联动。

---

## 架构总览

```
AI GM 跑团调用                        GM 备团时启用
      │                                    │
      ▼                                    ▼
┌─────────────┐                 ┌──────────────────┐
│  跑团 MCP   │  只读 · 3工具   │   备团 MCP       │  写入 · 待实施
│ mcp_server/ │  roll           │  mcp_admin/      │  扩展导入
│             │  search_rules   │                  │  数据源管理
│             │  roll_table     │                  │  卸载 / 状态查询
└──────┬──────┘                 └────────┬─────────┘
       │                                 │
       └──────────┬──────────────────────┘
                  ▼
          mcp_server/data/
          ├── rules/          486 条 · 7 分类
          │   └── extensions/ user.json + 第三方
          ├── random_tables/  37 表 + Oracle + 士气
          └── source_config.json
```

---

## 目录结构

```
CyberpunkRED-MCP/
├── PROJECT.md              ← 架构锚点（v3.1）
├── HANDOFF.md              ← 跨会话上下文
├── SHARED.path             ← 共享区路径
├── TEST_CHECKLIST.md       ← 烟雾测试清单（41 用例）
│
├── mcp_server/             ← 跑团 MCP（只读，已上线）
│   ├── server.py           ← FastMCP 入口 · 3 工具
│   ├── loader.py           ← 数据加载 + 分层合并
│   ├── requirements.txt    ← fastmcp>=3.2.0, dice>=4.0.0
│   └── data/
│       ├── rules/
│       │   ├── index.json        ← 7 分类索引
│       │   ├── combat.json       ← 85 条
│       │   ├── equipment.json    ← 143 条
│       │   ├── injuries.json     ← 26 条
│       │   ├── netrunner.json    ← 54 条
│       │   ├── services.json     ← 98 条
│       │   ├── skills.json       ← 66 条
│       │   ├── vehicles.json     ← 14 条
│       │   └── extensions/
│       │       └── user.json     ← user 层（最高优先级）
│       ├── random_tables/
│       │   ├── cyber.json        ← 37 表 + Oracle + 士气
│       │   └── table_index.json
│       └── source_config.json    ← 数据源启用/优先级配置
│
├── mcp_admin/              ← 备团 MCP（待实施）
│   ├── README.md           ← 入口与路线图
│   ├── DESIGN_v3_原则.md   ← 10 条设计原则
│   └── _legacy_admin_functions.py  ← v2 管理函数归档
│
├── docs/                   ← 文档归档
│   ├── ARCHITECTURE.md     ← 历史架构文档
│   ├── DESIGN_v2.md        ← v2 完整技术方案
│   ├── DESIGN_v2_用户版.md
│   ├── 使用说明书.md
│   └── 经验反馈.md
│
├── 鲨鱼包拓展/              ← 真实样本（v3 阶段 3 导入对象）
├── scripts/                ← core 数据生成脚本
├── solo/                   ← 随机表源数据
└── archive/                ← 历史归档（只读）
```

---

## 跑团 MCP 工具

| 工具 | 说明 | 数据 |
|------|------|------|
| `roll` | 通用骰子：`1d10` `2d6+3` `1d100` `d%` | 无依赖 |
| `search_rules` | 规则检索：7 分类过滤 + 分层搜索（core → 扩展 → user） | 486 条 + 扩展 |
| `roll_table` | 随机表掷骰：37 表 + 神谕（5 级概率）+ 士气（5 种敌人） | cyber.json |

### 数据层级

```
user       priority=999  最终解释权，不可禁用
third_party  priority=1-998  按需启用/禁用/卸载
core       priority=0    始终加载，不可禁用
```

三种扩展模式：**Add**（新增）/ **Replace**（遮蔽）/ **Extend**（并存）。

---

## 备团 MCP（待实施）

设计原则见 [`mcp_admin/DESIGN_v3_原则.md`](mcp_admin/DESIGN_v3_原则.md)。

计划能力：扩展包初始化、数据导入、数据源管理、扩展卸载、状态查询。

真实样本（鲨鱼包 V1.71）已采集于 `鲨鱼包拓展/`，等待备团 MCP 完成后跑通端到端流程。

---

## 快速启动

```bash
# 跑团 MCP
cd C:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP\mcp_server
C:\Users\Administrator\miniconda3\python.exe server.py

# core 数据重建
cd C:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP
C:\Users\Administrator\miniconda3\python.exe scripts/build_rule_data.py
C:\Users\Administrator\miniconda3\python.exe scripts/build_table_index.py

# 共享区路径
type SHARED.path
```

---

## 版本演进

| 版本 | 里程碑 | 日期 |
|------|--------|------|
| v1 | 基础部署：3 跑团工具 + 486 规则 + 37 表 | 2026-05-04 |
| v2 | 扩展系统：分层搜索 + Replace 遮蔽 + user 层 + 41/41 测试 | 2026-05-07 |
| v3.1 | 跑团端瘦身 + 双 MCP 架构 + 10 条原则 | 2026-05-07 |
| v3.2 | 备团 MCP 设计与实施 | 待定 |
| v3.3 | 鲨鱼包真实导入 | 待定 |

---

## 关键文档索引

| 文档 | 位置 | 用途 |
|------|------|------|
| 架构锚点 | `PROJECT.md` | 唯一设计权威（32 项决策） |
| 交接手册 | `HANDOFF.md` | 跨会话上下文 |
| v3 原则 | `mcp_admin/DESIGN_v3_原则.md` | 备团 MCP 设计原则 |
| v2 方案 | `docs/DESIGN_v2.md` | 历史参考 |
| 使用手册 | `docs/使用说明书.md` | 工具使用说明 |
| 测试清单 | `TEST_CHECKLIST.md` | 41 用例烟雾测试 |
| 工程经验 | `docs/engineering/` | 6 份方法论文档 |

---

> *"夜城不管你来自哪里，只看你能不能活下去。"*
