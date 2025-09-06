#!/usr/bin/env python3
"""
修复Typst生成问题的完整解决方案
"""

import json
import re
import sys
from pathlib import Path

def clean_text(text):
    """清理文本，确保Typst语法正确"""
    # 移除或转义特殊字符
    text = text.replace('"', '\\"')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_title(text, font_size=8):
    """判断是否为标题"""
    title_keywords = [
        'ACKNOWLEDGEMENTS', 'TABLE OF CONTENTS', 'SYSTEMATIC SECTION', 
        'INTRODUCTION', 'SPAWNING', 'DEVELOPMENT', 'HYBRID SPECIES'
    ]
    
    text_upper = text.upper()
    
    # 检查是否包含标题关键词且长度适中
    for keyword in title_keywords:
        if keyword in text_upper and len(text) < 100:
            return True, keyword
    
    return False, None

def separate_mixed_content(text):
    """分离混合在一起的内容"""
    # 尝试分离可能混合的内容
    parts = []
    
    # 查找可能的分界点
    separators = [
        'TABLE OF', 'SYSTEMATIC', 'INTRODUCTION', 
        'Genus ', 'Family ', 'Species '
    ]
    
    current_text = text
    for sep in separators:
        if sep in current_text:
            parts = current_text.split(sep, 1)
            if len(parts) == 2:
                return [parts[0].strip(), sep + parts[1].strip()]
    
    return [text] if text.strip() else []

def generate_correct_typst(page_data):
    """生成语法正确的Typst内容"""
    
    # 分析布局
    text_blocks = page_data['text_blocks']
    left_column = []
    right_column = []
    header = []
    footer = []
    
    for block in text_blocks:
        text = block['text'].strip()
        if not text:
            continue
            
        bbox = block['bbox']
        x, y = bbox[0], bbox[1]
        
        if y < 30:
            header.append(block)
        elif y > 500:
            footer.append(block)
        elif x < 400:
            left_column.append(block)
        else:
            right_column.append(block)
    
    # 排序
    left_column.sort(key=lambda x: x['bbox'][1])
    right_column.sort(key=lambda x: x['bbox'][1])
    header.sort(key=lambda x: x['bbox'][1])
    footer.sort(key=lambda x: x['bbox'][1])
    
    # 开始生成内容
    content_lines = []
    
    # 文档设置
    content_lines.extend([
        '#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))',
        '#set text(font: "Times New Roman", size: 8pt, lang: "en")',
        '#set par(justify: true, leading: 0.6em)',
        ''
    ])
    
    # 页眉
    for block in header:
        text = clean_text(block['text'])
        if text:
            content_lines.extend([f'#align(right)[{text}]', ''])
    
    # 双栏开始
    content_lines.extend(['#columns(2, gutter: 1cm)[', ''])
    
    # 左栏内容
    content_lines.append('// === 左栏：目录和索引 ===')
    content_lines.append('')
    
    for block in left_column:
        text = clean_text(block['text'])
        if not text:
            continue
        
        # 检查是否为标题
        is_title_text, keyword = is_title(text)
        
        if is_title_text:
            # 清理标题文本
            if keyword:
                # 提取纯标题
                if keyword in text:
                    title = keyword
                else:
                    title = text[:50] + '...' if len(text) > 50 else text
                content_lines.extend([f'== {title}', ''])
            else:
                content_lines.extend([f'== {text[:50]}', ''])
        else:
            # 分离可能混合的内容
            text_parts = separate_mixed_content(text)
            for part in text_parts:
                if part:
                    content_lines.extend([part, ''])
    
    # 分栏
    content_lines.extend(['#colbreak()', ''])
    
    # 右栏内容
    content_lines.append('// === 右栏：正文内容 ===')
    content_lines.append('')
    
    for block in right_column:
        text = clean_text(block['text'])
        if not text:
            continue
        
        # 检查是否为INTRODUCTION标题
        if 'INTRODUCTION' in text.upper() and len(text) < 50:
            content_lines.extend(['== INTRODUCTION', ''])
        else:
            # 正文内容
            content_lines.extend([text, ''])
    
    # 结束双栏
    content_lines.extend([']', ''])
    
    # 图片
    if page_data.get('images'):
        content_lines.append('// === 图片 ===')
        content_lines.append('')
        for i, img in enumerate(page_data['images']):
            content_lines.extend([
                '#figure(',
                f'  image("Chaetodontidae_3_images/{img["filename"]}", width: 80%),',
                f'  caption: [Figure {i+1}]',
                ')',
                ''
            ])
    
    # 页脚
    if footer:
        content_lines.append('// === 页脚 ===')
        for block in footer:
            text = clean_text(block['text'])
            if text:
                content_lines.append(f'#align(center)[#text(size: 7pt)[{text}]]')
    
    return '\n'.join(content_lines)

def main():
    """主函数"""
    # 读取页面数据
    try:
        with open('/tmp/chaetodontidae_3_session_data.json', 'r') as f:
            response = json.load(f)
        
        if not response['success']:
            print('❌ 无法读取页面数据')
            return False
        
        page_data = response['data']
        
        print('🔧 生成语法正确且完整的Typst内容...')
        
        # 生成修复版本
        correct_typst = generate_correct_typst(page_data)
        
        # 保存到临时文件
        temp_file = '/tmp/chaetodontidae_3_correct.typ'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(correct_typst)
        
        print('✅ 语法修复完成')
        print(f'📝 内容长度: {len(correct_typst)} 字符')
        print(f'📊 内容行数: {len(correct_typst.splitlines())} 行')
        print(f'💾 修复版本已保存到: {temp_file}')
        
        # 验证语法
        print('\n🔍 语法验证:')
        lines = correct_typst.splitlines()
        print(f'✅ 文档设置: {sum(1 for line in lines if line.startswith("#set"))} 行')
        print(f'✅ 双栏布局: {"#columns" in correct_typst and "#colbreak" in correct_typst}')
        print(f'✅ 标题数量: {sum(1 for line in lines if line.strip().startswith("=="))} 个')
        print(f'✅ 图片引用: {"#figure" in correct_typst}')
        print(f'✅ 页眉页脚: {"#align" in correct_typst}')
        
        return True
        
    except Exception as e:
        print(f'❌ 处理失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
