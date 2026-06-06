# Cyberpunk RED MCP Server

赛博朋克 RED TTRPG 的 AI 跑团工具服务。通过 MCP 协议为 AI 提供掷骰、规则检索、随机表查询能力。

## 工具

| 工具 | 说明 |
|------|------|
| `roll` | 掷骰子：`1d10` `2d6+3` `1d100` `d%` |
| `search_rules` | 规则检索：486 条结构化规则，7 分类过滤，分层搜索（core + 扩展 + user） |
| `roll_table` | 随机表掷骰：39 张表 + 神谕（5 级概率）+ 士气（5 种敌人） |

## 安装

需要 Python 3.10+。

```bash
pip install -r requirements.txt
```

依赖：
- `fastmcp >= 3.2.0`
- `dice >= 4.0.0`

## 启动

```bash
python server.py
```

MCP 通过 stdio 通信，启动后由 AI 客户端（如 CodeBuddy / Claude Desktop）自动连接。

## CodeBuddy / WorkBuddy 配置

在 `~/.workbuddy/mcp.json` 或 `~/.codebuddy/.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "cyberpunk-red": {
      "command": "python",
      "args": ["<path-to>/mcp_server/server.py"]
    }
  }
}
```

## 数据

```
data/
├── rules/
│   ├── index.json          ← 7 分类索引
│   ├── combat.json          85 条 — 战斗动作、远程DV矩阵、掩体
│   ├── equipment.json      143 条 — 武器、护甲、装备、赛博组件
│   ├── injuries.json        26 条 — 伤势状态、严重伤势
│   ├── netrunner.json       54 条 — 程序、黑冰、交互界面
│   ├── services.json        98 条 — 服务价格、住房、街头药物
│   ├── skills.json          66 条 — 66 项技能映射
│   ├── vehicles.json        14 条 — 载具属性
│   └── extensions/
│       └── user.json        ← user 层微调（最高优先级）
├── random_tables/
│   ├── cyber.json           ← 39 表 + 神谕 + 士气
│   └── table_index.json
└── source_config.json       ← 数据源启用/优先级配置
```

## 规则层级

```
user        priority=999  用户微调，最终解释权
third_party priority=1-998  第三方扩展，按需启用
core        priority=0    核心规则书，始终加载
```

三种扩展模式：**Add**（新增）/ **Replace**（遮蔽）/ **Extend**（并存）。

core 数据永不被覆盖。Replace 是查询时遮蔽，禁用扩展后自动恢复。

## 许可

规则数据基于 Cyberpunk RED 核心规则书（R. Talsorian Games）。
随机表数据基于《单人游玩模式》（R. Talsorian Games 2025）。
本项目仅供个人跑团使用。
