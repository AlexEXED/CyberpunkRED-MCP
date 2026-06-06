# PROJECT.md — 项目总纲

> **版本**: 3.1 | 日期: 2026-05-07
> **定位**: 双 MCP 架构 — 跑团端瘦身完成（3 工具只读），备团端待实施。三层规则模型。

---

## 一、项目定义

### 1.1 这是什么

**CPRED MCP Server** — 为赛博朋克 RED TTRPG 提供 AI 可调用的专用工具服务（掷骰、规则检索、随机表查询、扩展管理）。

采用 **双 MCP 架构**：
- **跑团 MCP**（`mcp_server/`）— 只读消费层，3 个工具：roll / search_rules / roll_table
- **备团 MCP**（`mcp_admin/`，待实施）— 数据导入与扩展管理，独立进程、独立配置

### 1.2 与 RPG 跑团的关系

```
CPRED MCP Server (本工作区)              ←→      CyberpunkRED-RPG (独立工作区)
  ├── 跑团 MCP (mcp_server/)                       │
  │     提供: roll / search_rules / roll_table     │  消费: AI GM 调用
  │     状态: 只读                                 │  反馈: _shared/FEEDBACK.md
  ├── 备团 MCP (mcp_admin/，待实施)                │
  │     提供: 扩展导入、数据源管理                 │
  │     使用者: GM 备团时（独立进程）              │
  └────────── _shared/rules/ ──────────────────────┘
              (共享规则数据)
```

**弱联动**: 本区只管 MCP 工具开发，RPG 跑团区独立运行。联动仅通过 `_shared/FEEDBACK.md`（缺陷回流）。

---

## 二、数据架构

### 2.1 四层规则模型

规则数据按来源分三层，上层可选择性覆盖下层：

```
用户微调 (user — 最终解释权，priority=999)
    │  ← 用户对规则的解释、定义、房规裁定
    │  ← 不可禁用/不可卸载
    │  ← _depends_on 字段声明依赖扩展
    ▼ 可覆盖
第三方规则 (third_party — 可选扩展，priority=1-998)
    │  ← 房规、社区自制、2070手册
    │  ← 三种模式：Add / Replace / Extend
    │  ← 可禁用（软件关闭）/ 可卸载（物理删除）
    ▼ 可覆盖
核心规则 (core — 基石，始终加载，priority=0)
    │  ← 核心规则书 PDF 官方原版
```

**层级优先级**（数字越大越优先）：

| 层级 | source | priority | 加载策略 |
|------|--------|----------|---------|
| user | `"user"` | 999（固定） | 始终启用，不可禁用/卸载 |
| third_party | 扩展包名 | 1-998（可调） | 按需启用/禁用/卸载 |
| core | `"core"` | 0（固定） | 始终加载，不可禁用 |

### 2.2 三种扩展模式

| 模式 | 效果 | 示例 |
|------|------|------|
| **Add** | 新增内容，不与 core 冲突 | 等离子步枪（core 不存在） |
| **Replace** | 替代 core 记录，遮蔽原始（数据不删除） | 2070版重型手枪伤害改为 4d6 |
| **Extend** | 补充 core 记录，两条并存由 AI 理解 | 重型手枪新增"穿甲"属性 |

### 2.3 显式分层，透明溯源

**禁止合并黑盒。** 每条规则必须携带来源身份证：

```json
{
  "武器种类": "重型手枪",
  "单发伤害": "3d6",
  "_source": "core",
  "_source_file": "weapons.json",
  "_category": "equipment"
}
```

### 2.4 确定性边界

| 类型 | 归属 | 约束 |
|------|------|------|
| 有明确触发条件的（杂兵 vs Boss） | **数据层** | 标注 `applies_when`，MCP 自动过滤 |
| 需要 GM/叙事判断的 | **GM 层（RPG 区）** | 不在 MCP 数据层处理 |

**原则：确定性归数据层，灵活性归 GM 层。**

---

## 三、MCP Server 工具集

### 3.1 跑团 MCP（`mcp_server/`，已上线）

只读层，3 个工具，AI 跑团时常驻：

| 工具 | 用途 | 数据依赖 | 使用频次 |
|------|------|----------|---------|
| `roll` | 通用骰子（d6/d10/d100/XdY+Z） | 无 | 高频 |
| `search_rules` | 规则速查（分层搜索：core + 扩展 + user） | 结构化规则 JSON | 按需 |
| `roll_table` | 随机表掷骰（37 表 + Oracle + 士气） | table_index.json | 每轮必用 |

### 3.2 备团 MCP（`mcp_admin/`，待实施）

独立进程，承担所有数据写能力，GM 备团时启用：

| 待实施能力 | 用途 |
|---------|------|
| 扩展包初始化 | 创建包目录结构 + manifest.json |
| 扩展数据导入 | 验证 + 写盘（接收 AI 协助生成的草稿 JSON） |
| 数据源管理 | 列表 / 启用 / 禁用 / 优先级调整 |
| 扩展卸载 | 物理删除 + 依赖检查（拒绝破坏依赖关系的卸载） |
| 状态查询 | pack_status：当前进度、下一步建议（服务原则 9.4） |

> 设计原则：[`mcp_admin/DESIGN_v3_原则.md`](mcp_admin/DESIGN_v3_原则.md)（10 条）
> 实施起点：[`mcp_admin/_legacy_admin_functions.py`](mcp_admin/_legacy_admin_functions.py)（v2 实现归档）

### 3.3 设计哲学

- **跑团端**：只读、精简、AI 默认视野，不暴露任何写能力
- **备团端**：写能力集中、流程严格、依赖人力协同
- **物理隔离**：两套独立 MCP 进程，不同场景挂不同实例

---

## 四、当前状态

### 4.1 已完成
- [x] MCP Server 部署验证：roll / roll_table / search_rules 通过 stdio 实际调用验证
- [x] 486 条结构化规则（7 分类 core）+ 39 张随机表 + Oracle + 士气
- [x] **v2 扩展系统**：search_rules 分层搜索 + Replace 遮蔽 + 来源标识
- [x] **user 层落地**：user.json 自动初始化 + 依赖声明 + 休眠/恢复
- [x] 41/41 端到端烟雾测试通过
- [x] **v3 阶段 1：跑团端瘦身完成**（2026-05-07）
  - 管理工具（5 个）从跑团 MCP 移除，代码归档至 `mcp_admin/_legacy_admin_functions.py`
  - 跑团 MCP 转为只读，3 工具精简
  - 加入 `instructions` 字段明确跑团专用场景
  - 项目文档重组：`mcp_server/` 保持纯净、`mcp_admin/` 备团占位、`docs/` 归档
- [x] **v3 原则敲定**：10 条原则（见 `mcp_admin/DESIGN_v3_原则.md`）

### 4.2 待实施
- [ ] **v3 阶段 2**：备团 MCP 设计与实施
  - manifest.json 格式
  - 扩展包目录结构（data/ + source/ + intermediate/）
  - 分类策略开放化（保留 7 标准 + 开放 mechanics/npcs/templates/lore）
  - 拓扑排序加载（处理扩展依赖链）
  - 入口文档与导航工具（服务原则 9.5）
- [ ] **v3 阶段 3**：鲨鱼包 V1.71 真实导入（样本已采集于 `鲨鱼包拓展/`）

### 4.3 已知风险
- 跑团端当前依赖 v2 数据格式（扁平 extension JSON）。备团 MCP 切换到新格式（包目录）时需同步升级 loader.py。

---

## 五、目录结构

```
CyberpunkRED-MCP/
├── PROJECT.md              ← 本文件（架构锚点）
├── README.md               ← 文件索引
├── HANDOFF.md              ← 跨会话上下文
├── SHARED.path             ← 共享区路径指针
│
├── mcp_server/             ← 跑团 MCP（只读，已上线）
│   ├── server.py           ← FastMCP 入口（3 跑团工具）
│   ├── loader.py           ← 规则/表加载器
│   ├── requirements.txt
│   └── data/
│       ├── rules/          ← 结构化规则 JSON（7 分类）
│       │   └── extensions/ ← 第三方扩展 + user.json
│       └── random_tables/  ← 随机表 JSON
│           └── extensions/ ← 随机表扩展
│
├── mcp_admin/              ← 备团 MCP（待实施）
│   ├── README.md           ← 备团端入口与路线图
│   ├── DESIGN_v3_原则.md   ← v3 设计原则（10 条）
│   └── _legacy_admin_functions.py  ← v2 管理函数归档（重构起点）
│
├── docs/                   ← 项目文档归档
│   ├── ARCHITECTURE.md
│   ├── DESIGN_v2.md        ← v2 完整技术设计
│   ├── DESIGN_v2_用户版.md
│   ├── 使用说明书.md
│   └── 经验反馈.md
│
├── 鲨鱼包拓展/              ← 真实样本（v3 阶段 3 导入对象）
│   └── RED体验改良整合包V1.71/
│
├── scripts/                ← 数据生成/维护脚本（core 数据构建）
├── solo/                   ← 随机表源数据
└── archive/                ← 历史归档（只读）
```

---

## 六、技术决策

### 6.1 v1 基础决策

| # | 决策 | 结论 | 日期 |
|---|------|------|------|
| D1 | 规则分层 | 三层：core(底) → third_party → user(顶) | 2026-05-06 |
| D2 | 层间关系 | 显式分层，透明溯源，禁止合并黑盒 | 2026-05-04 |
| D3 | 数据标注 | 每条规则带 `source` 身份证 | 2026-05-04 |
| D4 | 确定性边界 | 有条件的归数据层，需判断的归 GM 层 | 2026-05-04 |
| D5 | MCP 通信方式 | stdio（零配置，AI 自动管理进程） | 2026-05-04 |
| D6 | Python 环境 | `C:\Users\Administrator\miniconda3\python.exe` | 2026-05-04 |
| D7 | 编码 | Windows 默认 GBK，MCP 统一 UTF-8 | 2026-05-04 |
| D8 | 工具原则 | 一体化工具，拒绝碎片化脚本 | 2026-05-04 |
| D9 | 工作区拆分 | MCP 开发区 + RPG 测试区 + _shared 共享区 | 2026-05-06 |
| D10 | 规则模型升级 | 三层确定：core / third_party / user，solo 融入扩展层 | 2026-05-06 |

### 6.2 v2 扩展系统决策（2026-05-07 实施）

| # | 决策 | 结论 |
|---|------|------|
| D11 | 物理覆盖 | **铁律：扩展绝不物理覆盖 core 数据文件** |
| D12 | 扩展模式 | 三种同时支持：Replace / Extend / Add |
| D13 | 冲突检测 | 扩展记录自行声明 `_overrides` / `_extends` |
| D14 | user 层实现 | `extensions/user.json`，priority=999，不可禁用/卸载 |
| D15 | Replace 遮蔽 | 全查后过滤：收集所有层匹配，移除被 Replace 遮蔽的记录 |
| D16 | Extend 返回 | 返回两条记录（原始 + 扩展），由 AI/GM 合并理解 |
| D17 | 来源标识 | 结果新增 `source_layer` + `source_name` 字段 |
| D18 | 运行时开关 | 查询时实时检查 `source_config` 的 `enabled` 状态 |
| D19 | 分类策略 | 强制归入标准 7 分类，备注标注真实形态 |
| D20 | 卸载机制 | 禁用与卸载分离，新增 `remove_extension` 工具 |
| D21 | user 依赖 | `_depends_on` 字段声明依赖，依赖禁用/卸载时记录休眠 |
| D22 | user 保护 | `remove_extension` 和 `set_source_priority` 拒绝对 user 层操作 |

### 6.3 v3 架构决策（2026-05-07 阶段 1 实施）

| # | 决策 | 结论 |
|---|------|------|
| D23 | 转向声明 | **导入阶段必须大量依赖人力协同**——v1/v2 "一键导入" 假设被现实推翻 |
| D24 | 双 MCP 架构 | 跑团端（只读，3 工具）/ 备团端（写能力，独立进程） |
| D25 | 工作流外化 | 跨模型一致性靠工具/文档显式编码，不依赖 AI 内部推理 |
| D26 | 抗污染设计 | 长上下文 + 弱模型场景下仍需可用，强制状态校验 |
| D27 | 工作流分两阶段 | 阶段 A 全量预处理 → 阶段 B 总览分类（禁止边读边写） |
| D28 | 扩展包是项目 | 包目录结构（manifest + data + source + intermediate），非单 JSON |
| D29 | 包级依赖 | 第三方扩展可依赖其他扩展（如鲨鱼包公司狗 → 鲨鱼包），需拓扑加载 |
| D30 | 分类开放化 | 保留标准 7 分类 + 开放新增（mechanics / npcs / templates / lore） |
| D31 | 原始资料保留 | 每个扩展包内 source/ 子目录长期保留 docx/xlsx/pdf |
| D32 | MCP 协议层不强制 | 调研结论：协议层无强制能力，靠 instructions + docstring + 工具内部校验 |

---

## 七、铁律

1. **PROJECT.md 是唯一架构锚点。** 设计分歧以此为准。
2. **MCP Server 启动时全量加载，运行时零网络依赖。**
3. **每条规则必须标注来源。** 不能把 narrative 判断伪装成官方规则。
4. **archive/ 只进不出。** 历史文件归档即封存，不删除不修改。
5. **随机表行序一旦定稿即冻结。** 变更必须升级 `meta.version`。
6. **core 数据文件永不被第三方或扩展覆盖。** 扩展数据按来源隔离存放，Replace 采用查询时遮蔽策略。
7. **MCP 通过 stdio 实际调用验证，禁止直接函数调用测试。**
8. **本工作区只处理 MCP 开发事务。** RPG 跑团逻辑归 RPG 工作区。
9. **user 层是最终解释权。** 用户对规则的微调定义优先级最高，覆盖所有下层。

---

> *"夜城不管你来自哪里，只看你能不能活下去。"*
