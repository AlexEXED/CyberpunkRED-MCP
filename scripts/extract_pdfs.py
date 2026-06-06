#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取赛博朋克RED工作区中所有PDF的目录结构和主要内容
"""
import PyPDF2
import sys
import os

PDFS = [
    "赛博朋克红汉化规则核心书&FAQver2.50.pdf",
    "赛博朋克红-2070玩家手册-v1.6.3.pdf"
]

def extract_pdf_info(pdf_path, max_pages=20):
    """提取PDF的基本信息和指定页数内容"""
    if not os.path.exists(pdf_path):
        print(f"[跳过] 文件不存在: {pdf_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"📄 文件: {pdf_path}")
    print(f"{'='*70}")
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total = len(reader.pages)
            print(f"总页数: {total}")
            
            # 检查是否有目录/书签
            try:
                outlines = reader.outline
                if outlines:
                    print(f"\n【目录结构】:")
                    for item in outlines:
                        if isinstance(item, list):
                            for sub in item:
                                if hasattr(sub, 'title'):
                                    print(f"  - {sub.title}")
                        elif hasattr(item, 'title'):
                            print(f"  - {item.title}")
                else:
                    print("\n[无目录结构]")
            except:
                print("\n[无法读取目录]")
            
            # 提取前几页内容（了解整体结构）
            extract_up_to = min(max_pages, total)
            print(f"\n【前{extract_up_to}页内容摘要】:")
            
            for page_num in range(extract_up_to):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    # 只输出前300个字符，避免过长
                    preview = text.strip()[:300]
                    print(f"\n--- 第{page_num+1}页 ---")
                    print(preview)
                    if len(text.strip()) > 300:
                        print("...(截断)")
                else:
                    print(f"\n--- 第{page_num+1}页 --- [无法提取文本]")
                    
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    # 设置工作目录
    work_dir = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED"
    os.chdir(work_dir)
    
    for pdf in PDFS:
        extract_pdf_info(pdf, max_pages=30)
        print()
