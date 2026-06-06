#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 GM指南.md 的格式：分段、去多余空格、表格化
"""
import re

FILE = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\rules\GM指南.md"

with open(FILE, 'r', encoding='utf-8') as f:
    raw = f.read()

# Step 1: 修复中文之间的多余空格（但保留英文字词间的空格）
# 模式：中文字符之间的空格
raw = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', raw)
# 中文和英文标点之间的空格
raw = re.sub(r'([\u4e00-\u9fff])\s+([，。、；：？！""''「」【】（）])', r'\1\2', raw)
raw = re.sub(r'([，。、；：？！""''「」【】（）])\s+([\u4e00-\u9fff])', r'\1\2', raw)
# 数字和单位之间的空格（如 100 欧元 -> 100欧元）
raw = re.sub(r'(\d)\s+(欧元|欧|eb|发|米|码|级)', r'\1\2', raw)

# Step 2: 修复页面编号和空白标记
raw = re.sub(r'p\d+完\s*', '', raw)
raw = re.sub(r'P\d+完\s*', '', raw)
raw = re.sub(r'^\d+\s*$', '', raw, flags=re.MULTILINE)

# Step 3: 修复分段 - 在句号/问号/感叹号后增加换行（但保留列表内的）
# 先将所有多空行合并为单空行
raw = re.sub(r'\n{3,}', '\n\n', raw)

# Step 4: 修复"▶ 标题 ◀"格式
raw = re.sub(r'▶\s*', '#### ', raw)
raw = re.sub(r'\s*◀', '', raw)

# Step 5: 修复边栏标记
raw = re.sub(r'（边栏.*?）', '', raw)
raw = re.sub(r'侧边栏.*?\n', '', raw)

# Step 6: 尝试修复表格 - 检测看起来像表格的行
# 实际上源文件中表格格式已经不太好识别，不做复杂处理

# Step 7: 确保标题前后有空行
raw = re.sub(r'(?<!\n)(#+ )', r'\n\n\1', raw)
raw = re.sub(r'(#+ .+)\n(?!\n)', r'\1\n', raw)

# Step 8: 删除行首/行尾多余空格
lines = raw.split('\n')
cleaned = []
for line in lines:
    line = line.strip()
    if line:
        cleaned.append(line)
    else:
        # 保留空行作为段落分隔
        if cleaned and cleaned[-1] != '':
            cleaned.append('')

raw = '\n'.join(cleaned)

# 写回
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(raw)

# 统计
lines_count = len(raw.split('\n'))
print(f"✅ GM指南.md 清理完成")
print(f"   总行数: {lines_count}")
print(f"   文件大小: {len(raw)/1024:.1f} KB")
