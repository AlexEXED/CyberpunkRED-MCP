#!/usr/bin/env python3
"""
生成MCP add_records调用所需的确切records数组
每个批次输出为独立JSON文件，records已经是MCP格式
"""
import json, os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
OUTPUT_DIR = os.path.join(INPUT_DIR, "mcp_calls")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH = 5

def w_rec(w):
    return {"field_values": [
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
    ]}

def a_rec(a):
    return {"field_values": [
        {"field": "护甲名称", "text_value": {"items": [{"text": a["护甲名称"]}]}},
        {"field": "描述", "text_value": {"items": [{"text": a["描述"]}]}},
        {"field": "SP", "number_value": a["SP"]},
        {"field": "惩罚", "text_value": {"items": [{"text": a["惩罚"]}]}},
        {"field": "价格_eb", "number_value": a["价格_eb"]},
        {"field": "数据来源", "option_value": {"items": [{"text": a["数据来源"]}]}}
    ]}

def am_rec(i):
    return {"field_values": [
        {"field": "物品名称", "text_value": {"items": [{"text": i["物品名称"]}]}},
        {"field": "分类", "option_value": {"items": [{"text": i["分类"]}]}},
        {"field": "描述", "text_value": {"items": [{"text": i["描述"]}]}},
        {"field": "价格_eb", "number_value": i["价格_eb"]},
        {"field": "价格备注", "text_value": {"items": [{"text": i.get("价格备注", "")}]}},
        {"field": "数据来源", "option_value": {"items": [{"text": i["数据来源"]}]}}
    ]}

for src, fid, sid, builder in [
    ('weapons.json', 'VBWgAlhuTShk', 't00i2h', w_rec),
    ('armor.json', 'VBoLvnHbfPOD', 't00i2h', a_rec),
    ('ammo_accessories.json', 'VrBWgtvpLgqp', 't00i2h', am_rec),
]:
    with open(os.path.join(INPUT_DIR, src), 'r', encoding='utf-8') as f:
        data = json.load(f)
    for i in range(0, len(data), BATCH):
        batch = data[i:i+BATCH]
        records = [builder(r) for r in batch]
        call = {"file_id": fid, "sheet_id": sid, "records": records}
        tbl = src.replace('.json','')
        bnum = i // BATCH
        path = os.path.join(OUTPUT_DIR, f"{tbl}_b{bnum}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(call, f, ensure_ascii=False, separators=(',', ':'))
        print(f"{tbl}_b{bnum}.json: {len(records)} records, {os.path.getsize(path)} bytes")

# 输出调用清单
print("\n=== MCP调用清单 ===")
for fname in sorted(os.listdir(OUTPUT_DIR)):
    with open(os.path.join(OUTPUT_DIR, fname), 'r', encoding='utf-8') as f:
        call = json.load(f)
    print(f"  {fname}: file_id={call['file_id']}, records={len(call['records'])}")
