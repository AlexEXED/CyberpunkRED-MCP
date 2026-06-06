#!/usr/bin/env python3
"""
从原始weapons.json/armor.json/ammo_accessories.json构造精简MCP插入参数
输出: 每张表一个精简records JSON（去掉type字段，MCP不验证）
"""
import json, os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
OUTPUT_DIR = INPUT_DIR

def weapon_rec(w):
    return {
        "field_values": [
            {"field": "武器名称", "text_value": {"items": [{"text": w["武器名称"]}]}},
            {"field": "武器大类", "option_value": {"items": [{"text": w["武器大类"]}]}},
            {"field": "武器子类", "text_value": {"items": [{"text": w["武器子类"]}]}},
            {"field": "关联技能", "option_value": {"items": [{"text": w["关联技能"]}]}},
            {"field": "伤害骰数", "number_value": w["伤害骰数"]},
            {"field": "伤害面数", "number_value": w["伤害面数"]},
            {"field": "伤害表达式", "text_value": {"items": [{"text": w["伤害表达式"]}]}},
            {"field": "弹容", "text_value": {"items": [{"text": w["弹容"]}]}},
            {"field": "ROF", "number_value": w["ROF"]},
            {"field": "手数", "number_value": w["手数"]},
            {"field": "可隐藏", "bool_value": w["可隐藏"]},
            {"field": "价格_eb", "number_value": w["价格_eb"]},
            {"field": "特殊属性", "text_value": {"items": [{"text": w["特殊属性"]}]}},
            {"field": "数据来源", "option_value": {"items": [{"text": w["数据来源"]}]}}
        ]
    }

def armor_rec(a):
    return {
        "field_values": [
            {"field": "护甲名称", "text_value": {"items": [{"text": a["护甲名称"]}]}},
            {"field": "描述", "text_value": {"items": [{"text": a["描述"]}]}},
            {"field": "SP", "number_value": a["SP"]},
            {"field": "惩罚", "text_value": {"items": [{"text": a["惩罚"]}]}},
            {"field": "价格_eb", "number_value": a["价格_eb"]},
            {"field": "数据来源", "option_value": {"items": [{"text": a["数据来源"]}]}}
        ]
    }

def ammo_rec(i):
    return {
        "field_values": [
            {"field": "物品名称", "text_value": {"items": [{"text": i["物品名称"]}]}},
            {"field": "分类", "option_value": {"items": [{"text": i["分类"]}]}},
            {"field": "描述", "text_value": {"items": [{"text": i["描述"]}]}},
            {"field": "价格_eb", "number_value": i["价格_eb"]},
            {"field": "价格备注", "text_value": {"items": [{"text": i.get("价格备注", "")}]}},
            {"field": "数据来源", "option_value": {"items": [{"text": i["数据来源"]}]}}
        ]
    }

for name, builder, src in [
    ('weapons_ins.json', weapon_rec, 'weapons.json'),
    ('armor_ins.json', armor_rec, 'armor.json'),
    ('ammo_ins.json', ammo_rec, 'ammo_accessories.json')
]:
    with open(os.path.join(INPUT_DIR, src), 'r', encoding='utf-8') as f:
        data = json.load(f)
    records = [builder(row) for row in data]
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, separators=(',', ':'))
    print(f"{name}: {len(records)} records, {os.path.getsize(path)} bytes")

# 拆分武器为2批
with open(os.path.join(INPUT_DIR, 'weapons_ins.json'), 'r', encoding='utf-8') as f:
    weapons = json.load(f)
for i, batch in enumerate([weapons[:20], weapons[20:]]):
    path = os.path.join(OUTPUT_DIR, f'weapons_ins_b{i}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, separators=(',', ':'))
    print(f"weapons_ins_b{i}.json: {len(batch)} records, {os.path.getsize(path)} bytes")
