# MCP Server 扩展系统设计方案 v2

> **日期**: 2026-05-07 | **状态**: ✅ 已敲定并实施
> **范围**: search_rules 扩展读取 + 运行时开关 + 卸载机制 + user 层依赖

---

## 一、现有模块回顾

### 1.1 文件结构

```
mcp_server/
├── server.py          # 594 行，7 个 MCP 工具
├── loader.py          # 174 行，数据加载模块
├── data/
│   ├── rules/         # 7 个 core 规则 JSON + index.json（486 条）
│   │   └── extensions/  # 第三方扩展（按 source_name 隔离）
│   ├── random_tables/
│   │   ├── cyber.json   # 37 随机表 + 神谕 + 士气
│   │   └── extensions/  # 随机表扩展
│   └── source_config.json  # 数据源优先级配置
```

### 1.2 内存数据结构（state dict）

```python
state = {
    "rules_index": [...],                    # index.json 分类目录
    "rules_data": {                          # core 规则（7 分类）
        "injuries": [...],      # 26 条
        "combat": [...],        # 85 条
        "vehicles": [...],      # 14 条
        "netrunner": [...],     # 54 条
        "skills": [...],        # 66 条
        "services": [...],      # 98 条
        "equipment": [...],     # 143 条
    },
    "rules_extensions": [                    # 第三方扩展（已加载但未被搜索）
        {"source": "2070手册", "file": "2070手册.json", "data": [...]},
    ],
    "tables": {...},                         # 37 张随机表
    "oracle": {...},                         # 神谕 5 级
    "morale": [...],                         # 士气 5 种
    "table_meta": {...},                     # 版本信息
    "tables_extensions": [...],              # 随机表扩展
    "source_config": {                       # 优先级配置
        "sources": {
            "core": {"enabled": True, "priority": 0},
            ...
        }
    },
    "data_dir": str,                         # 数据目录路径
}
```

### 1.3 当前 search_rules 逻辑（server.py 78-160 行）

```python
@mcp.tool
def search_rules(query: str, category: str = None) -> dict:
    # 1. 验证 category 是否在 state["rules_data"].keys() 中
    # 2. 确定搜索范围：只从 state["rules_data"] 取
    # 3. 遍历记录，全字段子串匹配
    # 4. 按优先级排序（精确 > 开头 > 包含）
    # 5. 截断 10 条返回
```

**缺陷**：
- 第 99-103 行只搜索 `state["rules_data"]`
- 完全忽略 `state["rules_extensions"]`
- 无来源层级标识

### 1.4 当前 set_source_priority 逻辑（server.py 555-586 行）

```python
@mcp.tool
def set_source_priority(source_name, enabled=True, priority=None):
    # 1. 拒绝对 core 操作
    # 2. 修改 source_config["sources"][source_name]
    # 3. 写入 source_config.json
```

**缺陷**：
- 修改了配置文件，但 search_rules 不读取 enabled 状态
- 禁用操作实际无效果

### 1.5 当前 import_extension 逻辑（server.py 407-495 行）

```python
@mcp.tool
def import_extension(source_name, data_type, file_path, mode="extend"):
    # 1. 验证参数
    # 2. 读取 JSON
    # 3. 注入元数据（_source, _source_file, _category）
    # 4. 写入 extensions/{source_name}.json
    # 5. 更新 source_config
    # 6. 重新加载扩展到内存
```

**缺陷**：
- 第 447 行：`_category` 默认设为 `source_name`（非标准分类）
- 无 `_override_mode` / `_overrides` / `_extends` / `_depends_on` 字段注入
- 无 user 层特殊处理

### 1.6 当前 loader.py 逻辑

```python
def load_extensions(base_dir, data_type):
    # 遍历 extensions/ 目录
    # 每个 .json 文件加载为 {"source": name, "file": fname, "data": ...}
    # 不检查 enabled 状态
```

**缺陷**：
- 加载时不过滤 disabled 的扩展（这个可以接受，过滤在查询时做）

---

## 二、设计决策汇总

| # | 决策 | 结论 | 日期 |
|---|------|------|------|
| D11 | 物理覆盖 | **铁律：扩展绝不物理覆盖 core 数据文件** | 2026-05-07 |
| D12 | 扩展模式 | 三种同时支持：Replace / Extend / Add | 2026-05-07 |
| D13 | 冲突检测 | 扩展记录自行声明 `_overrides` / `_extends` | 2026-05-07 |
| D14 | user 层实现 | `extensions/user.json`，priority=999，不可禁用/卸载 | 2026-05-07 |
| D15 | Replace 遮蔽 | 全查后过滤：收集所有层匹配，移除被 Replace 遮蔽的记录 | 2026-05-07 |
| D16 | Extend 返回 | 返回两条记录（原始 + 扩展），由 AI/GM 合并理解 | 2026-05-07 |
| D17 | 来源标识 | 结果新增 `source_layer` + `source_name` 字段 | 2026-05-07 |
| D18 | 运行时开关 | 查询时实时检查 `source_config` 的 `enabled` 状态 | 2026-05-07 |
| D19 | 分类策略 | 强制归入标准 7 分类，备注标注真实形态 | 2026-05-07 |
| D20 | 卸载机制 | 禁用与卸载分离，新增 `remove_extension` 工具 | 2026-05-07 |
| D21 | user 依赖 | `_depends_on` 字段声明依赖，依赖禁用时记录休眠 | 2026-05-07 |
| D22 | user 保护 | `remove_extension` 和 `set_source_priority` 拒绝对 user 层操作 | 2026-05-07 |

---

## 三、扩展记录数据格式

### 3.1 三种模式的元数据字段

#### Add 模式（默认，新增内容）

```json
{
  "武器种类": "等离子步枪",
  "单发伤害": "6d6",
  "价格": "5000 eb",
  "_source": "2070手册",
  "_source_file": "2070_weapons.json",
  "_category": "equipment",
  "_override_mode": "add"
}
```

#### Replace 模式（替代 core 记录）

```json
{
  "武器种类": "重型手枪",
  "单发伤害": "4d6",
  "价格": "150 eb",
  "_source": "2070手册",
  "_source_file": "2070_weapons.json",
  "_category": "equipment",
  "_override_mode": "replace",
  "_overrides": "重型手枪"
}
```

`_overrides` 值 = 被替代的 core 记录中主键字段的值。查询时用于匹配遮蔽目标。

#### Extend 模式（补充 core 记录）

```json
{
  "武器种类": "重型手枪",
  "特殊属性": "穿甲",
  "备注": "2070 版本新增穿甲能力",
  "_source": "2070手册",
  "_source_file": "2070_weapons.json",
  "_category": "equipment",
  "_override_mode": "extend",
  "_extends": "重型手枪"
}
```

### 3.2 user 层记录格式

```json
{
  "武器种类": "重型手枪",
  "单发伤害": "5d6",
  "备注": "GM裁定：2070版重型手枪伤害降为5d6",
  "_source": "user",
  "_source_file": "user.json",
  "_category": "equipment",
  "_override_mode": "replace",
  "_overrides": "重型手枪",
  "_depends_on": "2070手册"
}
```

不依赖任何扩展的通用房规：

```json
{
  "动作名称": "爆头",
  "描述": "爆头伤害乘数改为 x3",
  "_source": "user",
  "_source_file": "user.json",
  "_category": "combat",
  "_override_mode": "extend",
  "_extends": "爆头",
  "_depends_on": null
}
```

### 3.3 元数据字段完整定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `_source` | string | ✅ | 来源标识：`"core"` / `"user"` / 扩展包名 |
| `_source_file` | string | ✅ | 来源文件名 |
| `_category` | string | ✅ | 标准 7 分类之一 |
| `_override_mode` | string | ✅ | `"add"` / `"replace"` / `"extend"` |
| `_overrides` | string | ❌ | Replace 模式：被替代记录的主键值 |
| `_extends` | string | ❌ | Extend 模式：被补充记录的主键值 |
| `_depends_on` | string/null | ❌ | user 层：依赖的扩展包名，null=不依赖 |

---

## 四、search_rules 新逻辑

### 4.1 查询流程（伪代码）

```python
def search_rules(query: str, category: str = None) -> dict:
    # 1. 验证参数
    if not query.strip():
        return error

    valid_categories = list(state["rules_data"].keys())  # 固定 7 个
    if category and category not in valid_categories:
        return error

    # 2. 收集所有层的匹配结果
    all_results = []

    # 2a. 搜索 core 层
    core_scope = {category: state["rules_data"][category]} if category else state["rules_data"]
    for cat, records in core_scope.items():
        for record in records:
            match = _match_record(record, query)
            if match:
                all_results.append({
                    "source": cat,
                    "source_layer": "core",
                    "source_name": "核心规则书",
                    "match_field": match["field"],
                    "match_priority": match["priority"],
                    "record": _clean_record(record),
                })

    # 2b. 搜索扩展层（rules_extensions）
    for ext in state["rules_extensions"]:
        ext_source = ext["source"]

        # D18: 检查 enabled 状态
        src_cfg = state["source_config"]["sources"].get(ext_source, {})
        if not src_cfg.get("enabled", True):
            continue  # 跳过禁用的扩展

        # D21: user 层依赖检查（user.json 中的记录）
        # 注：这里是扩展级别的检查，记录级别的 _depends_on 在下面处理

        ext_data = ext["data"]
        if not isinstance(ext_data, list):
            continue

        for record in ext_data:
            # 分类过滤
            rec_category = record.get("_category", "")
            if category and rec_category != category:
                continue

            # D21: 记录级别的依赖检查
            depends_on = record.get("_depends_on")
            if depends_on:
                dep_cfg = state["source_config"]["sources"].get(depends_on, {})
                if not dep_cfg.get("enabled", True):
                    continue  # 依赖的扩展被禁用，此记录休眠

            match = _match_record(record, query)
            if match:
                # 确定 source_layer
                if ext_source == "user":
                    layer = "user"
                else:
                    layer = "third_party"

                all_results.append({
                    "source": rec_category,
                    "source_layer": layer,
                    "source_name": ext_source,
                    "match_field": match["field"],
                    "match_priority": match["priority"],
                    "record": _clean_record(record),
                    "_override_mode": record.get("_override_mode", "add"),
                    "_overrides": record.get("_overrides"),
                    "_extends": record.get("_extends"),
                })

    # 3. D15: Replace 遮蔽处理
    #    收集所有 Replace 记录的 _overrides 目标
    override_targets = set()
    for r in all_results:
        if r.get("_override_mode") == "replace" and r.get("_overrides"):
            override_targets.add((r["source"], r["_overrides"]))

    #    移除被遮蔽的 core 记录
    if override_targets:
        filtered = []
        for r in all_results:
            if r["source_layer"] == "core":
                # 检查此 core 记录是否被遮蔽
                is_overridden = False
                for target_cat, target_key in override_targets:
                    if r["source"] == target_cat:
                        # 检查记录中是否有字段值 == target_key
                        for v in r["record"].values():
                            if str(v) == target_key:
                                is_overridden = True
                                break
                    if is_overridden:
                        break
                if not is_overridden:
                    filtered.append(r)
            else:
                filtered.append(r)
        all_results = filtered

    # 4. 排序：match_priority（精确>开头>包含），同优先级按层级排序（user > third_party > core）
    layer_order = {"user": 0, "third_party": 1, "core": 2}
    all_results.sort(key=lambda r: (r["match_priority"], layer_order.get(r["source_layer"], 9)))

    # 5. 截断 + 清理内部字段
    total_matches = len(all_results)
    all_results = all_results[:10]

    for r in all_results:
        r.pop("match_priority", None)
        r.pop("_override_mode", None)
        r.pop("_overrides", None)
        r.pop("_extends", None)

    return {
        "query": query,
        "category": category,
        "total_matches": total_matches,
        "results": all_results,
    }
```

### 4.2 返回值格式变更

**旧格式**：
```json
{
  "query": "重型手枪",
  "category": null,
  "total_matches": 1,
  "results": [{
    "source": "equipment",
    "match_field": "武器种类",
    "record": {"武器种类": "重型手枪", "单发伤害": "3d6", ...}
  }]
}
```

**新格式**：
```json
{
  "query": "重型手枪",
  "category": null,
  "total_matches": 2,
  "results": [
    {
      "source": "equipment",
      "source_layer": "third_party",
      "source_name": "2070手册",
      "match_field": "武器种类",
      "record": {"武器种类": "重型手枪", "单发伤害": "4d6", "备注": "2070版本"}
    },
    {
      "source": "equipment",
      "source_layer": "core",
      "source_name": "核心规则书",
      "match_field": "武器种类",
      "record": {"武器种类": "重型手枪", "单发伤害": "3d6", ...}
    }
  ]
}
```

**Replace 生效时**（2070 手册声明 replace 重型手枪）：
```json
{
  "query": "重型手枪",
  "category": null,
  "total_matches": 1,
  "results": [
    {
      "source": "equipment",
      "source_layer": "third_party",
      "source_name": "2070手册",
      "match_field": "武器种类",
      "record": {"武器种类": "重型手枪", "单发伤害": "4d6"}
    }
  ]
}
```

---

## 五、set_source_priority 改动

### 5.1 现有逻辑保留

- 拒绝对 core 操作 ✅
- 修改 enabled / priority ✅
- 写入 source_config.json ✅

### 5.2 新增：拒绝对 user 层操作

```python
if source_name == "user":
    return {"success": False, "error": "user 层不可禁用或调整优先级"}
```

### 5.3 无需重建内存

D18 决策：查询时实时检查 enabled，所以 set_source_priority 修改配置后立即生效，无需重建。

---

## 六、新增工具：remove_extension

### 6.1 接口定义

```python
@mcp.tool
def remove_extension(source_name: str) -> dict:
    """卸载第三方扩展包。物理删除扩展文件并清理配置。

    source_name: 扩展包标识（如 "2070手册"）

    注意：
    - core 和 user 层不可卸载
    - 卸载后依赖此扩展的 user 微调将休眠（不删除）
    - 如需临时关闭扩展，请使用 set_source_priority(enabled=false)
    """
```

### 6.2 处理流程

```python
def remove_extension(source_name: str) -> dict:
    # 1. 保护检查
    if source_name == "core":
        return error("core 不可卸载")
    if source_name == "user":
        return error("user 层不可卸载")

    # 2. 检查扩展是否存在
    config = state["source_config"]
    if source_name not in config["sources"]:
        return error(f"未找到扩展: {source_name}")

    # 3. 确定文件路径并删除
    data_type = config["sources"][source_name].get("data_type", "rules")
    if data_type == "rules":
        ext_path = os.path.join(state["data_dir"], "rules", "extensions", f"{source_name}.json")
    else:
        ext_path = os.path.join(state["data_dir"], "random_tables", "extensions", f"{source_name}.json")

    if os.path.exists(ext_path):
        os.remove(ext_path)

    # 4. 清理 source_config
    del config["sources"][source_name]
    save_source_config(state["data_dir"], config)
    state["source_config"] = config

    # 5. 重建内存中的扩展列表
    from loader import load_extensions
    if data_type == "rules":
        state["rules_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "rules"), "rules"
        )
    else:
        state["tables_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "random_tables"), "tables"
        )

    # 6. 统计受影响的 user 微调
    dormant_user_rules = 0
    for ext in state["rules_extensions"]:
        if ext["source"] == "user" and isinstance(ext["data"], list):
            for record in ext["data"]:
                if record.get("_depends_on") == source_name:
                    dormant_user_rules += 1

    return {
        "source": source_name,
        "removed": True,
        "dormant_user_rules": dormant_user_rules,
        "hint": f"已卸载。{dormant_user_rules} 条 user 微调进入休眠状态。" if dormant_user_rules else "已卸载。"
    }
```

---

## 七、import_extension 改动

### 7.1 强制 _category 为标准 7 分类

```python
VALID_CATEGORIES = ["injuries", "combat", "vehicles", "netrunner", "skills", "services", "equipment"]

# 导入时验证
for record in ext_data:
    record["_source"] = source_name
    record["_source_file"] = os.path.basename(file_path)

    # 强制 _category 为标准分类
    if record.get("_category") not in VALID_CATEGORIES:
        return {
            "success": False,
            "error": f"记录的 _category 必须是标准分类之一: {VALID_CATEGORIES}，"
                     f"收到: {record.get('_category')}"
        }

    # 验证 _override_mode
    mode = record.get("_override_mode", "add")
    if mode not in ("add", "replace", "extend"):
        return {
            "success": False,
            "error": f"_override_mode 必须是 add/replace/extend，收到: {mode}"
        }
```

### 7.2 user 层导入保护

```python
# user 层只能通过专用方式管理，不能通过 import_extension 覆盖
if source_name == "user":
    return {"success": False, "error": "user 层不可通过 import_extension 导入，请使用专用管理方式"}
```

---

## 八、loader.py 改动

### 8.1 无结构性改动

loader.py 的 `load_extensions` 函数保持不变：
- 仍然加载 extensions/ 下所有 .json 文件
- 不做 enabled 过滤（过滤在查询时做，D18）
- user.json 也在 extensions/ 目录中，会被正常加载

### 8.2 load_all 新增 user 层初始化

```python
def load_all(data_dir: str) -> dict:
    # ... 现有逻辑 ...

    # 确保 user.json 存在（首次启动时创建空文件）
    rules_ext_dir = os.path.join(rules_dir, "extensions")
    os.makedirs(rules_ext_dir, exist_ok=True)
    user_path = os.path.join(rules_ext_dir, "user.json")
    if not os.path.exists(user_path):
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump([], f)

    # 确保 source_config 中有 user 条目
    if "user" not in source_config["sources"]:
        source_config["sources"]["user"] = {
            "enabled": True,
            "priority": 999,
            "data_type": "rules",
        }
        save_source_config(data_dir, source_config)

    # ... 返回 state ...
```

---

## 九、source_config.json 格式升级

### 9.1 新格式

```json
{
  "sources": {
    "core": {
      "enabled": true,
      "priority": 0
    },
    "user": {
      "enabled": true,
      "priority": 999,
      "data_type": "rules"
    },
    "2070手册": {
      "enabled": true,
      "priority": 10,
      "mode": "extend",
      "data_type": "rules"
    }
  }
}
```

### 9.2 优先级层级

| 层级 | source | priority | 约束 |
|------|--------|----------|------|
| user | `"user"` | 999（固定） | 不可禁用、不可卸载、不可调优先级 |
| third_party | 扩展包名 | 1-998（可调） | 可禁用、可卸载 |
| core | `"core"` | 0（固定） | 不可禁用、不可卸载、不可调优先级 |

---

## 十、工具集变更总结

### 10.1 修改的工具

| 工具 | 改动点 |
|------|--------|
| `search_rules` | 新增扩展搜索 + 分层过滤 + Replace 遮蔽 + 来源标识 |
| `set_source_priority` | 新增 user 层保护 |
| `import_extension` | 强制 _category 验证 + _override_mode 验证 + user 层保护 |

### 10.2 新增的工具

| 工具 | 用途 |
|------|------|
| `remove_extension` | 物理卸载第三方扩展 |

### 10.3 不变的工具

| 工具 | 说明 |
|------|------|
| `roll` | 无关，不涉及规则数据 |
| `roll_table` | 暂不处理随机表扩展的分层（后续迭代） |
| `prepare_extension` | 预处理逻辑不变 |
| `list_sources` | 现有逻辑已能正确展示扩展状态 |

---

## 十一、实施步骤

1. **loader.py**：新增 user.json 初始化 + source_config user 条目
2. **server.py search_rules**：重写为分层查询逻辑
3. **server.py set_source_priority**：新增 user 层保护
4. **server.py import_extension**：新增 _category / _override_mode 验证 + user 保护
5. **server.py remove_extension**：新增工具
6. **验证**：通过 MCP stdio 端到端调用全部工具

---

## 十二、风险与边界

| 风险 | 缓解 |
|------|------|
| Replace 遮蔽匹配不精确（字段值部分匹配） | `_overrides` 值必须与 core 记录中某字段值**完全相等** |
| user.json 被意外删除 | load_all 启动时自动重建空文件 |
| 扩展记录缺少必填元数据 | import_extension 入口验证，拒绝不合规数据 |
| 大量扩展导致搜索变慢 | 实际场景扩展不超过 5 个，每个不超过 100 条，总量可控 |

---

## 十三、不在本次范围

- 随机表扩展的分层查询（roll_table 暂不改动）
- user 层的单条记录增删工具（暂由 AI 直接编辑 user.json）
- AI Skill `third-party-import` 的更新（需配合新字段，但属于 RPG 区职责）

---

> *"规则是骨架，扩展是肌肉，GM 的话是神经。骨架不能被替换，但肌肉可以换，神经说了算。"*
