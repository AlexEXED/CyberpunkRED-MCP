#!/usr/bin/env python3
"""
随机表索引生成脚本 — 从 cyber.json 生成 table_index.json

输入：mcp_server/data/random_tables/cyber.json
输出：mcp_server/data/random_tables/table_index.json
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYBER_JSON = os.path.join(BASE_DIR, "mcp_server", "data", "random_tables", "cyber.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "mcp_server", "data", "random_tables", "table_index.json")


def chinese_to_id(name: str) -> str:
    """将中文表名转为 snake_case ASCII id"""
    # 常见中文 → 英文映射（保持语义可读）
    cn_en = {
        "动词": "verb",
        "名词": "noun",
        "形容词": "adjective",
        "光景": "scenery",
        "声响": "sound",
        "气味": "smell",
        "NPC情绪": "npc_emotion",
        "角色职业": "role_occupation",
        " NPC 名字": "npc_name",
        "NPC关系": "npc_relationship",
        "遭遇钩子": "encounter_hook",
        "遭遇驱动力": "encounter_drive",
        "情节": "plot",
        "事件": "event",
        "地点": "location",
        "物品": "item",
        "奇物": "curiosity",
    }

    # 直接映射
    clean = name.strip()
    for cn, en in cn_en.items():
        if cn in clean:
            return en

    # 通用转换：去掉描述性后缀
    clean = re.sub(r"[_\s]*(描述|笔记|参考|补充).*", "", clean)
    clean = re.sub(r"[（(].*?[）)]", "", clean)
    clean = clean.strip()

    # 简单的中文 → 拼音/英文回退
    # 对于未映射的表名，用 hash 前 8 位
    simple_map = {
        "势力与派系": "faction",
        "企业名录": "corporation",
        "帮派": "gang",
        "游民宗族": "nomad_clan",
        "任务类型": "mission_type",
        "任务目标": "mission_objective",
        "任务复杂度": "mission_complexity",
        "任务报酬": "mission_reward",
        "任务转折": "mission_twist",
        "封闭式提问概率表": "oracle_closed",
        "开放式提问概率表": "oracle_open",
        "再掷概率表": "oracle_reroll",
        "BOSS困难": "boss_difficulty",
        "场景难度": "scene_difficulty",
        "难度递进": "difficulty_progression",
        "节拍": "beat",
        "节拍方向": "beat_direction",
        "强者时钟": "doom_clock",
        "时钟推进": "clock_advance",
        "士气与战斗意志表": "morale",
        "名词": "noun",
    }

    for cn, en in simple_map.items():
        if cn in clean:
            return en

    # 最终回退：取名字的前几个字的 hash
    return f"table_{hash(clean) & 0xFFFFFFFF:08x}"


def main():
    print("=" * 50)
    print("随机表索引生成脚本")
    print(f"输入: {CYBER_JSON}")
    print(f"输出: {OUTPUT_FILE}")
    print("=" * 50)

    with open(CYBER_JSON, "r", encoding="utf-8") as f:
        cyber = json.load(f)

    index = []

    # 处理 tables 中的标准随机表
    tables = cyber.get("tables", {})
    if isinstance(tables, dict):
        for name, table_data in tables.items():
            entry = {
                "id": chinese_to_id(name),
                "name": name,
                "dice": table_data.get("dice", ""),
                "type": "simple",
                "count": len(table_data.get("rows", [])),
            }
            index.append(entry)

    # 处理 oracle
    oracle = cyber.get("oracle", None)
    if oracle:
        index.append({
            "id": "oracle_closed",
            "name": "封闭式提问概率表",
            "dice": "1d100",
            "type": "oracle",
            "count": len(oracle) if isinstance(oracle, list) else 5,
        })

    # 处理 morale
    morale = cyber.get("morale", None)
    if morale:
        index.append({
            "id": "morale",
            "name": "士气与战斗意志表",
            "dice": "1d10",
            "type": "morale",
            "count": len(morale) if isinstance(morale, list) else 5,
        })

    # 处理 id 重复（追加 _2, _3）
    id_count = {}
    for entry in index:
        base_id = entry["id"]
        if base_id not in id_count:
            id_count[base_id] = 1
        else:
            id_count[base_id] += 1
            entry["id"] = f"{base_id}_{id_count[base_id]}"

    # 写出
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n→ table_index.json: {len(index)} 张表, {size_kb:.1f}KB")

    # 统计
    types = {}
    for e in index:
        t = e["type"]
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items()):
        print(f"  {t}: {c} 张")
    print(f"  合计: {len(index)}")

    # 打印部分条目
    print(f"\n前 10 张表:")
    for e in index[:10]:
        print(f"  {e['id']:25s} | {e['name']:20s} | {e['dice']:6s} | {e['type']:8s} | {e['count']}行")


if __name__ == "__main__":
    main()
