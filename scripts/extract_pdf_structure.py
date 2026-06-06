#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 pdfplumber 专业提取两个PDF的完整结构
"""
import pdfplumber
import os

PDFS = [
    ("赛博朋克红汉化规则核心书&FAQver2.50.pdf", "核心规则书"),
    ("赛博朋克红-2070玩家手册-v1.6.3.pdf", "2070玩家手册")
]

def extract_pdf_structure(pdf_path, label):
    print(f"\n{'='*70}")
    print(f"📄 {label}: {os.path.basename(pdf_path)}")
    print(f"{'='*70}")
    
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")
        
        # 提取前5页找目录/前言
        print(f"\n【前5页 - 查找目录和前言】")
        for i in range(min(5, total)):
            page = pdf.pages[i]
            text = page.extract_text()
            if text and text.strip():
                # 清理空格（pdfplumber有时会插入额外空格）
                clean = ' '.join(text.split())
                print(f"\n--- 第{i+1}页 ---")
                print(clean[:500])
        
        # 每隔10页提取一次，了解整体结构
        print(f"\n【每隔15页采样一次 - 了解整体结构】")
        for i in range(0, total, 15):
            page = pdf.pages[i]
            text = page.extract_text()
            if text and text.strip():
                clean = ' '.join(text.split())
                print(f"\n--- 第{i+1}页 ---")
                print(clean[:300])

def main():
    work_dir = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED"
    os.chdir(work_dir)
    
    for pdf, label in PDFS:
        path = os.path.join(work_dir, pdf)
        if os.path.exists(path):
            extract_pdf_structure(path, label)
        else:
            print(f"\n[跳过] {label}: 文件不存在")
        print()

if __name__ == "__main__":
    main()
