#!/usr/bin/env python3
"""
BCD 合表脚本 — 将 .workbuddy/shared/artifacts/ 下的 16 个 JSON 合并为 6 个规则文件

输入：.workbuddy/shared/artifacts/*.json（16 个 BCD artifacts）
输出：mcp_server/data/rules/*.json（6 个规则文件 + index.json）

每条记录会自动添加元数据字段：
  _source: 规则层级（core/solo/third_party）
  _source_file: 原始来源文件名
  _category: MCP 分类键
"""

import json
import os
import sys

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, ".workbuddy", "shared", "artifacts")
OUTPUT_DIR = os.path.join(BASE_DIR, "mcp_server", "data", "rules")

# 合表映射：分类键 → 源文件列表
MERGE_MAP = {
    "injuries": [
        "B1_伤势状态.json",
        "B2_严重伤势_身体.json",
        "B3_严重伤势_头部.json",
    ],
    "combat": [
        "B4_动作列表.json",
        "B5_远程DV值.json",
        "B6_掩体耐久值.json",
    ],
    "vehicles": [
        "B7_载具表.json",
    ],
    "netrunner": [
        "C1_程序表.json",
        "C2_黑冰表.json",
        "C3_交互界面能力.json",
        "C4_网络建筑部件.json",
    ],
    "skills": [
        "D1_66技能映射.json",
    ],
    "services": [
        "D2_服务价格.json",
        "D3_住房选项.json",
        "D4_街头药物.json",
        "D5_夜市物品精选.json",
    ],
}

# 分类描述
DESCRIPTIONS = {
    "injuries": "伤势状态与严重伤势",
    "combat": "战斗动作、远程DV矩阵、掩体耐久",
    "vehicles": "载具属性",
    "netrunner": "程序、黑冰、交互界面能力、网络建筑",
    "skills": "66项技能映射",
    "services": "服务价格、住房、街头药物、夜市物品",
}


def determine_source(data_source: str) -> str:
    """根据 数据来源 字段推断 _source 层级"""
    if not data_source:
        return "core"
    # BCD artifacts 全部来自核心规则书
    if any(kw in data_source for kw in [
        "核心书", "核心规则书", "2-战斗", "3-技能", "4-装备",
        "5-网行", "6-GM", "7-掌上代理",
    ]):
        return "core"
    # 单人模式来源
    if any(kw in data_source for kw in ["9-单人模式", "单人游玩"]):
        return "solo"
    return "core"


def extract_source_file(data_source: str) -> str:
    """从 数据来源 字段提取最可能的源文件名"""
    if not data_source:
        return ""
    # 常见模式: "2-战斗规则.md" 或 "核心规则书_全量提取.md p123"
    import re
    # 匹配 xxx-xxx.md 或 xxx_xxx.md 模式
    match = re.search(r"([\d\w\u4e00-\u9fff\-]+\.md)", data_source)
    if match:
        return match.group(1)
    return data_source.split(" ")[0]


def enrich_record(record: dict, category: str) -> dict:
    """为单条记录添加元数据字段"""
    data_source = record.get("数据来源", "")
    return {
        **record,
        "_source": determine_source(data_source),
        "_source_file": extract_source_file(data_source),
        "_category": category,
    }


def merge_category(category: str, filenames: list) -> list:
    """合并同一分类下的多个源文件"""
    merged = []
    for filename in filenames:
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  警告: 文件不存在 {filepath}")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)
        if not isinstance(records, list):
            print(f"  警告: {filename} 不是 JSON 数组，跳过")
            continue
        for record in records:
            merged.append(enrich_record(record, category))
        print(f"  + {filename}: {len(records)} 条")
    return merged


def collect_fields(records: list) -> list:
    """收集所有记录的字段名并集（排除 _ 前缀的元数据字段）"""
    fields = set()
    for record in records:
        for key in record.keys():
            if not key.startswith("_"):
                fields.add(key)
    return sorted(list(fields))


def main():
    print("=" * 50)
    print("BCD 合表脚本")
    print(f"输入目录: {ARTIFACTS_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    index = []
    total_records = 0

    for category, filenames in MERGE_MAP.items():
        print(f"\n[{category}] 合并 {len(filenames)} 个文件...")
        merged = merge_category(category, filenames)
        total_records += len(merged)

        # 收集字段并集
        fields = collect_fields(merged)

        # 写出 JSON
        output_path = os.path.join(OUTPUT_DIR, f"{category}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"  → {category}.json: {len(merged)} 条, {size_kb:.1f}KB")
        print(f"     字段: {fields}")

        # 构建索引条目
        index.append({
            "category": category,
            "file": f"{category}.json",
            "description": DESCRIPTIONS.get(category, ""),
            "count": len(merged),
            "fields": fields,
        })

    # 写出 index.json
    index_path = os.path.join(OUTPUT_DIR, "index.json")
    
    # 保留已有的 equipment 条目（如果存在）
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            old_index = json.load(f)
        old_equipment = [e for e in old_index if e["category"] == "equipment"]
        if old_equipment and not any(e["category"] == "equipment" for e in index):
            index.extend(old_equipment)
            print(f"\n  ✓ 保留了 equipment 条目（{old_equipment[0]['count']} 条）")
    
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(index_path) / 1024
    print(f"\n→ index.json: {len(index)} 个分类, {size_kb:.1f}KB")

    print(f"\n{'=' * 50}")
    print(f"合计: {total_records} 条规则记录")
    print(f"输出: {OUTPUT_DIR}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
