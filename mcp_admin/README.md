# 备团 MCP（待实施）

> **状态**：v3 原则已敲定，跑团端已完成瘦身（v2 的 5 个管理工具已迁出）。具体实施待开工。

---

## 定位

为 GM 提供 **数据导入、扩展管理** 的专用 MCP Server。
与跑团 MCP 物理隔离，**独立进程、独立配置**。

跑团 MCP（`mcp_server/server.py`）是**只读**的——不暴露任何写能力。
所有数据修改路径走本备团 MCP（待实施）或 CLI 兜底脚本。

---

## 已敲定的设计基础

### 设计原则
完整 10 条原则见 [`DESIGN_v3_原则.md`](./DESIGN_v3_原则.md)。

核心要点：
- 导入阶段必须依赖人力协同（被现实逼出的转向）
- 先全量转化，再总览分类（你提出的关键工作流）
- 跨模型一致性 + 抗污染（应对长上下文 / DeepSeek-V4 等弱模型）
- AI 主导工作流，但工具是 AI 的手脚、AI 是 GM 的导游

### MCP 协议层引导能力调研结论
- 协议层无强制能力，仅靠 `instructions` + `docstring` + 工具内部状态校验
- 不实施 middleware 强制初始化（过度设计）
- 真正强制约束在工具内部 + manifest 状态机

### 真实样本基线
- `c:\Users\Administrator\WorkBuddy\CyberpunkRED-MCP\鲨鱼包拓展\` ← 已采集
- 形态复杂：18 sheet xlsx + docx + pdf + 子扩展（公司狗部门主管）
- 已确认现实远超 v2 的"单 JSON 导入"假设

---

## 待设计

| 项目 | 备注 |
|------|------|
| `manifest.json` 格式 | 包级元数据：name/version/depends_on/extraction_progress |
| 扩展包目录结构 | data/ + source/ + intermediate/（v3 阶段 A 的中间产物） |
| 分类策略 | 保留 7 标准 + 开放新增 mechanics/npcs/templates/lore |
| `admin_server.py` 工具集 | 基于 `_legacy_admin_functions.py` 的 v2 函数重构 |
| 拓扑排序加载 | 处理扩展间的依赖链 |
| 卸载策略 | 拒绝 + 提示（依赖被破坏时） |
| CLI 兜底脚本 | 主入口走 MCP，CLI 作为人手动操作的备用 |
| 入口文档 | 单一显眼入口，AI 启动即可读取（原则 9.5） |

---

## 实施起点

[`_legacy_admin_functions.py`](./_legacy_admin_functions.py)
保存了 v2 的 5 个管理函数代码（已从跑团端 server.py 迁出）：
- `prepare_extension`
- `import_extension`
- `list_sources`
- `set_source_priority`
- `remove_extension`

**注意**：这些是 v2 的实现，使用扁平 JSON 模型，**不符合 v3 原则**。备团 MCP 实施时应**重构**而非直接复用：
- 包目录结构 ≠ 扁平 JSON 文件
- manifest 驱动 ≠ 字段散落在记录里
- 两阶段流程 ≠ 一次性 import

但保留它作为：
- 业务逻辑参考（验证规则、写盘逻辑）
- v2 → v3 迁移的对照基线
- 41/41 烟雾测试用例的复盘起点

---

## 进入备团工作流时

未来 AI 进入工作区做导入工作时，应：
1. 先读本 README
2. 再读 `DESIGN_v3_原则.md` 的 10 条原则
3. 调用待实施的状态查询工具（如 `pack_status`）了解当前进度
4. 按 manifest 引导推进

> *"骨架不能被替换，但肌肉可以换，神经说了算。"*
