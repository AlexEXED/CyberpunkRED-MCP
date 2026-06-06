#!/usr/bin/env python3
"""
生成所有MCP add_records调用所需的records数组(JSON文件)
text_value必须包含type:"text"
输出: 12个批次文件(每个≤5条),每条record都是完整MCP格式
"""
import json, os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
OUTPUT_DIR = os.path.join(INPUT_DIR, "mcp_insert")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH = 5

def tv(text):
    """text_value helper"""
    return {"text_value": {"items": [{"text": str(text), "type": "text"}]}}

def ov(text):
    """option_value helper"""
    return {"option_value": {"items": [{"text": str(text)}]}}

def nv(num):
    """number_value helper"""
    return {"number_value": num}

def bv(val):
    """bool_value helper"""
    return {"bool_value": bool(val)}

def w_rec(w):
    return {"field_values": [
        {"field": "武器名称", **tv(w["武器名称"])},
        {"field": "武器大类", **ov(w["武器大类"])},
        {"field": "武器子类", **tv(w["武器子类"])},
        {"field": "关联技能", **ov(w["关联技能"])},
        {"field": "伤害骰数", **nv(w["伤害骰数"])},
        {"field": "伤害面数", **nv(w["伤害面数"])},
        {"field": "伤害表达式", **tv(w["伤害表达式"])},
        {"field": "弹容", **tv(w["弹容"])},
        {"field": "ROF", **nv(w["ROF"])},
        {"field": "手数", **nv(w["手数"])},
        {"field": "可隐藏", **bv(w["可隐藏"])},
        {"field": "价格_eb", **nv(w["价格_eb"])},
        {"field": "特殊属性", **tv(w["特殊属性"] or " ")},
        {"field": "数据来源", **ov(w["数据来源"])}
    ]}

def a_rec(a):
    return {"field_values": [
        {"field": "护甲名称", **tv(a["护甲名称"])},
        {"field": "描述", **tv(a["描述"])},
        {"field": "SP", **nv(a["SP"])},
        {"field": "惩罚", **tv(a["惩罚"])},
        {"field": "价格_eb", **nv(a["价格_eb"])},
        {"field": "数据来源", **ov(a["数据来源"])}
    ]}

def am_rec(i):
    return {"field_values": [
        {"field": "物品名称", **tv(i["物品名称"])},
        {"field": "分类", **ov(i["分类"])},
        {"field": "描述", **tv(i["描述"])},
        {"field": "价格_eb", **nv(i["价格_eb"])},
        {"field": "价格备注", **tv(i.get("价格备注", "") or " ")},
        {"field": "数据来源", **ov(i["数据来源"])}
    ]}

jobs = [
    ('weapons.json', 'VBWgAlhuTShk', w_rec),
    ('armor.json', 'VBoLvnHbfPOD', a_rec),
    ('ammo_accessories.json', 'VrBWgtvpLgqp', am_rec),
]

manifest = []
for src, fid, builder in jobs:
    with open(os.path.join(INPUT_DIR, src), 'r', encoding='utf-8') as f:
        data = json.load(f)
    tbl = src.replace('.json', '')
    for i in range(0, len(data), BATCH):
        batch = data[i:i+BATCH]
        records = [builder(r) for r in batch]
        out = {"file_id": fid, "sheet_id": "t00i2h", "records": records}
        bnum = i // BATCH
        fname = f"{tbl}_b{bnum}.json"
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        manifest.append({"file": fname, "fid": fid, "count": len(records)})

# 输出清单
with open(os.path.join(OUTPUT_DIR, '_manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

total = sum(m["count"] for m in manifest)
print(f"Generated {len(manifest)} batch files, {total} total records")
for m in manifest:
    print(f"  {m['file']}: {m['count']} records -> {m['fid']}")
