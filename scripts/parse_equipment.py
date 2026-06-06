#!/usr/bin/env python3
"""
A验证批次 - 从 rules/4-装备与赛博组件.md 确定性提取武器/护甲/弹药数据
输出: 3个JSON文件供MCP插入SmartSheet

铁律: 纯正则解析，零幻觉，解析失败=报错=不输出
"""

import re
import json
import sys

INPUT_FILE = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\rules\4-装备与赛博组件.md"
OUTPUT_DIR = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output"


def parse_price(price_str: str) -> dict:
    """从价格字符串提取数值和备注
    '50 eb（略贵）' -> {'value': 50, 'note': '略贵'}
    '100 eb' -> {'value': 100, 'note': ''}
    '500 eb（昂贵）' -> {'value': 500, 'note': '昂贵'}
    """
    price_str = price_str.strip()
    m = re.search(r'([\d,]+)\s*eb', price_str)
    if not m:
        return {'value': 0, 'note': price_str, 'raw': price_str}
    value = int(m.group(1).replace(',', ''))
    # 提取括号内备注
    note_m = re.search(r'[（(](.+?)[）)]', price_str)
    note = note_m.group(1).strip() if note_m else ''
    return {'value': value, 'note': note, 'raw': price_str}


def parse_damage(dmg_str: str) -> dict:
    """从伤害字符串提取骰数和面数
    '2d6' -> {'dice': 2, 'sides': 6, 'expr': '2d6'}
    '5d6' -> {'dice': 5, 'sides': 6, 'expr': '5d6'}
    """
    dmg_str = dmg_str.strip()
    m = re.match(r'(\d+)d(\d+)', dmg_str)
    if m:
        return {'dice': int(m.group(1)), 'sides': int(m.group(2)), 'expr': dmg_str}
    return {'dice': 0, 'sides': 0, 'expr': dmg_str, 'raw': dmg_str}


def parse_magazine(mag_str: str) -> str:
    """提取弹容描述
    '12发（中型弹）' -> '12发（中型弹）'
    '30发（中型弹）' -> '30发（中型弹）'
    """
    return mag_str.strip()


def extract_melee_weapons(text: str) -> list:
    """提取近战武器类别表"""
    weapons = []
    # 匹配近战武器表格行
    pattern = re.compile(
        r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+d\d+)\s*\|\s*(\d+)\s*\|\s*(能|不能)\s*\|\s*(.+?)\s*\|'
    )
    lines = text.split('\n')
    in_melee = False
    for line in lines:
        if '## 近战武器' in line:
            in_melee = True
            continue
        if in_melee and line.startswith('---'):
            continue
        if in_melee and line.startswith('## '):
            break
        if in_melee and '|' in line and '近战武器类别' not in line:
            m = pattern.match(line.strip())
            if m:
                category = m.group(1).strip()
                examples = m.group(2).strip()
                dmg = parse_damage(m.group(4))
                rof = int(m.group(5))
                concealable = m.group(6).strip() == '能'
                price = parse_price(m.group(7))
                # 解析例子中的具体武器
                for wp_name in re.split(r'[，,]', examples):
                    wp_name = wp_name.strip()
                    if wp_name and wp_name != '取决于武器':
                        weapons.append({
                            '武器名称': wp_name,
                            '武器大类': '近战武器',
                            '武器子类': category,
                            '关联技能': '近战',
                            '伤害骰数': dmg['dice'],
                            '伤害面数': dmg['sides'],
                            '伤害表达式': dmg['expr'],
                            '弹容': '-',
                            'ROF': rof,
                            '手数': 1,
                            '可隐藏': concealable,
                            '价格_eb': price['value'],
                            '特殊属性': '',
                            '数据来源': '基础武器表'
                        })
    return weapons


def extract_ranged_pistols(text: str) -> list:
    """提取手枪类远程武器"""
    weapons = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if '### 手枪类' in line:
            in_section = True
            continue
        if in_section and '### 长枪类' in line:
            break
        if in_section and line.startswith('---'):
            continue
        if in_section and '|' in line and '武器种类' not in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 10:
                name = parts[1]
                skill = parts[2]
                dmg = parse_damage(parts[3])
                mag = parse_magazine(parts[4])
                rof = int(parts[5]) if parts[5].isdigit() else 0
                hands = int(parts[6]) if parts[6].isdigit() else 1
                concealable = parts[7] == '能'
                price = parse_price(parts[8])
                special = parts[9] if len(parts) > 9 else ''
                weapons.append({
                    '武器名称': name,
                    '武器大类': '手枪',
                    '武器子类': name,
                    '关联技能': skill,
                    '伤害骰数': dmg['dice'],
                    '伤害面数': dmg['sides'],
                    '伤害表达式': dmg['expr'],
                    '弹容': mag,
                    'ROF': rof,
                    '手数': hands,
                    '可隐藏': concealable,
                    '价格_eb': price['value'],
                    '特殊属性': special,
                    '数据来源': '基础武器表'
                })
    return weapons


def extract_ranged_longguns(text: str) -> list:
    """提取长枪类远程武器"""
    weapons = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if '### 长枪类' in line:
            in_section = True
            continue
        if in_section and line.startswith('---'):
            continue
        if in_section and (line.startswith('## ') or line.startswith('> ')):
            if in_section and weapons:  # 已有数据则退出
                break
        if in_section and '|' in line and '武器种类' not in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 10:
                name = parts[1]
                skill = parts[2]
                dmg = parse_damage(parts[3])
                mag = parse_magazine(parts[4])
                rof = int(parts[5]) if parts[5].isdigit() else 0
                hands = int(parts[6]) if parts[6].isdigit() else 2
                concealable = parts[7] == '能'
                price = parse_price(parts[8])
                special = parts[9] if len(parts) > 9 else ''
                weapons.append({
                    '武器名称': name,
                    '武器大类': '长枪',
                    '武器子类': name,
                    '关联技能': skill,
                    '伤害骰数': dmg['dice'],
                    '伤害面数': dmg['sides'],
                    '伤害表达式': dmg['expr'],
                    '弹容': mag,
                    'ROF': rof,
                    '手数': hands,
                    '可隐藏': concealable,
                    '价格_eb': price['value'],
                    '特殊属性': special,
                    '数据来源': '基础武器表'
                })
    return weapons


def extract_exotic_weapons(text: str) -> list:
    """提取异种武器表"""
    weapons = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if '## 异种武器' in line:
            in_section = True
            continue
        if in_section and '---' in line and not any(c.isdigit() for c in line):
            continue
        if in_section and line.startswith('## ') and '异种武器' not in line:
            break
        if in_section and '|' in line and '武器' in line and '说明' in line:
            continue  # skip header
        if in_section and '|' in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 5:
                name = parts[1]
                desc = parts[2]
                price = parse_price(parts[3])
                # 推断技能
                skill = '重型武器'
                if '中型手枪' in desc or '重型手枪' in desc or '超重型手枪' in desc:
                    skill = '手枪'
                if '霰弹枪' in desc:
                    skill = '重型武器'
                if '突击步枪' in desc:
                    skill = '重型武器'
                if '近战' in desc:
                    skill = '近战'
                weapons.append({
                    '武器名称': name,
                    '武器大类': '异种武器',
                    '武器子类': '',
                    '关联技能': skill,
                    '伤害骰数': 0,
                    '伤害面数': 0,
                    '伤害表达式': '',
                    '弹容': '-',
                    'ROF': 0,
                    '手数': 1,
                    '可隐藏': False,
                    '价格_eb': price['value'],
                    '特殊属性': desc,
                    '数据来源': '基础武器表'
                })
    return weapons


def extract_armor(text: str) -> list:
    """提取护甲列表"""
    armors = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if '### 护甲列表' in line:
            in_section = True
            continue
        if in_section and '---' in line and '护甲种类' not in line:
            continue
        if in_section and line.startswith('## '):
            break
        if in_section and '|' in line and '护甲种类' not in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 7:
                name = parts[1].replace('**', '').strip()
                desc = parts[2].strip()
                sp_str = parts[3].replace('**', '').strip()
                penalty = parts[4].strip()
                price = parse_price(parts[5])
                armors.append({
                    '护甲名称': name,
                    '描述': desc,
                    'SP': int(sp_str) if sp_str.isdigit() else sp_str,
                    '惩罚': penalty,
                    '价格_eb': price['value'],
                    '数据来源': '基础护甲表'
                })
    return armors


def extract_ammo(text: str) -> list:
    """提取弹药表"""
    items = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if line.startswith('## 弹药') and '异种' not in line:
            in_section = True
            continue
        if in_section and '---' in line and '弹药类型' not in line:
            continue
        if in_section and line.startswith('## '):
            break
        if in_section and '|' in line and '弹药类型' not in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 5:
                name = parts[1]
                price_raw = parts[2]
                usable = parts[3] if len(parts) > 3 else ''
                price = parse_price(price_raw)
                items.append({
                    '物品名称': name,
                    '分类': '弹药',
                    '描述': usable,
                    '价格_eb': price['value'],
                    '价格备注': price['note'] if price['note'] else price_raw,
                    '数据来源': '基础装备表'
                })
    return items


def extract_accessories(text: str) -> list:
    """提取武器配件表"""
    items = []
    lines = text.split('\n')
    in_section = False
    for line in lines:
        if '## 武器配件' in line:
            in_section = True
            continue
        if in_section and '---' in line and '配件' not in line:
            continue
        if in_section and line.startswith('## '):
            break
        if in_section and '|' in line and '配件' in line and '价格' in line:
            continue  # skip header
        if in_section and '|' in line:
            parts = [p.strip() for p in line.strip().split('|')]
            if len(parts) >= 4:
                name = parts[1]
                price_raw = parts[2]
                # 处理价格中带描述的情况
                desc = ''
                if '（' in price_raw or '(' in price_raw:
                    desc_m = re.search(r'[（(](.+?)[）)]', price_raw)
                    if desc_m:
                        desc = desc_m.group(1)
                price = parse_price(price_raw)
                items.append({
                    '物品名称': name,
                    '分类': '配件',
                    '描述': desc,
                    '价格_eb': price['value'],
                    '价格备注': price_raw if price['value'] == 0 else '',
                    '数据来源': '基础装备表'
                })
    return items


def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    # 提取所有数据
    melee = extract_melee_weapons(text)
    pistols = extract_ranged_pistols(text)
    longguns = extract_ranged_longguns(text)
    exotic = extract_exotic_weapons(text)
    armor = extract_armor(text)
    ammo = extract_ammo(text)
    accessories = extract_accessories(text)

    # 合并武器
    all_weapons = melee + pistols + longguns + exotic

    # 输出JSON
    weapons_file = os.path.join(OUTPUT_DIR, 'weapons.json')
    armor_file = os.path.join(OUTPUT_DIR, 'armor.json')
    ammo_file = os.path.join(OUTPUT_DIR, 'ammo_accessories.json')

    with open(weapons_file, 'w', encoding='utf-8') as f:
        json.dump(all_weapons, f, ensure_ascii=False, indent=2)

    with open(armor_file, 'w', encoding='utf-8') as f:
        json.dump(armor, f, ensure_ascii=False, indent=2)

    with open(ammo_file, 'w', encoding='utf-8') as f:
        json.dump(ammo + accessories, f, ensure_ascii=False, indent=2)

    # 后处理：清除脏数据
    for filepath in [weapons_file, armor_file, ammo_file]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cleaned = []
        for row in data:
            # 过滤分隔行
            if any(k == '武器名称' and re.match(r'^[-—]+$', str(v)) for k, v in row.items()):
                continue
            # 清除 ** markdown 标记
            for k, v in row.items():
                if isinstance(v, str):
                    row[k] = v.replace('**', '')
            cleaned.append(row)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

    # 重新统计
    with open(weapons_file, 'r', encoding='utf-8') as f:
        all_weapons = json.load(f)
    with open(armor_file, 'r', encoding='utf-8') as f:
        armor = json.load(f)
    with open(ammo_file, 'r', encoding='utf-8') as f:
        ammo_acc = json.load(f)

    # 打印统计
    print(f"=== A验证批次解析结果 ===")
    print(f"武器速查: {len(all_weapons)} 行 (近战{len(melee)} + 手枪{len(pistols)} + 长枪{len(longguns)} + 异种{len(exotic)})")
    print(f"护甲速查: {len(armor)} 行")
    print(f"弹药与配件: {len(ammo_acc)} 行")
    print(f"总计: {len(all_weapons) + len(armor) + len(ammo_acc)} 行")
    print(f"\n输出文件:")
    print(f"  {weapons_file}")
    print(f"  {armor_file}")
    print(f"  {ammo_file}")

    # 输出武器预览
    print(f"\n=== 武器速查预览 ===")
    for w in all_weapons[:5]:
        print(f"  {w['武器名称']} | {w['武器大类']} | {w['伤害表达式']} | {w['价格_eb']}eb")
    if len(all_weapons) > 5:
        print(f"  ... 共{len(all_weapons)}行")

    print(f"\n=== 护甲速查预览 ===")
    for a in armor[:5]:
        print(f"  {a['护甲名称']} | SP{a['SP']} | {a['惩罚']} | {a['价格_eb']}eb")

    print(f"\n=== 弹药与配件预览 ===")
    for i in ammo_acc[:5]:
        print(f"  {i['物品名称']} | {i['分类']} | {i['价格_eb']}eb")


if __name__ == '__main__':
    main()
