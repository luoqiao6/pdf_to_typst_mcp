"""
核心数据模型

定义PDF解析和Typst生成过程中使用的核心数据结构。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any, Union
from enum import Enum
import json


class ElementType(Enum):
    """元素类型枚举"""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    LIST = "list"
    QUOTE = "quote"
    CODE = "code"
    FORMULA = "formula"
    FOOTNOTE = "footnote"
    REFERENCE = "reference"


class TextStyle(Enum):
    """文本样式枚举"""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"


@dataclass
class BoundingBox:
    """边界框"""
    x0: float  # 左边界
    y0: float  # 下边界
    x1: float  # 右边界
    y1: float  # 上边界
    
    @property
    def width(self) -> float:
        """获取宽度"""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """获取高度"""
        return self.y1 - self.y0
    
    @property
    def center(self) -> Tuple[float, float]:
        """获取中心点坐标"""
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)


@dataclass
class FontInfo:
    """字体信息"""
    name: str
    size: float
    color: Tuple[int, int, int]  # RGB颜色
    styles: List[TextStyle]
    
    def __post_init__(self):
        """后处理，确保样式列表不为空"""
        if not self.styles:
            self.styles = [TextStyle.NORMAL]


@dataclass
class TextBlock:
    """文本块"""
    text: str
    page: int
    bbox: BoundingBox
    font: FontInfo
    element_type: ElementType = ElementType.TEXT
    confidence: float = 1.0  # 识别置信度
    
    def __post_init__(self):
        """后处理，清理文本内容"""
        self.text = self.text.strip()
    
    @property
    def is_bold(self) -> bool:
        """是否为粗体"""
        return TextStyle.BOLD in self.font.styles
    
    @property
    def is_italic(self) -> bool:
        """是否为斜体"""
        return TextStyle.ITALIC in self.font.styles


@dataclass
class TableCell:
    """表格单元格"""
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    font: Optional[FontInfo] = None
    
    def __post_init__(self):
        """后处理，清理单元格文本"""
        self.text = self.text.strip()


@dataclass
class Table:
    """表格"""
    cells: List[TableCell]
    page: int
    bbox: BoundingBox
    rows: int
    cols: int
    has_header: bool = False
    table_type: str = "simple"  # simple, complex, form
    confidence: float = 1.0
    
    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """获取指定位置的单元格"""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None
    
    def to_2d_array(self) -> List[List[str]]:
        """转换为二维数组格式"""
        result = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                result[cell.row][cell.col] = cell.text
        return result


@dataclass
class Image:
    """图像"""
    data: bytes
    page: int
    bbox: BoundingBox
    format: str  # png, jpg, etc.
    filename: str
    width: int
    height: int
    dpi: Optional[Tuple[int, int]] = None
    
    @property
    def size_mb(self) -> float:
        """获取图像大小（MB）"""
        return len(self.data) / (1024 * 1024)


@dataclass
class Heading:
    """标题"""
    text: str
    level: int  # 1-6
    page: int
    bbox: BoundingBox
    font: FontInfo
    numbering: Optional[str] = None  # 如 "1.2.3"
    
    def __post_init__(self):
        """后处理，确保标题级别在有效范围内"""
        self.level = max(1, min(6, self.level))


@dataclass
class Paragraph:
    """段落"""
    text_blocks: List[TextBlock]
    page: int
    bbox: BoundingBox
    alignment: str = "left"  # left, center, right, justify
    indent: float = 0.0
    spacing_before: float = 0.0
    spacing_after: float = 0.0
    
    @property
    def text(self) -> str:
        """获取段落完整文本"""
        return " ".join(block.text for block in self.text_blocks)


@dataclass
class ListItem:
    """列表项"""
    text: str
    level: int
    bullet_type: str  # bullet, number, letter
    page: int
    bbox: BoundingBox


@dataclass
class List:
    """列表"""
    items: List[ListItem]
    page: int
    bbox: BoundingBox
    list_type: str  # ordered, unordered


@dataclass
class PageInfo:
    """页面信息"""
    number: int
    width: float
    height: float
    rotation: int = 0
    
    @property
    def aspect_ratio(self) -> float:
        """获取宽高比"""
        return self.width / self.height if self.height > 0 else 1.0


@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    pages: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            key: value for key, value in self.__dict__.items()
            if value is not None
        }


@dataclass
class ParsedDocument:
    """解析后的文档"""
    metadata: DocumentMetadata
    pages: List[PageInfo]
    text_blocks: List[TextBlock]
    tables: List[Table]
    images: List[Image]
    headings: List[Heading]
    paragraphs: List[Paragraph]
    lists: List[List]
    
    def get_elements_by_page(self, page_num: int) -> Dict[str, List]:
        """获取指定页面的所有元素"""
        return {
            "text_blocks": [tb for tb in self.text_blocks if tb.page == page_num],
            "tables": [t for t in self.tables if t.page == page_num],
            "images": [img for img in self.images if img.page == page_num],
            "headings": [h for h in self.headings if h.page == page_num],
            "paragraphs": [p for p in self.paragraphs if p.page == page_num],
            "lists": [l for l in self.lists if l.page == page_num],
        }
    
    def get_page_count(self) -> int:
        """获取页面总数"""
        return len(self.pages)


@dataclass
class TypstDocument:
    """Typst文档"""
    content: str
    metadata: DocumentMetadata
    images: List[str]  # 图像文件路径列表
    
    def save(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.content)


# 错误和异常类
class PDFParseError(Exception):
    """PDF解析错误"""
    pass


class TypstGenerationError(Exception):
    """Typst生成错误"""
    pass


class UnsupportedFormatError(Exception):
    """不支持的格式错误"""
    pass
