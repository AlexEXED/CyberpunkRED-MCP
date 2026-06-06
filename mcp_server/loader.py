"""
loader.py — MCP Server 数据加载模块

启动时一次性加载所有数据到内存：
  - 7 个规则 JSON（486 条）
  - cyber.json（37 随机表 + 神谕 + 士气）
  - extensions/ 子目录（第三方扩展，如有）

返回一个 state dict 供所有工具函数消费。
"""

import json
import os


def load_rules(rules_dir: str) -> tuple[list, dict]:
    """加载规则数据

    Returns:
        index: index.json 的分类列表
        data: {category_name: [records...], ...}
    """
    index_path = os.path.join(rules_dir, "index.json")
    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    data = {}
    for entry in index:
        file_path = os.path.join(rules_dir, entry["file"])
        with open(file_path, encoding="utf-8") as f:
            records = json.load(f)
        data[entry["category"]] = records

    return index, data


def load_tables(rt_dir: str) -> dict:
    """加载随机表数据

    Returns:
        {
            "meta": {...},
            "tables": {"动词": {"dice":..., "rows":[...]}, ...},
            "oracle": {"必然": {...}, ...},
            "morale": [...]
        }
    """
    cyber_path = os.path.join(rt_dir, "cyber.json")
    with open(cyber_path, encoding="utf-8") as f:
        cyber = json.load(f)

    return {
        "meta": cyber.get("meta", {}),
        "tables": cyber.get("tables", {}),
        "oracle": cyber.get("oracle", {}),
        "morale": cyber.get("morale", []),
    }


def load_extensions(base_dir: str, data_type: str) -> list[dict]:
    """加载 extensions/ 子目录的扩展数据

    Args:
        base_dir: rules/ 或 random_tables/ 目录
        data_type: "rules" 或 "tables"

    Returns:
        [{"source": name, "data": ..., "mode": ...}, ...]
    """
    ext_dir = os.path.join(base_dir, "extensions")
    if not os.path.isdir(ext_dir):
        return []

    extensions = []
    for fname in sorted(os.listdir(ext_dir)):
        if not fname.endswith(".json"):
            continue
        file_path = os.path.join(ext_dir, fname)
        with open(file_path, encoding="utf-8") as f:
            ext_data = json.load(f)
        source_name = fname.replace(".json", "")
        extensions.append({
            "source": source_name,
            "file": fname,
            "data": ext_data,
        })

    return extensions


def load_source_config(data_dir: str) -> dict:
    """加载数据源优先级配置

    Returns:
        {"sources": {name: {"enabled": bool, "priority": int}, ...}}
    """
    config_path = os.path.join(data_dir, "source_config.json")
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    # 默认配置：core 始终启用，优先级最低
    return {"sources": {"core": {"enabled": True, "priority": 0}}}


def save_source_config(data_dir: str, config: dict):
    """保存数据源优先级配置。

    ⚠️ 跑团端是只读的——本函数仅用于启动期初始化（创建 user 条目等）。
    扩展导入、启用/禁用、卸载等运行时写入操作由备团 MCP 承担，不应在跑团端调用。
    """
    config_path = os.path.join(data_dir, "source_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_all(data_dir: str) -> dict:
    """一次性加载所有数据

    Args:
        data_dir: mcp_server/data/ 目录路径

    Returns:
        {
            "rules_index": [...],
            "rules_data": {"combat": [...], "equipment": [...], ...},
            "rules_extensions": [...],
            "tables": {"动词": {...}, ...},
            "oracle": {...},
            "morale": [...],
            "table_meta": {...},
            "tables_extensions": [...],
            "source_config": {...},
            "data_dir": str,
        }
    """
    rules_dir = os.path.join(data_dir, "rules")
    rt_dir = os.path.join(data_dir, "random_tables")

    # 核心数据
    rules_index, rules_data = load_rules(rules_dir)
    table_data = load_tables(rt_dir)

    # 源配置（先加载，便于决定是否需要写回 user 条目）
    source_config = load_source_config(data_dir)

    # 在加载扩展之前，确保 user.json 与 source_config["user"] 已就绪
    # 这样首次启动时 user 层也能进入内存，无需重启服务
    rules_ext_dir = os.path.join(rules_dir, "extensions")
    os.makedirs(rules_ext_dir, exist_ok=True)
    user_path = os.path.join(rules_ext_dir, "user.json")
    if not os.path.exists(user_path):
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump([], f)

    if "user" not in source_config["sources"]:
        source_config["sources"]["user"] = {
            "enabled": True,
            "priority": 999,
            "data_type": "rules",
        }
        save_source_config(data_dir, source_config)

    # 扩展数据（此时 user.json 必然存在）
    rules_ext = load_extensions(rules_dir, "rules")
    tables_ext = load_extensions(rt_dir, "tables")

    # 统计
    total_rules = sum(len(v) for v in rules_data.values())
    total_tables = len(table_data["tables"])
    total_ext_rules = sum(
        len(e["data"]) if isinstance(e["data"], list) else 0
        for e in rules_ext
    )

    state = {
        "rules_index": rules_index,
        "rules_data": rules_data,
        "rules_extensions": rules_ext,
        "tables": table_data["tables"],
        "oracle": table_data["oracle"],
        "morale": table_data["morale"],
        "table_meta": table_data["meta"],
        "tables_extensions": tables_ext,
        "source_config": source_config,
        "data_dir": data_dir,
    }

    import sys
    print(f"[loader] 已加载: {total_rules} 条规则 ({len(rules_data)} 分类)"
          f" + {total_tables} 张随机表"
          f" + {len(rules_ext)} 个规则扩展（{total_ext_rules} 条扩展记录）"
          f" + {len(tables_ext)} 个表扩展", file=sys.stderr)

    return state
