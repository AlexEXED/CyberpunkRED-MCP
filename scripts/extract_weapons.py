#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从赛博朋克RED规则书中提取武器信息
"""

import PyPDF2
import sys

pdf_path = "赛博朋克红汉化规则核心书&FAQver2.50.pdf"

try:
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        print(f"PDF总页数: {total_pages}")
        
        # 提取第96-105页（武器和装备表格）
        print("\n" + "="*60)
        print("第96-105页内容（武器表格部分）")
        print("="*60 + "\n")
        
        for page_num in range(95, min(105, total_pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            print(f"\n=== 第 {page_num + 1} 页 ===")
            print(text[:1500] if text else "[无法提取文本]")
            
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)
