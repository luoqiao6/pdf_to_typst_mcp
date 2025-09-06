"""
Typst代码生成辅助函数

提供智能的Typst代码生成功能，确保图片路径、表格格式等正确。
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def generate_smart_typst_content(
    session_data: Dict[str, Any], 
    output_path: Path,
    image_dir: Path = None
) -> str:
    """
    智能生成Typst内容
    
    Args:
        session_data: 会话数据，包含页面文本和结构信息
        output_path: 输出文件路径
        image_dir: 图像目录路径
    
    Returns:
        str: 生成的Typst代码
    """
    
    # 基础设置
    typst_content = """#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: "Times New Roman", size: 10pt, lang: "en")
#set par(justify: true, leading: 0.65em)

"""
    
    # 处理每一页的内容
    for page_idx, page_data in enumerate(session_data.get('page_data', [])):
        page_num = page_idx + 1
        
        # 添加页面标题（如果是第一页）
        if page_num == 1:
            # 查找第一个可能的标题
            title_found = False
            for text_block in page_data.get('text_blocks', []):
                if (text_block['font']['size'] > 12 and 
                    any('bold' in style for style in text_block['font']['styles'])):
                    typst_content += f"= {text_block['text'].strip()}\n\n"
                    title_found = True
                    break
            
            if not title_found:
                # 使用文件名作为标题
                typst_content += f"= {output_path.stem.replace('_', ' ').title()}\n\n"
        
        # 处理文本内容
        processed_texts = []
        for text_block in page_data.get('text_blocks', []):
            text = text_block['text'].strip()
            if not text:
                continue
                
            font_size = text_block['font']['size']
            is_bold = any('bold' in style for style in text_block['font']['styles'])
            is_italic = any('italic' in style for style in text_block['font']['styles'])
            
            # 跳过已经作为标题处理的文本
            if page_num == 1 and is_bold and font_size > 12 and text in typst_content:
                continue
            
            # 判断是否为小标题
            if is_bold and font_size >= 8:
                if len(text) < 100:  # 短文本可能是标题
                    typst_content += f"== {text}\n\n"
                    continue
            
            # 判断是否为页眉页脚
            bbox = text_block['bbox']
            if bbox[1] < 50 or bbox[1] > 500:  # 页面顶部或底部
                if len(text) < 200:
                    if bbox[1] < 50:  # 页眉
                        typst_content += f"#align(right)[{text}]\n\n"
                    else:  # 页脚
                        typst_content += f"#align(center)[#text(size: 8pt)[{text}]]\n\n"
                    continue
            
            # 普通段落文本
            processed_texts.append(text)
        
        # 合并连续的段落文本
        if processed_texts:
            # 简单的段落分割逻辑
            current_paragraph = []
            for text in processed_texts:
                if len(text) > 200:  # 长文本，可能是完整段落
                    if current_paragraph:
                        typst_content += ' '.join(current_paragraph) + '\n\n'
                        current_paragraph = []
                    typst_content += text + '\n\n'
                else:
                    current_paragraph.append(text)
            
            if current_paragraph:
                typst_content += ' '.join(current_paragraph) + '\n\n'
        
        # 处理图片
        for img_idx, image in enumerate(page_data.get('images', [])):
            if image_dir:
                # 计算相对路径
                image_rel_path = image_dir.name + '/' + image['filename']
            else:
                image_rel_path = image['filename']
            
            typst_content += f"""#figure(
  image("{image_rel_path}", width: 70%),
  caption: [图片 {page_num}-{img_idx + 1}]
)

"""
        
        # 处理表格
        for table_idx, table in enumerate(page_data.get('tables', [])):
            if table['rows'] > 0 and table['cols'] > 0:
                typst_content += f"#table(\n"
                typst_content += f"  columns: {table['cols']},\n"
                typst_content += f"  stroke: 0.5pt,\n"
                
                # 生成表格内容
                cells = table['cells']
                for row in range(table['rows']):
                    row_cells = [cell['text'] for cell in cells 
                               if cell['row'] == row]
                    if row_cells:
                        cell_content = ', '.join(f'[{cell}]' for cell in row_cells)
                        typst_content += f"  {cell_content},\n"
                
                typst_content += ")\n\n"
    
    return typst_content


def fix_image_paths_in_typst(typst_content: str, image_dir_name: str) -> str:
    """
    修复Typst内容中的图片路径
    
    Args:
        typst_content: 原始Typst内容
        image_dir_name: 图像目录名称
    
    Returns:
        str: 修复后的Typst内容
    """
    import re
    
    # 查找所有image()调用
    pattern = r'image\("([^"]+)"'
    
    def fix_path(match):
        original_path = match.group(1)
        # 如果路径不包含目录，添加图像目录
        if '/' not in original_path:
            return f'image("{image_dir_name}/{original_path}"'
        return match.group(0)
    
    return re.sub(pattern, fix_path, typst_content)


def extract_image_captions_from_text(page_data: Dict[str, Any]) -> Dict[str, str]:
    """
    从页面文本中提取图片说明
    
    Args:
        page_data: 页面数据
    
    Returns:
        Dict[str, str]: 图片文件名到说明的映射
    """
    captions = {}
    
    # 查找可能的图片说明文本
    for text_block in page_data.get('text_blocks', []):
        text = text_block['text'].strip()
        font_size = text_block['font']['size']
        
        # 小字体的长文本可能是图片说明
        if font_size < 8 and len(text) > 50:
            # 简单的启发式：包含常见说明词汇
            caption_keywords = ['photo', 'figure', 'image', 'picture', 'courtesy', 'credit']
            if any(keyword in text.lower() for keyword in caption_keywords):
                # 使用文本的哈希作为键（简化处理）
                key = f"caption_{len(captions) + 1}"
                captions[key] = text
    
    return captions


def generate_enhanced_typst_with_ai_analysis(
    session_data: Dict[str, Any],
    output_path: Path,
    image_dir: Path = None,
    ai_analysis: Dict[str, Any] = None
) -> str:
    """
    基于AI分析结果生成增强的Typst内容
    
    Args:
        session_data: 会话数据
        output_path: 输出路径
        image_dir: 图像目录
        ai_analysis: AI分析结果
    
    Returns:
        str: 增强的Typst内容
    """
    
    # 如果有AI分析结果，使用更智能的生成
    if ai_analysis:
        # 这里可以集成AI分析的布局信息
        # 目前使用基础的智能生成
        pass
    
    # 生成基础内容
    content = generate_smart_typst_content(session_data, output_path, image_dir)
    
    # 如果有图像目录，修复路径
    if image_dir:
        content = fix_image_paths_in_typst(content, image_dir.name)
    
    return content
