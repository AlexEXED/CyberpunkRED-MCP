#!/usr/bin/env python3
"""
将解析输出的JSON转换为MCP add_records可用的请求体
输出: 3个request JSON文件
"""
import json
import os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
OUTPUT_DIR = INPUT_DIR

def build_weapon_record(w):
    return {
        "field_values": [
            {"field": "武器名称", "text_value": {"items": [{"text": w["武器名称"], "type": "text"}]}},
            {"field": "武器大类", "option_value": {"items": [{"text": w["武器大类"]}]}},
            {"field": "武器子类", "text_value": {"items": [{"text": w["武器子类"], "type": "text"}]}},
            {"field": "关联技能", "option_value": {"items": [{"text": w["关联技能"]}]}},
            {"field": "伤害骰数", "number_value": w["伤害骰数"]},
            {"field": "伤害面数", "number_value": w["伤害面数"]},
            {"field": "伤害表达式", "text_value": {"items": [{"text": w["伤害表达式"], "type": "text"}]}},
            {"field": "弹容", "text_value": {"items": [{"text": w["弹容"], "type": "text"}]}},
            {"field": "ROF", "number_value": w["ROF"]},
            {"field": "手数", "number_value": w["手数"]},
            {"field": "可隐藏", "bool_value": w["可隐藏"]},
            {"field": "价格_eb", "number_value": w["价格_eb"]},
            {"field": "特殊属性", "text_value": {"items": [{"text": w["特殊属性"], "type": "text"}]}},
            {"field": "数据来源", "option_value": {"items": [{"text": w["数据来源"]}]}}
        ]
    }

def build_armor_record(a):
    return {
        "field_values": [
            {"field": "护甲名称", "text_value": {"items": [{"text": a["护甲名称"], "type": "text"}]}},
            {"field": "描述", "text_value": {"items": [{"text": a["描述"], "type": "text"}]}},
            {"field": "SP", "number_value": a["SP"]},
            {"field": "惩罚", "text_value": {"items": [{"text": a["惩罚"], "type": "text"}]}},
            {"field": "价格_eb", "number_value": a["价格_eb"]},
            {"field": "数据来源", "option_value": {"items": [{"text": a["数据来源"]}]}}
        ]
    }

def build_ammo_record(i):
    return {
        "field_values": [
            {"field": "物品名称", "text_value": {"items": [{"text": i["物品名称"], "type": "text"}]}},
            {"field": "分类", "option_value": {"items": [{"text": i["分类"]}]}},
            {"field": "描述", "text_value": {"items": [{"text": i["描述"], "type": "text"}]}},
            {"field": "价格_eb", "number_value": i["价格_eb"]},
            {"field": "价格备注", "text_value": {"items": [{"text": i.get("价格备注", ""), "type": "text"}]}},
            {"field": "数据来源", "option_value": {"items": [{"text": i["数据来源"]}]}}
        ]
    }

def main():
    with open(os.path.join(INPUT_DIR, 'weapons.json'), 'r', encoding='utf-8') as f:
        weapons = json.load(f)
    with open(os.path.join(INPUT_DIR, 'armor.json'), 'r', encoding='utf-8') as f:
        armors = json.load(f)
    with open(os.path.join(INPUT_DIR, 'ammo_accessories.json'), 'r', encoding='utf-8') as f:
        ammo = json.load(f)

    weapon_records = [build_weapon_record(w) for w in weapons]
    armor_records = [build_armor_record(a) for a in armors]
    ammo_records = [build_ammo_record(i) for i in ammo]

    # 输出为可直接用于MCP调用的JSON
    for name, records in [('weapons_mcp.json', weapon_records),
                          ('armor_mcp.json', armor_records),
                          ('ammo_mcp.json', ammo_records)]:
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"{name}: {len(records)} records -> {path}")

if __name__ == '__main__':
    main()
