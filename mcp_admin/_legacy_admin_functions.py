"""
v2 管理函数代码归档（legacy）
=============================

本文件保存 v2 跑团 MCP 中的 5 个管理工具函数代码，作为备团 MCP 实施时的参考基线。

⚠️ **不要直接复用**。这些函数基于 v2 的"扁平 JSON + 单层第三方"模型，不符合 v3 原则：
  - v3 要求"包目录结构"（manifest.json + data/ + source/）
  - v3 要求"两阶段流程"（preprocess + commit）
  - v3 要求"包级依赖 + 拓扑加载"
  - v3 要求"工作流外化"（manifest 状态机 + CLI 强制校验）

这些函数应当在 v3 备团 MCP 实施时**重构**：
  - 业务逻辑（验证规则、写盘、依赖检查）可以参考
  - 接口签名、状态管理需要重新设计
  - 测试用例（v2 烟雾测试 41/41）可作为回归基线

---

迁出时间：2026-05-07（v3 阶段 1：跑团端瘦身）
迁出来源：mcp_server/server.py（v2 完整实现，41/41 烟雾测试通过）
迁出原因：跑团 MCP 转为只读，所有写能力下沉到备团 MCP
"""

import json
import os
import re

# ⚠️ 这些函数依赖于跑团端的 state 和 save_source_config 全局符号
# 备团 MCP 实施时需重构为：第一参数接收 state，避免全局依赖

VALID_CATEGORIES = ["injuries", "combat", "vehicles", "netrunner", "skills", "services", "equipment"]


# ════════════════════════════════════════
#  v2 函数 1：prepare_extension
# ════════════════════════════════════════

def prepare_extension(file_path: str, extract_mode: str = "auto") -> dict:
    """预处理第三方文档，提取表格和文本内容供审核。

    支持 PDF/Word/Excel/CSV/Markdown/纯文本。
    输出提取摘要，不做最终导入决策。

    ⚠️ v3 决议：此函数不再作为 MCP 工具暴露。
    PDF/DOCX/XLSX 应由 AI 直接用 IDE 内置 skill 读取，比此工具靠谱十倍。
    本函数代码仅作 JSON/CSV/MD 简单检视的逻辑参考。
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()
    file_name = os.path.basename(file_path)

    result = {
        "file": file_name,
        "format": ext,
        "extract_mode": extract_mode,
        "tables": [],
        "text_sections": [],
    }

    try:
        if ext in (".csv", ".tsv"):
            import csv
            delimiter = "\t" if ext == ".tsv" else ","
            with open(file_path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
            if rows:
                result["tables"].append({
                    "headers": rows[0],
                    "rows": len(rows) - 1,
                    "sample": rows[1:4],
                    "suggested_type": "rules",
                })

        elif ext == ".md":
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            table_blocks = re.findall(
                r"((?:^\|.+\|$\n?)+)", content, re.MULTILINE
            )
            for block in table_blocks:
                lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
                if len(lines) >= 2:
                    headers = [c.strip() for c in lines[0].strip("|").split("|")]
                    result["tables"].append({
                        "headers": headers,
                        "rows": len(lines) - 2,
                        "suggested_type": "rules",
                    })
            headings = re.findall(r"^(#{1,4})\s+(.+)$", content, re.MULTILINE)
            for level, title in headings[:10]:
                result["text_sections"].append({
                    "level": len(level),
                    "title": title,
                })

        elif ext == ".txt":
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            result["text_sections"].append({
                "content_preview": content[:500],
                "total_chars": len(content),
            })

        elif ext == ".json":
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                result["tables"].append({
                    "type": "json_array",
                    "rows": len(data),
                    "sample": data[:2] if data else [],
                    "suggested_type": "rules",
                })
            elif isinstance(data, dict):
                result["tables"].append({
                    "type": "json_object",
                    "keys": list(data.keys())[:10],
                    "suggested_type": "tables",
                })

        else:
            result["hint"] = (
                f"格式 {ext} 需要 AI 协助处理。"
                f"建议：PDF 请使用 WorkBuddy 的 PDF 读取功能先提取文本，"
                f"Word/Excel 请先另存为 CSV 或 Markdown。"
            )

    except Exception as e:
        result["error"] = f"提取失败: {e}"

    result["summary"] = (
        f"发现 {len(result['tables'])} 个表格, "
        f"{len(result['text_sections'])} 个文本段落"
    )

    return result


# ════════════════════════════════════════
#  v2 函数 2：import_extension
# ════════════════════════════════════════

def import_extension(state, save_source_config_fn, source_name: str, data_type: str,
                      file_path: str, mode: str = "extend") -> dict:
    """导入经审核的第三方扩展包。

    ⚠️ v3 重构方向：
      - 接受"包目录"而非"单 JSON"
      - 阶段化：preprocess（生成中间产物）+ commit（验证后落地）
      - manifest.json 驱动，记录提取进度
      - 包级依赖声明（depends_on）
    """
    if source_name == "user":
        return {"success": False, "error": "user 层不可通过 import_extension 导入"}
    if data_type not in ("rules", "tables"):
        return {"success": False, "error": f"data_type 必须是 rules 或 tables，收到: {data_type}"}
    if mode not in ("extend", "override"):
        return {"success": False, "error": f"mode 必须是 extend 或 override，收到: {mode}"}
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    with open(file_path, encoding="utf-8") as f:
        ext_data = json.load(f)

    if data_type == "rules":
        ext_dir = os.path.join(state["data_dir"], "rules", "extensions")
    else:
        ext_dir = os.path.join(state["data_dir"], "random_tables", "extensions")

    os.makedirs(ext_dir, exist_ok=True)

    imported = 0
    overridden = 0
    if data_type == "rules" and isinstance(ext_data, list):
        # 第一遍：全量验证
        for idx, record in enumerate(ext_data):
            if not isinstance(record, dict):
                return {"success": False, "error": f"第 {idx} 条记录不是对象: {type(record).__name__}"}
            if record.get("_category") not in VALID_CATEGORIES:
                return {
                    "success": False,
                    "error": f"第 {idx} 条记录的 _category 必须是标准分类之一: {VALID_CATEGORIES}，收到: {record.get('_category')}",
                }
            override_mode = record.get("_override_mode", "add")
            if override_mode not in ("add", "replace", "extend"):
                return {
                    "success": False,
                    "error": f"第 {idx} 条记录的 _override_mode 必须是 add/replace/extend，收到: {override_mode}",
                }

        # 第二遍：注入元数据
        for record in ext_data:
            record["_source"] = source_name
            record["_source_file"] = os.path.basename(file_path)
            record["_override_mode"] = record.get("_override_mode", "add")
            imported += 1

    elif data_type == "tables" and isinstance(ext_data, dict):
        for tbl_name, tbl_data in ext_data.items():
            if isinstance(tbl_data, dict):
                tbl_data["_source"] = source_name
                imported += 1
                if mode == "override" and tbl_name in state["tables"]:
                    overridden += 1

    output_path = os.path.join(ext_dir, f"{source_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ext_data, f, ensure_ascii=False, indent=2)

    config = state["source_config"]
    config["sources"][source_name] = {
        "enabled": True,
        "priority": 10,
        "mode": mode,
        "data_type": data_type,
    }
    save_source_config_fn(state["data_dir"], config)
    state["source_config"] = config

    from loader import load_extensions
    if data_type == "rules":
        state["rules_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "rules"), "rules"
        )
    else:
        state["tables_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "random_tables"), "tables"
        )

    return {
        "source": source_name,
        "type": data_type,
        "mode": mode,
        "imported": imported,
        "overridden": overridden,
        "output_file": output_path,
    }


# ════════════════════════════════════════
#  v2 函数 3：list_sources
# ════════════════════════════════════════

def list_sources(state) -> dict:
    """查看已加载的数据源层级和优先级。

    ⚠️ v3 重构方向：扩展从"扁平 JSON"变为"包目录"，需要读 manifest.json，
    展示 extraction_progress、depends_on、版本号等更丰富信息。
    """
    sources = []

    total_rules = sum(len(v) for v in state["rules_data"].values())
    sources.append({
        "name": "core",
        "priority": 0,
        "enabled": True,
        "rules_count": total_rules,
        "tables_count": len(state["tables"]),
        "categories": list(state["rules_data"].keys()),
    })

    for ext in state["rules_extensions"]:
        src = ext["source"]
        cfg = state["source_config"]["sources"].get(src, {})
        count = len(ext["data"]) if isinstance(ext["data"], list) else 0
        sources.append({
            "name": src,
            "priority": cfg.get("priority", 10),
            "enabled": cfg.get("enabled", True),
            "rules_count": count,
            "tables_count": 0,
            "mode": cfg.get("mode", "extend"),
        })

    for ext in state["tables_extensions"]:
        src = ext["source"]
        cfg = state["source_config"]["sources"].get(src, {})
        count = len(ext["data"]) if isinstance(ext["data"], dict) else 0
        existing = next((s for s in sources if s["name"] == src), None)
        if existing:
            existing["tables_count"] = count
        else:
            sources.append({
                "name": src,
                "priority": cfg.get("priority", 10),
                "enabled": cfg.get("enabled", True),
                "rules_count": 0,
                "tables_count": count,
                "mode": cfg.get("mode", "extend"),
            })

    sources.sort(key=lambda s: s["priority"], reverse=True)

    return {
        "sources": sources,
        "total_rules": sum(s["rules_count"] for s in sources),
        "total_tables": sum(s["tables_count"] for s in sources),
    }


# ════════════════════════════════════════
#  v2 函数 4：set_source_priority
# ════════════════════════════════════════

def set_source_priority(state, save_source_config_fn, source_name: str,
                          enabled: bool = True, priority: int = None) -> dict:
    """设置数据源的启用状态和优先级。

    ⚠️ v3 注意事项：包级依赖检查应在禁用前进行（拒绝禁用被其他包依赖的扩展）。
    """
    if source_name == "core":
        return {"success": False, "error": "core 源不可禁用或调整优先级"}
    if source_name == "user":
        return {"success": False, "error": "user 层不可禁用或调整优先级"}

    config = state["source_config"]
    if source_name not in config["sources"]:
        return {"success": False, "error": f"未找到数据源: {source_name}"}

    src_cfg = config["sources"][source_name]
    src_cfg["enabled"] = enabled
    if priority is not None:
        src_cfg["priority"] = priority

    save_source_config_fn(state["data_dir"], config)
    state["source_config"] = config

    return {
        "source": source_name,
        "enabled": enabled,
        "priority": src_cfg.get("priority", 10),
    }


# ════════════════════════════════════════
#  v2 函数 5：remove_extension
# ════════════════════════════════════════

def remove_extension(state, save_source_config_fn, source_name: str) -> dict:
    """卸载第三方扩展包。物理删除扩展文件并清理配置。

    ⚠️ v3 重构方向：
      - 卸载策略改为"拒绝 + 提示"——若有其他扩展依赖此包，拒绝卸载
      - 包目录结构下需要删除整个目录（含 source/、data/、manifest.json）
    """
    if source_name == "core":
        return {"success": False, "error": "core 不可卸载"}
    if source_name == "user":
        return {"success": False, "error": "user 层不可卸载"}

    config = state["source_config"]
    if source_name not in config["sources"]:
        return {"success": False, "error": f"未找到扩展: {source_name}"}

    data_type = config["sources"][source_name].get("data_type", "rules")
    if data_type == "rules":
        ext_path = os.path.join(state["data_dir"], "rules", "extensions", f"{source_name}.json")
    else:
        ext_path = os.path.join(state["data_dir"], "random_tables", "extensions", f"{source_name}.json")

    if os.path.exists(ext_path):
        os.remove(ext_path)

    del config["sources"][source_name]
    save_source_config_fn(state["data_dir"], config)
    state["source_config"] = config

    from loader import load_extensions
    if data_type == "rules":
        state["rules_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "rules"), "rules"
        )
    else:
        state["tables_extensions"] = load_extensions(
            os.path.join(state["data_dir"], "random_tables"), "tables"
        )

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
        "hint": f"已卸载。{dormant_user_rules} 条 user 微调进入休眠状态。" if dormant_user_rules else "已卸载。",
    }
