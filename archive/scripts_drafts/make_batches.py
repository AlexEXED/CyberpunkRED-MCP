#!/usr/bin/env python3
"""
将weapons/armor/ammo拆分为小批次(5条/批)，输出为单独JSON文件
供DeferExecuteTool逐批调用MCP add_records
"""
import json, os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
OUTPUT_DIR = os.path.join(INPUT_DIR, "batches")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH = 5
counter = 0

for src, file_id, sheet_id in [
    ('weapons.json', 'VBWgAlhuTShk', 't00i2h'),
    ('armor.json', 'VBoLvnHbfPOD', 't00i2h'),
    ('ammo_accessories.json', 'VrBWgtvpLgqp', 't00i2h'),
]:
    with open(os.path.join(INPUT_DIR, src), 'r', encoding='utf-8') as f:
        data = json.load(f)

    for i in range(0, len(data), BATCH):
        batch = data[i:i+BATCH]
        fname = f"batch_{counter:03d}_{src.replace('.json','')}_{i}.json"
        meta = {
            "file_id": file_id,
            "sheet_id": sheet_id,
            "table": src.replace('.json',''),
            "offset": i,
            "total": len(data),
            "records": batch
        }
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, separators=(',', ':'))
        counter += 1

    print(f"{src}: {len(data)} records -> {((len(data)-1)//BATCH)+1} batches")

print(f"\nTotal: {counter} batch files in {OUTPUT_DIR}")
