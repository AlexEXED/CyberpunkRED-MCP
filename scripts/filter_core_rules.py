#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选核心规则书全量提取，去除小说/故事章节，仅保留规则类内容。
含完整性校验：检查保留和跳过的页数总和是否等于源文件总页数。

保留的章节（基于PDF目录结构）：
  - 第23-30页: 赛博朋克简介/RPG入门
  - 第31-117页: 角色创建（职业、属性、技能、装备、赛博组件）
  - 第120-228页: 核心机制（判定、战斗、网行、创伤）
  - 第229-319页: 背景设定（夜之城、企业战争）
  - 第321-406页: 经济/夜市/生活/GM指南/遭遇表
  - 第435-462页: FAQ、DLC（代理）

跳过的章节：
  - 第1-8页: 封面/群号/翻译名单/目录
  - 第9-22页: 小说 "永不消逝"（强尼银手故事）
  - 第407-434页: 啸报、黑狗（短篇小说合集）
"""

import re
import os

INPUT = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\rules\核心规则书_全量提取.md"
OUTPUT = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\rules\核心规则书_规则部分.md"


def is_rules_page(page_num):
    """判断页面是否为规则类内容"""
    if 1 <= page_num <= 8:    # 封面/前言/目录
        return False
    if 9 <= page_num <= 22:   # 小说「永不消逝」
        return False
    if 407 <= page_num <= 434: # 啸报/黑狗（小说）
        return False
    return True


def main():
    with open(INPUT, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ===== 阶段1：解析全量文件中的页数 =====
    total_source_pages = content.count("--- 第")
    print(f"源文件页数: {total_source_pages}")
    
    pages = re.split(r'(--- 第(\d+)页 ---\n)', content)
    
    # 提取所有页面段
    segments = []
    i = 0
    while i < len(pages):
        if pages[i].startswith('--- 第'):
            marker = pages[i]
            page_num = int(pages[i + 1])
            text_start = i + 2
            if text_start < len(pages):
                remaining = []
                j = text_start
                while j < len(pages) and not pages[j].startswith('--- 第'):
                    remaining.append(pages[j])
                    j += 1
                text = ''.join(remaining)
            else:
                text = ""
            segments.append({
                'page_num': page_num,
                'marker': marker,
                'text': text
            })
        i += 1
    
    parsed_pages = len(segments)
    print(f"解析页数: {parsed_pages}")
    
    # ===== 校验1：源文件完整性 =====
    if parsed_pages != total_source_pages:
        print(f"❌ 解析页数({parsed_pages}) ≠ 标记页数({total_source_pages})，文件可能损坏")
    
    # ===== 阶段2：筛选 =====
    kept = 0
    skipped = 0
    kept_ranges = []
    skipped_ranges = []
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write("# 赛博朋克RED 核心规则书 — 规则部分（筛选版）\n\n")
        f.write("> 筛选说明：已去除小说故事章节（第1-22页：前言/目录/永不消逝；第407-434页：啸报/黑狗）\n")
        f.write("> 保留所有规则类内容（角色创建、战斗、网行、装备、背景设定、GM指南等）\n\n")
        f.write("---\n\n")
        
        for seg in segments:
            pn = seg['page_num']
            if is_rules_page(pn):
                f.write(seg['marker'])
                f.write(seg['text'])
                kept += 1
            else:
                skipped += 1
                if not skipped_ranges or skipped_ranges[-1][1] + 1 != pn:
                    skipped_ranges.append([pn, pn])
                else:
                    skipped_ranges[-1][1] = pn
    
    # ===== 阶段3：校验 =====
    total_out = kept + skipped
    total_match = total_out == total_source_pages
    
    print(f"\n{'='*50}")
    print(f"📊 筛选结果")
    print(f"{'='*50}")
    print(f"   保留: {kept} 页（规则内容）")
    print(f"   跳过: {skipped} 页（小说/前言/目录）")
    print(f"   合计: {total_out} 页")
    print(f"{'✅' if total_match else '❌'} 页数校验: {total_out} {'=' if total_match else '≠'} {total_source_pages}")
    
    # 校验2：检查规则关键词在保留文件中是否存在
    print(f"\n📋 规则关键词检查:")
    keywords = ["职业", "属性", "技能", "战斗", "护甲", "武器", "赛博", "判定"]
    for kw in keywords:
        count = 0
        with open(OUTPUT, 'r', encoding='utf-8') as f:
            count = f.read().count(kw)
        status = "✅" if count > 0 else "❌"
        print(f"   {status} '{kw}': {count} 次")
    
    # 校验3：边界检查 - 开头不应是小说页
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        # 跳过头几行的元数据
        for _ in range(10):
            line = f.readline()
            if '第23页' in line or '第24页' in line:
                print(f"✅ 边界检查: 规则内容从第23页开始")
                break
            if '第9页' in line or '第10页' in line:
                print(f"❌ 边界错误: 规则内容从小说页开始！")
                break

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"\n📄 输出: {os.path.basename(OUTPUT)} ({size_kb:.1f} KB)")
    print(f"   跳过的页码范围: {skipped_ranges}")
    print(f"✅ 筛选完成")


if __name__ == "__main__":
    main()
