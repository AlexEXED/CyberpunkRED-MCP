"""
Cyberpunk RED MCP Server — 跑团端（只读）
=========================================
3 个跑团专用工具：

  roll           — 掷骰子（基于 dice 库）
  search_rules   — 规则速查（分层搜索：core + 第三方扩展 + user 微调）
  roll_table     — 随机表掷骰（含神谕/士气）

---

定位：
  本服务器为跑团 AI 消费专用，**只读**数据层。
  不暴露任何数据导入、修改、扩展管理能力。
  所有写能力由独立的备团 MCP（mcp_admin/，待实施）或 CLI 兜底脚本承担。

技术栈：FastMCP 3.x + dice 4.0 + Python 3.13
"""

import json
import os
import re

import dice as dice_lib
from fastmcp import FastMCP

from loader import load_all

# ── 启动时加载数据 ──
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
state = load_all(DATA_DIR)

mcp = FastMCP(
    "CyberpunkRED",
    instructions=(
        "赛博朋克 RED TTRPG 跑团专用 MCP。\n"
        "工具：roll（掷骰）/ search_rules（规则查询）/ roll_table（随机表）。\n"
        "search_rules 已支持分层搜索：core 规则 + 已启用的第三方扩展 + user 微调，"
        "结果带 source_layer（core/third_party/user）与 source_name 溯源。\n"
        "本服务器不提供任何写能力。如需导入或管理扩展数据，请使用独立的备团 MCP。"
    ),
)


# ════════════════════════════════════════
#  跑团工具
# ════════════════════════════════════════


@mcp.tool
def roll(expression: str) -> dict:
    """掷骰子。支持 1d10, 2d6+3, 1d100, d%, 3d10 等标准骰子表达式。

    返回每颗骰子的单独结果、修正值和总计。
    """
    expr = expression.strip().lower().replace(" ", "")

    # 提取修正值：匹配末尾的 +N 或 -N
    modifier = 0
    dice_part = expr
    m = re.match(r"^(\d*d[\d%]+)([+-]\d+)$", expr)
    if m:
        dice_part = m.group(1)
        modifier = int(m.group(2))

    try:
        result = dice_lib.roll(dice_part)
    except Exception as e:
        return {"success": False, "error": f"无效的骰子表达式: {expression} ({e})"}

    # 统一提取 rolls
    if hasattr(result, "__iter__"):
        rolls = list(result)
    else:
        rolls = [int(result)]

    total = sum(rolls) + modifier

    return {
        "expression": expression,
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
    }


def _match_record(record: dict, query: str) -> dict | None:
    """对单条记录做全字段子串匹配，返回最佳匹配信息或 None"""
    best_match = None
    best_priority = 99

    for key, value in record.items():
        if key.startswith("_"):
            continue
        val_str = str(value) if value is not None else ""
        if not val_str:
            continue

        if query == val_str:
            priority = 0  # 精确匹配
        elif val_str.startswith(query):
            priority = 1  # 开头匹配
        elif query in val_str:
            priority = 2  # 包含匹配
        else:
            continue

        if priority < best_priority:
            best_priority = priority
            best_match = key

    if best_match is not None:
        return {"field": best_match, "priority": best_priority}
    return None


def _clean_record(record: dict) -> dict:
    """构建返回记录（排除 _ 前缀元数据）"""
    return {k: v for k, v in record.items() if not k.startswith("_")}


@mcp.tool
def search_rules(query: str, category: str = None) -> dict:
    """在规则数据中搜索关键词（覆盖 core + 第三方扩展 + user 微调）。

    支持 7 个分类过滤: injuries/combat/vehicles/netrunner/skills/services/equipment
    对所有字段做子串匹配（自动 str 转换，兼容 int/str/None）。
    返回最多 10 条结果，按匹配优先级排序。
    结果包含 source_layer（core/third_party/user）和 source_name 来源标识。
    """
    if not query or not query.strip():
        return {"success": False, "error": "查询关键词不能为空"}

    query = query.strip()
    valid_categories = list(state["rules_data"].keys())

    if category and category not in valid_categories:
        return {
            "success": False,
            "error": f"无效的规则类别: {category}，可选: {', '.join(valid_categories)}",
        }

    # ── 收集所有层的匹配结果 ──
    all_results = []

    # 2a. 搜索 core 层
    core_scope = (
        {category: state["rules_data"][category]}
        if category
        else state["rules_data"]
    )
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

    # 2b. 搜索扩展层（rules_extensions，含 third_party 和 user）
    for ext in state["rules_extensions"]:
        ext_source = ext["source"]

        # 检查 enabled 状态（D18）
        src_cfg = state["source_config"]["sources"].get(ext_source, {})
        if not src_cfg.get("enabled", True):
            continue

        ext_data = ext["data"]
        if not isinstance(ext_data, list):
            continue

        for record in ext_data:
            # 分类过滤
            rec_category = record.get("_category", "")
            if category and rec_category != category:
                continue

            # 记录级别的依赖检查（D21）
            # 依赖不存在（已卸载）或被禁用 → 此条记录休眠
            depends_on = record.get("_depends_on")
            if depends_on:
                dep_cfg = state["source_config"]["sources"].get(depends_on)
                if dep_cfg is None or not dep_cfg.get("enabled", True):
                    continue

            match = _match_record(record, query)
            if match:
                layer = "user" if ext_source == "user" else "third_party"
                all_results.append({
                    "source": rec_category or ext_source,
                    "source_layer": layer,
                    "source_name": ext_source,
                    "match_field": match["field"],
                    "match_priority": match["priority"],
                    "record": _clean_record(record),
                    "_override_mode": record.get("_override_mode", "add"),
                    "_overrides": record.get("_overrides"),
                    "_extends": record.get("_extends"),
                })

    # ── Replace 遮蔽处理（D15）──
    override_targets = set()
    for r in all_results:
        if r.get("_override_mode") == "replace" and r.get("_overrides"):
            override_targets.add((r["source"], r["_overrides"]))

    if override_targets:
        filtered = []
        for r in all_results:
            if r["source_layer"] == "core":
                is_overridden = False
                for target_cat, target_key in override_targets:
                    if r["source"] == target_cat:
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

    # ── 排序：match_priority（精确>开头>包含），同优先级按层级（user > third_party > core）──
    layer_order = {"user": 0, "third_party": 1, "core": 2}
    all_results.sort(
        key=lambda r: (r["match_priority"], layer_order.get(r["source_layer"], 9))
    )

    # ── 截断 + 清理内部字段 ──
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


@mcp.tool
def roll_table(table_name: str, roll_value: int = None) -> dict:
    """在随机表中掷骰。支持 37 张标准表 + 神谕（5级概率）+ 士气（5种敌人）。

    table_name: 表名（支持精确匹配和模糊匹配）
    roll_value: 手动指定骰值（可选，不指定则自动掷骰）

    返回掷骰结果、命中行的索引和范围（用于偏移量计算）。
    """
    tables = state["tables"]
    oracle = state["oracle"]
    morale = state["morale"]

    name = table_name.strip()

    # ── 神谕特殊处理 ──
    oracle_keywords = ["神谕", "oracle", "概率", "封闭式", "开放式"]
    if any(kw in name.lower() for kw in oracle_keywords):
        # 确定概率等级
        level = None
        for lv in oracle.keys():
            if lv in name:
                level = lv
                break
        if level is None:
            return {
                "type": "oracle",
                "levels": list(oracle.keys()),
                "hint": "请指定概率等级，如: roll_table('神谕 50/50')",
            }
        # 掷 d100
        rv = roll_value if roll_value else int(sum(list(dice_lib.roll("1d100"))))
        # 查找命中
        for result_name, ranges in oracle[level].items():
            if ranges[0] <= rv <= ranges[1]:
                return {
                    "type": "oracle",
                    "level": level,
                    "dice": "1d100",
                    "roll": rv,
                    "result": result_name,
                    "range": {"min": ranges[0], "max": ranges[1]},
                    "source": "core",
                    "table_version": state["table_meta"].get("version", "1.0"),
                }
        return {"type": "oracle", "level": level, "roll": rv, "result": "未命中"}

    # ── 士气特殊处理 ──
    morale_keywords = ["士气", "morale", "战斗意志"]
    if any(kw in name.lower() for kw in morale_keywords):
        return {
            "type": "morale",
            "entries": [
                {"enemy_type": m[0], "flee_range": m[1], "fight_range": m[2]}
                for m in morale
            ],
            "hint": "士气表需配合 d10 出目和敌人类型使用",
        }

    # ── 标准表查找 ──
    # 1. 精确匹配
    if name in tables:
        return _roll_on_table(name, tables[name], roll_value)

    # 2. 模糊匹配
    matches = {k: v for k, v in tables.items() if name in k}
    if len(matches) == 1:
        matched_name = list(matches.keys())[0]
        return _roll_on_table(matched_name, matches[matched_name], roll_value)
    elif len(matches) > 1:
        return {
            "type": "ambiguous",
            "query": name,
            "matches": [
                {"name": k, "dice": v["dice"], "rows": len(v["rows"])}
                for k, v in matches.items()
            ],
            "hint": f"找到 {len(matches)} 个匹配，请指定更精确的表名",
        }

    # 3. 反向模糊：表名中包含查询的任意词
    words = name.split()
    matches = {k: v for k, v in tables.items() if any(w in k for w in words)}
    if len(matches) == 1:
        matched_name = list(matches.keys())[0]
        return _roll_on_table(matched_name, matches[matched_name], roll_value)
    elif len(matches) > 1:
        return {
            "type": "ambiguous",
            "query": name,
            "matches": [
                {"name": k, "dice": v["dice"], "rows": len(v["rows"])}
                for k, v in matches.items()
            ],
        }

    return {"success": False, "error": f"未找到表名: {name}"}


def _roll_on_table(name: str, table: dict, manual_roll: int = None) -> dict:
    """在单张表上掷骰并返回结果"""
    dice_spec = table["dice"]
    rows = table["rows"]

    # 掷骰
    if manual_roll is not None:
        rv = manual_roll
    else:
        result = dice_lib.roll(dice_spec)
        rv = int(sum(list(result)))

    # 查找命中行
    for idx, row in enumerate(rows):
        if row["min"] <= rv <= row["max"]:
            return {
                "table_name": name,
                "dice": dice_spec,
                "roll": rv,
                "result": row["text"],
                "result_index": idx,
                "result_min": row["min"],
                "result_max": row["max"],
                "type": "simple",
                "source": "core",
                "table_version": state["table_meta"].get("version", "1.0"),
            }

    return {
        "table_name": name,
        "dice": dice_spec,
        "roll": rv,
        "result": None,
        "error": f"骰值 {rv} 未命中任何行（表范围 {rows[0]['min']}-{rows[-1]['max']}）",
    }


# ════════════════════════════════════════
#  启动
# ════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
