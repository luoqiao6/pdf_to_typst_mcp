"""
混合PDF解析器实现

结合pdfplumber和PyMuPDF的优势，实现高质量的PDF内容提取。
- pdfplumber: 文本提取和表格识别
- PyMuPDF: 样式信息和图像提取
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import logging

try:
    import pdfplumber
    import fitz  # PyMuPDF
    from PIL import Image as PILImage
except ImportError as e:
    raise ImportError(f"缺少必要的依赖包: {e}")

from .parser_interface import BasePDFParser
from .models import (
    TextBlock, Table, Image, DocumentMetadata, PageInfo,
    BoundingBox, FontInfo, TextStyle, TableCell, ElementType,
    PDFParseError
)

# 设置日志
logger = logging.getLogger(__name__)


class HybridPDFParser(BasePDFParser):
    """混合PDF解析器"""
    
    def _setup(self) -> None:
        """设置解析器"""
        super()._setup()
        
        # 添加特定配置
        hybrid_config = {
            'use_pdfplumber_for_text': True,
            'use_pymupdf_for_images': True,
            'use_pdfplumber_for_tables': True,
            'use_pymupdf_for_styles': True,
            'text_extraction_method': 'layout',  # layout, simple
            'table_settings': {
                'vertical_strategy': 'lines',
                'horizontal_strategy': 'lines',
                'snap_tolerance': 3,
                'join_tolerance': 3,
            }
        }
        
        for key, value in hybrid_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def extract_metadata(self, pdf_path: Path) -> DocumentMetadata:
        """
        提取文档元数据
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            DocumentMetadata: 文档元数据
        """
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                
                return DocumentMetadata(
                    title=metadata.get('title'),
                    author=metadata.get('author'),
                    subject=metadata.get('subject'),
                    creator=metadata.get('creator'),
                    producer=metadata.get('producer'),
                    creation_date=metadata.get('creationDate'),
                    modification_date=metadata.get('modDate'),
                    pages=doc.page_count
                )
                
        except Exception as e:
            logger.warning(f"提取元数据失败: {e}")
            return DocumentMetadata(pages=0)
    
    def get_page_info(self, pdf_path: Path) -> List[PageInfo]:
        """
        获取页面信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[PageInfo]: 页面信息列表
        """
        pages = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    rect = page.rect
                    pages.append(PageInfo(
                        number=page_num + 1,
                        width=rect.width,
                        height=rect.height,
                        rotation=page.rotation
                    ))
                    
        except Exception as e:
            logger.error(f"获取页面信息失败: {e}")
            raise PDFParseError(f"无法获取页面信息: {e}")
        
        return pages
    
    def extract_text(self, pdf_path: Path) -> List[TextBlock]:
        """
        提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[TextBlock]: 文本块列表
        """
        text_blocks = []
        
        try:
            # 使用pdfplumber提取文本布局
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 提取字符级别的信息
                    chars = page.chars
                    
                    # 按行分组字符
                    lines = self._group_chars_into_lines(chars)
                    
                    for line in lines:
                        if not line:
                            continue
                        
                        # 合并行中的字符
                        text = ''.join(char['text'] for char in line)
                        if not text.strip():
                            continue
                        
                        # 计算边界框
                        bbox = self._calculate_bbox_from_chars(line)
                        
                        # 获取字体信息
                        font_info = self._extract_font_info_from_chars(line)
                        
                        # 创建文本块
                        text_block = TextBlock(
                            text=text,
                            page=page_num + 1,
                            bbox=bbox,
                            font=font_info,
                            element_type=ElementType.TEXT
                        )
                        
                        text_blocks.append(text_block)
                        
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            # 如果pdfplumber失败，尝试使用PyMuPDF
            text_blocks = self._extract_text_with_pymupdf(pdf_path)
        
        return text_blocks
    
    def _extract_text_with_pymupdf(self, pdf_path: Path) -> List[TextBlock]:
        """使用PyMuPDF提取文本作为备选方案"""
        text_blocks = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # 获取文本字典
                    text_dict = page.get_text("dict")
                    
                    for block in text_dict["blocks"]:
                        if "lines" not in block:
                            continue
                        
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if not text:
                                    continue
                                
                                # 创建边界框
                                bbox = BoundingBox(
                                    x0=span["bbox"][0],
                                    y0=span["bbox"][1],
                                    x1=span["bbox"][2],
                                    y1=span["bbox"][3]
                                )
                                
                                # 创建字体信息
                                font_info = FontInfo(
                                    name=span["font"],
                                    size=span["size"],
                                    color=(0, 0, 0),  # 默认黑色
                                    styles=self._get_text_styles_from_flags(span["flags"])
                                )
                                
                                text_block = TextBlock(
                                    text=text,
                                    page=page_num + 1,
                                    bbox=bbox,
                                    font=font_info,
                                    element_type=ElementType.TEXT
                                )
                                
                                text_blocks.append(text_block)
                                
        except Exception as e:
            logger.error(f"PyMuPDF文本提取失败: {e}")
            raise PDFParseError(f"文本提取失败: {e}")
        
        return text_blocks
    
    def extract_tables(self, pdf_path: Path) -> List[Table]:
        """
        提取表格
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[Table]: 表格列表
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 使用pdfplumber的表格检测
                    page_tables = page.find_tables(
                        table_settings=self.config['table_settings']
                    )
                    
                    for table_data in page_tables:
                        # 提取表格数据
                        table_array = table_data.extract()
                        if not table_array:
                            continue
                        
                        # 过滤空表格
                        rows = len(table_array)
                        cols = len(table_array[0]) if table_array else 0
                        
                        if (rows < self.config['min_table_rows'] or 
                            cols < self.config['min_table_cols']):
                            continue
                        
                        # 创建表格单元格
                        cells = []
                        for row_idx, row in enumerate(table_array):
                            for col_idx, cell_text in enumerate(row):
                                if cell_text is None:
                                    cell_text = ""
                                
                                cell = TableCell(
                                    text=str(cell_text),
                                    row=row_idx,
                                    col=col_idx
                                )
                                cells.append(cell)
                        
                        # 创建表格边界框
                        bbox = BoundingBox(
                            x0=table_data.bbox[0],
                            y0=table_data.bbox[1],
                            x1=table_data.bbox[2],
                            y1=table_data.bbox[3]
                        )
                        
                        # 检测是否有表头
                        has_header = self._detect_table_header(table_array)
                        
                        table = Table(
                            cells=cells,
                            page=page_num + 1,
                            bbox=bbox,
                            rows=rows,
                            cols=cols,
                            has_header=has_header
                        )
                        
                        tables.append(table)
                        
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
        
        return tables
    
    def extract_images(self, pdf_path: Path) -> List[Image]:
        """
        提取图像
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[Image]: 图像列表
        """
        images = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        # 获取图像引用
                        xref = img[0]
                        
                        # 提取图像数据
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # 获取图像信息
                        pil_image = PILImage.open(io.BytesIO(image_bytes))
                        width, height = pil_image.size
                        
                        # 过滤小图像
                        if (width < self.config['image_min_width'] or 
                            height < self.config['image_min_height']):
                            continue
                        
                        # 获取图像位置（近似）
                        image_rects = page.get_image_rects(xref)
                        if image_rects:
                            rect = image_rects[0]
                            bbox = BoundingBox(
                                x0=rect.x0,
                                y0=rect.y0,
                                x1=rect.x1,
                                y1=rect.y1
                            )
                        else:
                            # 默认边界框
                            bbox = BoundingBox(x0=0, y0=0, x1=width, y1=height)
                        
                        # 生成文件名
                        filename = f"image_p{page_num + 1}_{img_index + 1}.{image_ext}"
                        
                        image_obj = Image(
                            data=image_bytes,
                            page=page_num + 1,
                            bbox=bbox,
                            format=image_ext,
                            filename=filename,
                            width=width,
                            height=height
                        )
                        
                        images.append(image_obj)
                        
        except Exception as e:
            logger.error(f"提取图像失败: {e}")
        
        return images
    
    def _group_chars_into_lines(self, chars: List[Dict]) -> List[List[Dict]]:
        """将字符按行分组"""
        if not chars:
            return []
        
        # 按y坐标排序
        sorted_chars = sorted(chars, key=lambda c: (c['top'], c['x0']))
        
        lines = []
        current_line = []
        current_y = None
        tolerance = 2  # y坐标容差
        
        for char in sorted_chars:
            char_y = char['top']
            
            if current_y is None or abs(char_y - current_y) <= tolerance:
                current_line.append(char)
                current_y = char_y
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [char]
                current_y = char_y
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _calculate_bbox_from_chars(self, chars: List[Dict]) -> BoundingBox:
        """从字符列表计算边界框"""
        if not chars:
            return BoundingBox(0, 0, 0, 0)
        
        x0 = min(char['x0'] for char in chars)
        y0 = min(char['top'] for char in chars)
        x1 = max(char['x1'] for char in chars)
        y1 = max(char['bottom'] for char in chars)
        
        return BoundingBox(x0, y0, x1, y1)
    
    def _extract_font_info_from_chars(self, chars: List[Dict]) -> FontInfo:
        """从字符列表提取字体信息"""
        if not chars:
            return FontInfo("default", 12, (0, 0, 0), [TextStyle.NORMAL])
        
        # 使用第一个字符的字体信息
        first_char = chars[0]
        
        font_name = first_char.get('fontname', 'default')
        font_size = first_char.get('size', 12)
        
        # 简单的样式检测
        styles = [TextStyle.NORMAL]
        if 'bold' in font_name.lower():
            styles.append(TextStyle.BOLD)
        if 'italic' in font_name.lower():
            styles.append(TextStyle.ITALIC)
        
        return FontInfo(
            name=font_name,
            size=font_size,
            color=(0, 0, 0),  # 默认黑色
            styles=styles
        )
    
    def _get_text_styles_from_flags(self, flags: int) -> List[TextStyle]:
        """从PyMuPDF的flags获取文本样式"""
        styles = [TextStyle.NORMAL]
        
        # PyMuPDF字体标志
        if flags & 2**4:  # 粗体
            styles.append(TextStyle.BOLD)
        if flags & 2**1:  # 斜体
            styles.append(TextStyle.ITALIC)
        
        return styles
    
    def _detect_table_header(self, table_array: List[List]) -> bool:
        """检测表格是否有表头"""
        if not table_array or len(table_array) < 2:
            return False
        
        # 简单启发式：如果第一行的内容看起来像标题
        first_row = table_array[0]
        if not first_row:
            return False
        
        # 检查是否包含常见的表头特征
        header_indicators = ['名称', '标题', 'name', 'title', '类型', 'type', '编号', 'id']
        
        for cell in first_row:
            if cell and any(indicator in str(cell).lower() for indicator in header_indicators):
                return True
        
        return False
