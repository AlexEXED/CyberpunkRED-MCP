#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量提取PDF为可读Markdown文本（含校验保障）
用法: python extract_full.py -i input.pdf -o output.md
"""
import pdfplumber
import sys
import os
import argparse
from datetime import datetime

def extract_pdf(pdf_path, output_path):
    blank_pages = []
    page_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"PDF总页数: {total}")
        print(f"开始提取时间: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(pdf_path)} — 全量提取\n\n")
            f.write(f"> 源文件: {os.path.basename(pdf_path)}\n")
            f.write(f"> 页数: {total}\n")
            f.write(f"> 提取日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"> 提取工具: pdfplumber\n")
            f.write("---\n\n")
            
            for i in range(total):
                page = pdf.pages[i]
                text = page.extract_text()
                
                if text and text.strip():
                    clean = ' '.join(text.split())
                    f.write(f"\n--- 第{i+1}页 ---\n{clean}\n\n")
                    page_count += 1
                else:
                    f.write(f"\n--- 第{i+1}页 --- [空白页/无文本层]\n\n")
                    blank_pages.append(i + 1)
                    page_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"  已处理 {i+1}/{total} 页...")
    
    print("-" * 40)
    print(f"提取完成时间: {datetime.now().strftime('%H:%M:%S')}")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        marker_count = content.count("--- 第")
    
    page_ok = marker_count == total
    if page_ok:
        print(f"✅ 页数校验: 标记数 {marker_count} = 总页 {total}")
    else:
        print(f"❌ 页数校验失败: 标记数 {marker_count} ≠ 总页 {total}")
    
    if blank_pages:
        print(f"⚠️ 空白页 {len(blank_pages)} 个: {blank_pages}")
    else:
        print(f"✅ 空白页: 0 个")
    
    file_size = os.path.getsize(output_path)
    if file_size > 0:
        print(f"✅ 文件大小: {file_size/1024:.1f} KB")
    else:
        print(f"❌ 文件为空！")
        sys.exit(1)
    
    log_path = output_path.replace('.md', '_audit.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"PDF提取审计日志\n{'='*50}\n")
        log.write(f"源文件: {pdf_path}\n")
        log.write(f"输出文件: {output_path}\n")
        log.write(f"总页数: {total}\n")
        log.write(f"成功提取: {total - len(blank_pages)} 页\n")
        log.write(f"空白页: {len(blank_pages)} 个\n")
        if blank_pages:
            log.write(f"空白页列表: {blank_pages}\n")
        log.write(f"页数校验: {'通过' if page_ok else '失败'}\n")
        log.write(f"文件大小: {file_size/1024:.1f} KB\n")
        log.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"📋 审计日志: {os.path.basename(log_path)}")
    print(f"✅ 提取完成")
    return page_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='全量提取PDF为Markdown（含校验）')
    parser.add_argument('-i', '--input', required=True, help='输入PDF路径')
    parser.add_argument('-o', '--output', required=True, help='输出MD路径')
    args = parser.parse_args()
    ok = extract_pdf(args.input, args.output)
    sys.exit(0 if ok else 1)
