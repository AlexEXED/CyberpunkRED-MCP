# HANDOFF — 当前状态

> **最后更新：** 2026-05-07 22:05
> **交接序列：** #4（v3 阶段 1 完成）
>
> **v3 阶段 1 协作记录：**
> - 现实需求识别：用户提供鲨鱼包真实样本，发现扩展生态远超 v2 假设
> - 原则讨论：claude-opus-4-7-thinking（10 条原则迭代敲定）
> - 架构决策：双 MCP 架构（跑团端瘦身 + 备团端待实施）
> - 实施执行：claude-opus-4-7-thinking（瘦身、文件迁移、文档重组）

## 1. 当前目标
v3 阶段 1 已完成跑团端瘦身。下一阶段是备团 MCP 的具体设计与实施。

## 2. 已完成
- [x] v1：MCP Server 基础部署、3 跑团工具、486 条规则、37 张随机表
- [x] v2：扩展系统（分层搜索 + Replace 遮蔽 + user 层 + 5 管理工具）+ 41/41 烟雾测试
- [x] v3 阶段 1：跑团端瘦身（2026-05-07）
  - 双 MCP 架构敲定
  - 5 个管理工具从 server.py 移除（代码归档至 mcp_admin/_legacy_admin_functions.py）
  - server.py 加入 instructions 字段，明确"跑团专用、只读"
  - 项目文档重组：mcp_server/ 保持纯净、mcp_admin/ 备团占位、docs/ 归档
  - 10 条 v3 原则文档落地于 mcp_admin/DESIGN_v3_原则.md

## 3. 失败的尝试
v3 讨论过程中推翻了多个 v1/v2 假设（自我修正，不算失败）：
- "一键自动化导入" → 现实需要人力协同
- "扩展是单 JSON" → 实际是多文件项目
- "标准 7 分类够用" → 现实有机制重写、NPC 卡、范例、世界观
- "MCP 瘦身就完了" → WorkBuddy 环境下 AI 视野=MCP 工具集，需要双端架构

## 4. 关键决策（v3 新增）
- **D23 转向声明**：导入阶段必须大量依赖人力协同
- **D24 双 MCP 架构**：跑团端只读 / 备团端写能力
- **D27 两阶段工作流**：先全量预处理，再总览分类
- **D29 包级依赖**：扩展可依赖扩展（如鲨鱼包公司狗 → 鲨鱼包）
- **D30 分类开放化**：保留 7 标准 + 开放 mechanics/npcs/templates/lore
- **D32 MCP 协议无强制**：靠 instructions + docstring + 工具内部校验

详见 `PROJECT.md` 第 6.3 节，原则详见 `mcp_admin/DESIGN_v3_原则.md`。

## 5. 当前阻塞
_无阻塞。备团 MCP 待开工，无前置条件。_

## 6. 下一步（v3 阶段 2 / 阶段 3）
**阶段 2：备团 MCP 设计与实施**
1. 设计 manifest.json 格式
2. 设计扩展包目录结构（data/ + source/ + intermediate/）
3. 设计分类策略（开放化）
4. 实施备团 MCP server（admin_server.py）
5. 实施 CLI 兜底脚本
6. 拓扑排序加载逻辑
7. 入口文档与导航工具（服务原则 9.5）

**阶段 3：鲨鱼包 V1.71 真实导入**
- 样本已采集于 `鲨鱼包拓展/`
- 选择小章节先跑通端到端流程
- 验证原则 9/10 是否经得住考验

## 7. 快速启动命令
```bash
# 跑团 MCP（只读）
cd C:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP\mcp_server
C:\Users\Administrator\miniconda3\python.exe server.py

# 备团 MCP — 待实施

# 数据重建（core 数据，不涉及扩展）
cd C:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP
C:\Users\Administrator\miniconda3\python.exe scripts/build_rule_data.py
C:\Users\Administrator\miniconda3\python.exe scripts/build_table_index.py
```

## 8. 相关文件
**架构文档**：
- `PROJECT.md` — 项目总纲
- `mcp_admin/DESIGN_v3_原则.md` — 备团 MCP 设计原则（10 条）
- `mcp_admin/README.md` — 备团端入口

**跑团 MCP（只读）**：
- `mcp_server/server.py` — 3 工具
- `mcp_server/loader.py` — 数据加载

**备团 MCP（待实施）**：
- `mcp_admin/_legacy_admin_functions.py` — v2 管理函数归档（重构起点）

**历史文档（归档）**：
- `docs/DESIGN_v2.md` — v2 完整技术方案
- `docs/ARCHITECTURE.md` — 历史架构
- `docs/使用说明书.md` — v2 工具手册
- `docs/经验反馈.md`

**真实样本**：
- `鲨鱼包拓展/RED体验改良整合包V1.71/` — 阶段 3 导入对象
