"""
PDF解析器接口

定义PDF解析器的标准接口，支持不同的解析引擎实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import (
    ParsedDocument, TextBlock, Table, Image, 
    DocumentMetadata, PageInfo, PDFParseError
)


class PDFParserInterface(ABC):
    """PDF解析器接口"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化解析器
        
        Args:
            config: 解析器配置参数
        """
        self.config = config or {}
        self._setup()
    
    @abstractmethod
    def _setup(self) -> None:
        """设置解析器"""
        pass
    
    @abstractmethod
    def parse_document(self, pdf_path: Path) -> ParsedDocument:
        """
        解析PDF文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            ParsedDocument: 解析后的文档对象
            
        Raises:
            PDFParseError: 解析失败时抛出异常
        """
        pass
    
    @abstractmethod
    def extract_text(self, pdf_path: Path) -> List[TextBlock]:
        """
        提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[TextBlock]: 文本块列表
        """
        pass
    
    @abstractmethod
    def extract_tables(self, pdf_path: Path) -> List[Table]:
        """
        提取表格
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[Table]: 表格列表
        """
        pass
    
    @abstractmethod
    def extract_images(self, pdf_path: Path) -> List[Image]:
        """
        提取图像
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[Image]: 图像列表
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, pdf_path: Path) -> DocumentMetadata:
        """
        提取文档元数据
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            DocumentMetadata: 文档元数据
        """
        pass
    
    @abstractmethod
    def get_page_info(self, pdf_path: Path) -> List[PageInfo]:
        """
        获取页面信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            List[PageInfo]: 页面信息列表
        """
        pass
    
    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        验证PDF文件是否有效
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            bool: 文件是否有效
        """
        try:
            if not pdf_path.exists():
                return False
            
            if pdf_path.suffix.lower() != '.pdf':
                return False
            
            # 检查文件大小
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            max_size_mb = self.config.get('max_file_size_mb', 100)
            
            if file_size_mb > max_size_mb:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        return ['.pdf']


class BasePDFParser(PDFParserInterface):
    """基础PDF解析器实现"""
    
    def _setup(self) -> None:
        """设置解析器"""
        # 设置默认配置
        default_config = {
            'max_file_size_mb': 100,
            'extract_images': True,
            'extract_tables': True,
            'min_table_rows': 2,
            'min_table_cols': 2,
            'image_min_width': 50,
            'image_min_height': 50,
        }
        
        # 合并用户配置
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def parse_document(self, pdf_path: Path) -> ParsedDocument:
        """
        解析PDF文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            ParsedDocument: 解析后的文档对象
        """
        if not self.validate_pdf(pdf_path):
            raise PDFParseError(f"无效的PDF文件: {pdf_path}")
        
        try:
            # 提取各种内容
            metadata = self.extract_metadata(pdf_path)
            pages = self.get_page_info(pdf_path)
            text_blocks = self.extract_text(pdf_path)
            tables = self.extract_tables(pdf_path) if self.config.get('extract_tables') else []
            images = self.extract_images(pdf_path) if self.config.get('extract_images') else []
            
            # 创建解析后的文档对象
            return ParsedDocument(
                metadata=metadata,
                pages=pages,
                text_blocks=text_blocks,
                tables=tables,
                images=images,
                headings=[],  # 将在后续步骤中分析
                paragraphs=[],  # 将在后续步骤中分析
                lists=[]  # 将在后续步骤中分析
            )
            
        except Exception as e:
            raise PDFParseError(f"解析PDF文档失败: {str(e)}") from e
