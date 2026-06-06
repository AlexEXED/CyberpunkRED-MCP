#!/usr/bin/env python3
"""
装备数据提取脚本 — 从 rules/4-装备与赛博组件.md 提取 ~142 条装备记录

输入：rules/4-装备与赛博组件.md（359 行）
输出：mcp_server/data/rules/equipment.json

提取策略：按段落逐段扫描，根据最近的 H2/H3/H4 标题确定子表类别。
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_FILE = os.path.join(BASE_DIR, "rules", "4-装备与赛博组件.md")
OUTPUT_FILE = os.path.join(BASE_DIR, "mcp_server", "data", "rules", "equipment.json")

SOURCE_NAME = "4-装备与赛博组件.md"
CATEGORY = "equipment"
SOURCE_LAYER = "core"


def strip_heading_noise(text: str) -> str:
    """去掉标题中的噪音：括号、方括号、空格"""
    # 先处理全角括号（最外层）
    text = re.sub(r"（.*?）", "", text)
    # 再处理方括号
    text = re.sub(r"【.*?】", "", text)
    # 最后处理半角括号（仅用于清理残留）
    text = re.sub(r"\(.*?\)", "", text)
    return text.strip()


def classify_table(h2: str, h3: str, h4: str) -> str | None:
    """根据上下文标题判断子表类别，返回 _item_type 或 None（跳过）"""
    # 按最具体的标题优先判断
    candidates = [h4, h3, h2]

    for heading in candidates:
        if not heading:
            continue
        clean = strip_heading_noise(heading)

        # 跳过参考表
        skip_keywords = [
            "价格分类参考", "基础规则", "组件安装级别", "赛博组件类型",
            "赛博碟板", "程序", "职业起始装备", "全量提取",
        ]
        if any(kw in heading for kw in skip_keywords):
            return "SKIP"

        # 近战武器
        if clean == "近战武器":
            return "近战武器"

        # 远程武器子类
        if clean in ("手枪类", "长枪类"):
            return f"远程武器_{clean}"

        # 异种武器
        if clean == "异种武器":
            return "异种武器"

        # 武器配件
        if clean == "武器配件":
            return "武器配件"

        # 弹药
        if clean == "弹药":
            return "弹药"

        # 护甲列表
        if "护甲列表" in clean or clean == "护甲":
            return "护甲"

        # 装备列表
        if "装备列表" in clean or clean == "装备":
            return "装备"

        # 赛博组件子类
        cyberware_map = {
            "时尚装置": "赛博组件_时尚装置",
            "神经组件": "赛博组件_神经组件",
            "赛博光学": "赛博组件_赛博光学",
            "赛博音频": "赛博组件_赛博音频",
            "体内赛博组件": "赛博组件_体内",
            "外周赛博组件": "赛博组件_外周",
            "赛博义肢": "赛博组件_义肢",
        }
        if clean in cyberware_map:
            return cyberware_map[clean]

    return None


def parse_table_lines(table_lines: list[str]) -> list[dict]:
    """解析收集到的表格行，返回记录列表"""
    rows = []
    for line in table_lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.match(r"^[-:]+$", c) for c in cells):
            continue
        if cells:
            rows.append(cells)

    if len(rows) < 2:
        return []

    header = rows[0]
    data_rows = rows[1:]
    records = []
    for row in data_rows:
        record = {}
        for i, key in enumerate(header):
            if i < len(row):
                val = row[i].strip()
                if val == "—":
                    record[key] = None
                else:
                    num_match = re.match(r"^(\d+)$", val)
                    record[key] = int(num_match.group(1)) if num_match else val
            else:
                record[key] = None
        records.append(record)
    return records


def main():
    print("=" * 50)
    print("装备数据提取脚本")
    print(f"输入: {SOURCE_FILE}")
    print(f"输出: {OUTPUT_FILE}")
    print("=" * 50)

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_records = []
    type_counts = {}
    table_lines = []
    h2 = h3 = h4 = ""

    def flush():
        nonlocal table_lines
        if not table_lines:
            return
        records = parse_table_lines(table_lines)
        table_lines = []

        if not records:
            return

        item_type = classify_table(h2, h3, h4)
        if item_type is None:
            print(f"  警告: 未识别子表 [{h2}] > [{h3}] > [{h4}]，跳过 {len(records)} 条")
            return
        if item_type == "SKIP":
            return

        enriched = [
            {
                **r,
                "数据来源": SOURCE_NAME,
                "_item_type": item_type,
                "_source": SOURCE_LAYER,
                "_source_file": SOURCE_NAME,
                "_category": CATEGORY,
            }
            for r in records
        ]
        all_records.extend(enriched)
        type_counts[item_type] = type_counts.get(item_type, 0) + len(records)
        print(f"  + {item_type}: {len(records)} 条")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#### "):
            flush()
            h4 = stripped[5:].strip()
            continue
        elif stripped.startswith("### "):
            flush()
            h3 = stripped[4:].strip()
            h4 = ""
            continue
        elif stripped.startswith("## "):
            flush()
            h2 = stripped[3:].strip()
            h3 = ""
            h4 = ""
            continue
        elif stripped.startswith("# "):
            flush()
            continue

        if stripped.startswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            flush()

    flush()

    # 排序
    all_records.sort(key=lambda r: r.get("_item_type", ""))

    # 写出
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    total = sum(type_counts.values())
    print(f"\n→ equipment.json: {total} 条, {size_kb:.1f}KB")
    print(f"\n各子表统计:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print(f"  合计: {total}")


if __name__ == "__main__":
    main()
