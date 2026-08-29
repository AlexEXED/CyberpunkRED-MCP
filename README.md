# Cyberpunk RED MCP Server

赛博朋克 RED TTRPG 的 AI 跑团工具服务。通过 [MCP 协议](https://modelcontextprotocol.io/) 为 AI 提供掷骰、规则检索、随机表查询能力。

## 工具

| 工具 | 说明 |
|------|------|
| `roll` | 通用掷骰：`1d10` `2d6+3` `1d100` `d%` |
| `search_rules` | 规则检索：486 条结构化规则，7 分类过滤，三层优先级搜索 |
| `roll_table` | 随机表掷骰：53 张表 + 神谕（5 级概率）+ 士气（5 种敌人） |

## 快速开始

### 1. 安装依赖

```bash
cd mcp_server
pip install -r requirements.txt
```

依赖：`fastmcp >= 3.2.0`、`dice >= 4.0.0`。需要 Python 3.10+。

### 2. 配置 MCP 客户端

在你的 MCP 客户端配置中添加：

**CodeBuddy / WorkBuddy** (`~/.workbuddy/mcp.json`)：

```json
{
  "mcpServers": {
    "cyberpunk-red": {
      "command": "python",
      "args": ["<your-path>/mcp_server/server.py"]
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`)：

```json
{
  "mcpServers": {
    "cyberpunk-red": {
      "command": "python",
      "args": ["<your-path>/mcp_server/server.py"]
    }
  }
}
```

将 `<your-path>` 替换为你本地的项目路径。

### 3. 启动

MCP 通过 stdio 通信，配置好客户端后自动启动，无需手动运行。

## 数据

### 规则（486 条 · 7 分类）

| 分类 | 条数 | 内容 |
|------|------|------|
| combat | 85 | 战斗动作、远程DV矩阵、掩体 |
| equipment | 143 | 武器、护甲、装备、赛博组件 |
| services | 98 | 服务价格、住房、街头药物 |
| skills | 66 | 技能映射 |
| netrunner | 54 | 程序、黑冰、交互界面 |
| injuries | 26 | 伤势状态、严重伤势 |
| vehicles | 14 | 载具属性 |

### 随机表（53 张 + 神谕 + 士气）

涵盖：夜城场景、NPC、遭遇、装备、赛博改造、派系、尸体战利品、任务剧情等。附带神谕系统（5 级概率判定）和士气系统（5 种敌人类型）。

### 三层规则模型

```
user        priority=999  用户微调，最终解释权
third_party priority=1-998  第三方扩展，按需启用
core        priority=0    核心规则书，始终加载
```

三种扩展模式：**Add**（新增）/ **Replace**（查询时遮蔽，禁用后恢复）/ **Extend**（与原记录并存）。

## 项目结构

```
mcp_server/             ← MCP Server（已上线）
├── server.py           ← FastMCP 入口 · 3 工具
├── loader.py           ← 数据加载 + 分层合并
├── requirements.txt
├── VERSION
└── data/
    ├── rules/          ← 7 分类 JSON + extensions/
    ├── random_tables/  ← 随机表 + 索引
    └── source_config.json

mcp_admin/              ← 备团端（设计中）
docs/                   ← 架构与工程文档
scripts/                ← 数据构建脚本
```

## 发布

预构建的发布包可在 [Releases](https://github.com/AlexEXED/CyberpunkRED-MCP/releases) 页面下载。

从源码构建：

```bash
python scripts/build_release.py
# 输出 → release/cyberpunk-red-mcp-v{version}.tar.gz + .zip
```

## 许可

代码部分采用 [MIT License](LICENSE)。

规则数据基于 Cyberpunk RED 核心规则书（R. Talsorian Games）。随机表数据基于《单人游玩模式》（R. Talsorian Games 2025）。游戏数据版权归原作者所有，本项目仅供个人跑团使用。
