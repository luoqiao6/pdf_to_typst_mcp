"""
内容分析器

分析PDF解析结果，识别学术文档结构，包括标题层级、段落、列表等。
"""

from __future__ import annotations

import re
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import logging

from .models import (
    ParsedDocument, TextBlock, Heading, Paragraph, List as DocList,
    ListItem, BoundingBox, ElementType, FontInfo, TextStyle
)

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化内容分析器
        
        Args:
            config: 分析器配置
        """
        self.config = config or {}
        self._setup_config()
        
        # 编译正则表达式
        self._compile_patterns()
    
    def _setup_config(self):
        """设置默认配置"""
        default_config = {
            # 标题识别配置
            'heading_font_size_threshold': 2.0,  # 字体大小差异阈值
            'heading_patterns': [
                r'^第[一二三四五六七八九十\d]+章',  # 中文章节
                r'^第[一二三四五六七八九十\d]+节',  # 中文小节
                r'^\d+\.\d*\s*',  # 数字编号 1.1
                r'^[一二三四五六七八九十]+[、.]',  # 中文数字编号
                r'^[A-Z]+\.\s*',  # 字母编号 A.
                r'^Chapter\s+\d+',  # 英文章节
                r'^Section\s+\d+',  # 英文小节
            ],
            
            # 段落识别配置
            'paragraph_line_spacing_threshold': 5.0,  # 行间距阈值
            'paragraph_indent_threshold': 20.0,  # 缩进阈值
            
            # 列表识别配置
            'list_patterns': [
                r'^\s*[•·▪▫◦‣⁃]\s*',  # 项目符号
                r'^\s*\d+[.、]\s*',  # 数字列表
                r'^\s*[a-zA-Z][.、)]\s*',  # 字母列表
                r'^\s*[一二三四五六七八九十]+[.、)]\s*',  # 中文数字列表
                r'^\s*[(（]\d+[)）]\s*',  # 括号数字
            ],
            
            # 引用识别配置
            'reference_patterns': [
                r'\[\d+\]',  # [1]
                r'\(\d+\)',  # (1)
                r'参考文献',
                r'References',
                r'Bibliography',
            ],
            
            # 公式识别配置
            'formula_patterns': [
                r'\$.*?\$',  # LaTeX公式
                r'\\begin\{.*?\}.*?\\end\{.*?\}',  # LaTeX环境
            ]
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.heading_regexes = [
            re.compile(pattern) for pattern in self.config['heading_patterns']
        ]
        
        self.list_regexes = [
            re.compile(pattern) for pattern in self.config['list_patterns']
        ]
        
        self.reference_regexes = [
            re.compile(pattern) for pattern in self.config['reference_patterns']
        ]
        
        self.formula_regexes = [
            re.compile(pattern, re.DOTALL) for pattern in self.config['formula_patterns']
        ]
    
    def analyze_document(self, parsed_doc: ParsedDocument) -> ParsedDocument:
        """
        分析文档内容
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            ParsedDocument: 分析后的文档
        """
        logger.info("开始分析文档内容")
        
        # 分析标题
        headings = self.analyze_headings(parsed_doc.text_blocks)
        logger.info(f"识别出 {len(headings)} 个标题")
        
        # 分析段落
        paragraphs = self.analyze_paragraphs(parsed_doc.text_blocks, headings)
        logger.info(f"识别出 {len(paragraphs)} 个段落")
        
        # 分析列表
        lists = self.analyze_lists(parsed_doc.text_blocks)
        logger.info(f"识别出 {len(lists)} 个列表")
        
        # 更新文档
        parsed_doc.headings = headings
        parsed_doc.paragraphs = paragraphs
        parsed_doc.lists = lists
        
        return parsed_doc
    
    def analyze_headings(self, text_blocks: List[TextBlock]) -> List[Heading]:
        """
        分析标题
        
        Args:
            text_blocks: 文本块列表
            
        Returns:
            List[Heading]: 标题列表
        """
        headings = []
        
        # 计算平均字体大小
        avg_font_size = self._calculate_average_font_size(text_blocks)
        
        for block in text_blocks:
            # 检查是否为标题
            if self._is_heading(block, avg_font_size):
                level = self._determine_heading_level(block, avg_font_size)
                numbering = self._extract_heading_numbering(block.text)
                
                heading = Heading(
                    text=block.text,
                    level=level,
                    page=block.page,
                    bbox=block.bbox,
                    font=block.font,
                    numbering=numbering
                )
                
                headings.append(heading)
                
                # 更新文本块类型
                block.element_type = ElementType.HEADING
        
        # 后处理：调整标题层级
        headings = self._adjust_heading_levels(headings)
        
        return headings
    
    def analyze_paragraphs(self, text_blocks: List[TextBlock], 
                          headings: List[Heading]) -> List[Paragraph]:
        """
        分析段落
        
        Args:
            text_blocks: 文本块列表
            headings: 标题列表
            
        Returns:
            List[Paragraph]: 段落列表
        """
        paragraphs = []
        
        # 排除标题块
        heading_blocks = {id(h) for h in headings}
        non_heading_blocks = [
            block for block in text_blocks 
            if id(block) not in heading_blocks and block.element_type != ElementType.HEADING
        ]
        
        # 按页面和位置排序
        sorted_blocks = sorted(
            non_heading_blocks, 
            key=lambda b: (b.page, b.bbox.y0, b.bbox.x0)
        )
        
        # 分组为段落
        current_paragraph_blocks = []
        
        for i, block in enumerate(sorted_blocks):
            current_paragraph_blocks.append(block)
            
            # 检查是否应该结束当前段落
            should_end_paragraph = False
            
            if i < len(sorted_blocks) - 1:
                next_block = sorted_blocks[i + 1]
                
                # 不同页面
                if block.page != next_block.page:
                    should_end_paragraph = True
                
                # 垂直间距过大
                elif (next_block.bbox.y0 - block.bbox.y1 > 
                      self.config['paragraph_line_spacing_threshold']):
                    should_end_paragraph = True
                
                # 缩进变化
                elif abs(block.bbox.x0 - next_block.bbox.x0) > self.config['paragraph_indent_threshold']:
                    should_end_paragraph = True
            else:
                # 最后一个块
                should_end_paragraph = True
            
            if should_end_paragraph and current_paragraph_blocks:
                # 创建段落
                paragraph = self._create_paragraph(current_paragraph_blocks)
                paragraphs.append(paragraph)
                current_paragraph_blocks = []
        
        return paragraphs
    
    def analyze_lists(self, text_blocks: List[TextBlock]) -> List[DocList]:
        """
        分析列表
        
        Args:
            text_blocks: 文本块列表
            
        Returns:
            List[DocList]: 列表
        """
        lists = []
        current_list_items = []
        
        for block in text_blocks:
            list_match = self._match_list_pattern(block.text)
            
            if list_match:
                # 创建列表项
                item = ListItem(
                    text=block.text,
                    level=self._determine_list_level(block),
                    bullet_type=list_match['type'],
                    page=block.page,
                    bbox=block.bbox
                )
                
                current_list_items.append(item)
                
                # 更新文本块类型
                block.element_type = ElementType.LIST
                
            elif current_list_items:
                # 结束当前列表
                doc_list = self._create_list(current_list_items)
                lists.append(doc_list)
                current_list_items = []
        
        # 处理最后的列表
        if current_list_items:
            doc_list = self._create_list(current_list_items)
            lists.append(doc_list)
        
        return lists
    
    def _calculate_average_font_size(self, text_blocks: List[TextBlock]) -> float:
        """计算平均字体大小"""
        if not text_blocks:
            return 12.0
        
        sizes = [block.font.size for block in text_blocks if block.font.size > 0]
        return sum(sizes) / len(sizes) if sizes else 12.0
    
    def _is_heading(self, block: TextBlock, avg_font_size: float) -> bool:
        """判断是否为标题"""
        # 字体大小检查
        if block.font.size > avg_font_size + self.config['heading_font_size_threshold']:
            return True
        
        # 粗体检查
        if block.is_bold:
            return True
        
        # 模式匹配检查
        for regex in self.heading_regexes:
            if regex.match(block.text.strip()):
                return True
        
        # 短文本且居中
        if len(block.text.strip()) < 50 and self._is_centered(block):
            return True
        
        return False
    
    def _determine_heading_level(self, block: TextBlock, avg_font_size: float) -> int:
        """确定标题级别"""
        # 基于字体大小
        size_diff = block.font.size - avg_font_size
        
        if size_diff > 8:
            return 1
        elif size_diff > 4:
            return 2
        elif size_diff > 2:
            return 3
        else:
            return 4
    
    def _extract_heading_numbering(self, text: str) -> Optional[str]:
        """提取标题编号"""
        # 匹配数字编号
        match = re.match(r'^(\d+(?:\.\d+)*)', text.strip())
        if match:
            return match.group(1)
        
        # 匹配中文编号
        match = re.match(r'^(第[一二三四五六七八九十\d]+[章节])', text.strip())
        if match:
            return match.group(1)
        
        return None
    
    def _adjust_heading_levels(self, headings: List[Heading]) -> List[Heading]:
        """调整标题层级"""
        if not headings:
            return headings
        
        # 统计各级别的字体大小
        level_sizes = defaultdict(list)
        for heading in headings:
            level_sizes[heading.font.size].append(heading)
        
        # 按字体大小排序，重新分配级别
        sorted_sizes = sorted(level_sizes.keys(), reverse=True)
        
        for level, size in enumerate(sorted_sizes, 1):
            for heading in level_sizes[size]:
                heading.level = min(level, 6)  # 最多6级标题
        
        return headings
    
    def _is_centered(self, block: TextBlock) -> bool:
        """判断文本是否居中"""
        # 简单的居中判断：检查左右边距是否相近
        # 这里需要页面宽度信息，暂时使用简单判断
        return block.bbox.x0 > 100  # 简化判断
    
    def _create_paragraph(self, blocks: List[TextBlock]) -> Paragraph:
        """创建段落"""
        if not blocks:
            raise ValueError("段落不能为空")
        
        # 计算段落边界框
        x0 = min(block.bbox.x0 for block in blocks)
        y0 = min(block.bbox.y0 for block in blocks)
        x1 = max(block.bbox.x1 for block in blocks)
        y1 = max(block.bbox.y1 for block in blocks)
        
        bbox = BoundingBox(x0, y0, x1, y1)
        
        # 确定对齐方式
        alignment = self._determine_alignment(blocks)
        
        # 计算缩进
        indent = blocks[0].bbox.x0 if blocks else 0
        
        return Paragraph(
            text_blocks=blocks,
            page=blocks[0].page,
            bbox=bbox,
            alignment=alignment,
            indent=indent
        )
    
    def _determine_alignment(self, blocks: List[TextBlock]) -> str:
        """确定段落对齐方式"""
        if not blocks:
            return "left"
        
        # 简单的对齐判断
        x_positions = [block.bbox.x0 for block in blocks]
        
        if all(abs(x - x_positions[0]) < 5 for x in x_positions):
            return "left"
        else:
            return "justify"
    
    def _match_list_pattern(self, text: str) -> Optional[Dict]:
        """匹配列表模式"""
        for regex in self.list_regexes:
            match = regex.match(text.strip())
            if match:
                # 确定列表类型
                matched_text = match.group(0)
                
                if '•' in matched_text or '·' in matched_text:
                    list_type = "bullet"
                elif re.search(r'\d+', matched_text):
                    list_type = "number"
                elif re.search(r'[a-zA-Z]', matched_text):
                    list_type = "letter"
                else:
                    list_type = "bullet"
                
                return {
                    'type': list_type,
                    'marker': matched_text.strip()
                }
        
        return None
    
    def _determine_list_level(self, block: TextBlock) -> int:
        """确定列表项级别"""
        # 基于缩进确定级别
        indent = block.bbox.x0
        
        if indent < 50:
            return 1
        elif indent < 100:
            return 2
        elif indent < 150:
            return 3
        else:
            return 4
    
    def _create_list(self, items: List[ListItem]) -> DocList:
        """创建列表"""
        if not items:
            raise ValueError("列表不能为空")
        
        # 计算列表边界框
        x0 = min(item.bbox.x0 for item in items)
        y0 = min(item.bbox.y0 for item in items)
        x1 = max(item.bbox.x1 for item in items)
        y1 = max(item.bbox.y1 for item in items)
        
        bbox = BoundingBox(x0, y0, x1, y1)
        
        # 确定列表类型
        first_item = items[0]
        list_type = "ordered" if first_item.bullet_type == "number" else "unordered"
        
        return DocList(
            items=items,
            page=first_item.page,
            bbox=bbox,
            list_type=list_type
        )
