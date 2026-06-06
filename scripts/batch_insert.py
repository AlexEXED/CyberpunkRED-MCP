"""Generate MCP insert payloads for all BCD batch tables."""
import json, os, time

ARTIFACTS = r'C:\Users\Administrator\WorkBuddy\CyberpunkRED\.workbuddy\shared\artifacts'
OUTPUT = r'C:\Users\Administrator\WorkBuddy\CyberpunkRED\.workbuddy\shared\insert_payloads'
os.makedirs(OUTPUT, exist_ok=True)

# Field title mappings: JSON key -> SmartSheet field title
# Only list mismatches; defaults use JSON key as-is
FIELD_MAP = {
    'B5_远程DV值.json': {'距离范围': '距离段', '备注': '描述'},
    'B6_掩体耐久值.json': {'SP值': 'SP', 'HP值': 'HP'},
}

# Table definitions: (file_id, json_filename, field_overrides)
TABLES = [
    # B batch
    ('VhgoVpdZPtJr', 'B1_伤势状态.json'),  # DONE
    ('VBdQdOGfvRbF', 'B2_严重伤势_身体.json'),
    ('VhvizmyFiSKY', 'B3_严重伤势_头部.json'),
    ('VdiTsNSDQREz', 'B4_动作列表.json'),
    ('VgnBlEFOzmKN', 'B5_远程DV值.json'),
    ('VJkUrGcGkpSi', 'B6_掩体耐久值.json'),
    ('VDpDzvToiHuH', 'B7_载具表.json'),
    # C batch
    ('VOQxpbCjplZP', 'C1_程序表.json'),
    ('VuXwUYqxrSlr', 'C2_黑冰表.json'),
    ('VvyfkCWKrdQX', 'C3_交互界面能力.json'),
    ('VvJTBhABYoWo', 'C4_网络建筑部件.json'),
    # D batch
    ('VbtysxvoqQKx', 'D1_66技能映射.json'),
    ('VuiiPGcJIyqq', 'D2_服务价格.json'),
    ('VUBzqrbmYxiV', 'D3_住房选项.json'),
    ('VHCHmOleSIHN', 'D4_街头药物.json'),
    ('VKiJCFApmfon', 'D5_夜市物品精选.json'),
]

SHEET_ID = 't00i2h'
BATCH_SIZE = 20

for file_id, json_file in TABLES:
    if json_file == 'B1_伤势状态.json':
        continue  # already done
    
    fpath = os.path.join(ARTIFACTS, json_file)
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mapping = FIELD_MAP.get(json_file, {})
    
    records = []
    for row in data:
        fv = []
        for json_key, value in row.items():
            title = mapping.get(json_key, json_key)  # apply mapping or use as-is
            
            if isinstance(value, bool):
                fv.append({'field': title, 'bool_value': value})
            elif isinstance(value, (int, float)):
                fv.append({'field': title, 'number_value': value})
            elif json_key in ('数据来源',) or json_key.endswith('来源') or title.endswith('来源'):
                # select field - use text_value with items (MCP handles conversion)
                fv.append({'field': title, 'text_value': {'items': [{'text': str(value) if value else ' ', 'type': 'text'}]}})
            elif value == '':
                fv.append({'field': title, 'text_value': {'items': [{'text': ' ', 'type': 'text'}]}})
            else:
                fv.append({'field': title, 'text_value': {'items': [{'text': str(value), 'type': 'text'}]}})
        
        records.append({'field_values': fv})
    
    # Split into batches
    batches = [records[i:i+BATCH_SIZE] for i in range(0, len(records), BATCH_SIZE)]
    
    for bi, batch in enumerate(batches):
        batch_file = f'{json_file.replace(".json","")}_batch{bi}.json'
        payload = {
            'file_id': file_id,
            'sheet_id': SHEET_ID,
            'records': batch
        }
        outpath = os.path.join(OUTPUT, batch_file)
        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    
    print(f'{json_file}: {len(data)} rows → {len(batches)} batch(es)')

print(f'\nAll payloads saved to {OUTPUT}')
print(f'Total files: {len(os.listdir(OUTPUT))}')
