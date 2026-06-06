#!/usr/bin/env python3
"""
将MCP请求JSON拆分为≤20行的批次文件，方便逐批调用MCP
"""
import json, os

INPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"
BATCH_SIZE = 20

for name in ['weapons_mcp.json', 'armor_mcp.json', 'ammo_mcp.json']:
    with open(os.path.join(INPUT_DIR, name), 'r', encoding='utf-8') as f:
        records = json.load(f)
    base = name.replace('_mcp.json', '')
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        batch_file = os.path.join(INPUT_DIR, f"{base}_batch{i//BATCH_SIZE}.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False)
        print(f"{base}_batch{i//BATCH_SIZE}.json: {len(batch)} records")
