#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量提取2070玩家手册为可读Markdown文本（含校验保障）
用法: python extract_2070_full.py

输出路径: rules/2070玩家手册_参考摘要.md
"""
import pdfplumber
import os
import sys
from datetime import datetime

PDF = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\赛博朋克红-2070玩家手册-v1.6.3.pdf"
OUT = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\rules\2070玩家手册_参考摘要.md"

blank_pages = []
page_count = 0

with pdfplumber.open(PDF) as pdf:
    total = len(pdf.pages)
    print(f"PDF总页数: {total}")
    print(f"开始提取时间: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 40)
    
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write("# 赛博朋克红-2070玩家手册 参考摘要\n\n")
        f.write("> ⚠️ 此手册为个人房规扩展，非官方规则。\n")
        f.write("> 本文件为全量文本提取，用于快速查阅补充内容。\n\n")
        f.write(f"> 源文件: {os.path.basename(PDF)}\n")
        f.write(f"> 页数: {total}\n")
        f.write(f"> 提取日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("---\n\n")
        
        for i in range(total):
            page = pdf.pages[i]
            text = page.extract_text()
            
            if text and text.strip():
                clean = ' '.join(text.split())
                f.write(f"\n--- 第{i+1}页 ---\n")
                f.write(clean + "\n\n")
                page_count += 1
            else:
                f.write(f"\n--- 第{i+1}页 --- [空白页/无文本层]\n\n")
                blank_pages.append(i + 1)
                page_count += 1
            
            if (i + 1) % 25 == 0:
                print(f"  已处理 {i+1}/{total} 页...")

# ===== 校验 =====
print("-" * 40)
print(f"提取完成时间: {datetime.now().strftime('%H:%M:%S')}")

with open(OUT, 'r', encoding='utf-8') as f:
    content = f.read()
    marker_count = content.count("--- 第")

page_ok = marker_count == total
print(f"{'✅' if page_ok else '❌'} 页数校验: 标记数 {marker_count} {'=' if page_ok else '≠'} 总页 {total}")
print(f"{'⚠️' if blank_pages else '✅'} 空白页: {len(blank_pages)} 个{' -> ' + str(blank_pages) if blank_pages else ''}")
print(f"✅ 文件大小: {os.path.getsize(OUT)/1024:.1f} KB")

# 审计日志
log_path = OUT.replace('.md', '_audit.log')
with open(log_path, 'w', encoding='utf-8') as log:
    log.write(f"PDF提取审计日志\n{'='*50}\n")
    log.write(f"源文件: {PDF}\n")
    log.write(f"输出文件: {OUT}\n")
    log.write(f"页数: {total}\n")
    log.write(f"空白页: {len(blank_pages)} 个\n")
    if blank_pages:
        log.write(f"空白页列表: {blank_pages}\n")
    log.write(f"页数校验: {'通过' if page_ok else '失败'}\n")
    log.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print(f"📋 审计日志: {os.path.basename(log_path)}")
print(f"✅ 完成")
