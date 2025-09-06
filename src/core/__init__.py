"""
核心功能模块

包含PDF解析、内容分析、Typst生成等核心功能。
"""

from .models import (
    TextBlock, Table, Image, Heading, Paragraph, List,
    ParsedDocument, TypstDocument, DocumentMetadata, PageInfo,
    PDFParseError, TypstGenerationError, UnsupportedFormatError
)

# 基础接口和模型总是可用
from .parser_interface import PDFParserInterface, BasePDFParser

# 可选导入，需要外部依赖的模块
try:
    from .pdf_parser import HybridPDFParser
    _HAS_PDF_PARSER = True
except ImportError:
    _HAS_PDF_PARSER = False

try:
    from .content_analyzer import ContentAnalyzer
    _HAS_CONTENT_ANALYZER = True
except ImportError:
    _HAS_CONTENT_ANALYZER = False

try:
    from .typst_generator import TypstGenerator
    _HAS_TYPST_GENERATOR = True
except ImportError:
    _HAS_TYPST_GENERATOR = False

try:
    from .pipeline import PDFToTypstPipeline
    _HAS_PIPELINE = True
except ImportError:
    _HAS_PIPELINE = False

# 基础导出列表
__all__ = [
    # 数据模型
    'TextBlock', 'Table', 'Image', 'Heading', 'Paragraph', 'List',
    'ParsedDocument', 'TypstDocument', 'DocumentMetadata', 'PageInfo',
    
    # 异常类
    'PDFParseError', 'TypstGenerationError', 'UnsupportedFormatError',
    
    # 基础解析器（总是可用）
    'PDFParserInterface', 'BasePDFParser',
]

# 根据可用性添加到导出列表
if _HAS_PDF_PARSER:
    __all__.append('HybridPDFParser')

if _HAS_CONTENT_ANALYZER:
    __all__.append('ContentAnalyzer')

if _HAS_TYPST_GENERATOR:
    __all__.append('TypstGenerator')

if _HAS_PIPELINE:
    __all__.append('PDFToTypstPipeline')