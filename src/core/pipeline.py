"""
PDF转Typst处理流水线

整合PDF解析、内容分析和Typst生成的完整处理流程。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import logging

from .pdf_parser import HybridPDFParser
from .content_analyzer import ContentAnalyzer
from .typst_generator import TypstGenerator
from .models import ParsedDocument, TypstDocument, PDFParseError, TypstGenerationError

logger = logging.getLogger(__name__)


class PDFToTypstPipeline:
    """PDF转Typst处理流水线"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化处理流水线
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self._setup_config()
        
        # 初始化组件
        self.parser = HybridPDFParser(self.config.get('parser', {}))
        self.analyzer = ContentAnalyzer(self.config.get('analyzer', {}))
        self.generator = TypstGenerator(self.config.get('generator', {}))
        
        # 进度回调函数
        self.progress_callback: Optional[Callable[[str, float], None]] = None
    
    def _setup_config(self):
        """设置默认配置"""
        default_config = {
            'output_format': 'typst',
            'save_images': True,
            'create_output_dir': True,
            'overwrite_existing': False,
            'log_level': 'INFO',
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，接收(阶段名称, 进度百分比)参数
        """
        self.progress_callback = callback
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(stage, progress)
        
        logger.info(f"{stage}: {progress:.1f}%")
    
    def convert(self, pdf_path: Path, output_path: Path) -> TypstDocument:
        """
        转换PDF到Typst
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径
            
        Returns:
            TypstDocument: 生成的Typst文档
            
        Raises:
            PDFParseError: PDF解析失败
            TypstGenerationError: Typst生成失败
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始转换: {pdf_path} -> {output_path}")
            
            # 验证输入
            self._validate_input(pdf_path, output_path)
            
            # 第一阶段：PDF解析
            self._update_progress("PDF解析", 0)
            parsed_doc = self.parser.parse_document(pdf_path)
            self._update_progress("PDF解析", 100)
            
            logger.info(f"解析完成: {len(parsed_doc.text_blocks)} 个文本块, "
                       f"{len(parsed_doc.tables)} 个表格, "
                       f"{len(parsed_doc.images)} 个图像")
            
            # 第二阶段：内容分析
            self._update_progress("内容分析", 0)
            analyzed_doc = self.analyzer.analyze_document(parsed_doc)
            self._update_progress("内容分析", 100)
            
            logger.info(f"分析完成: {len(analyzed_doc.headings)} 个标题, "
                       f"{len(analyzed_doc.paragraphs)} 个段落, "
                       f"{len(analyzed_doc.lists)} 个列表")
            
            # 第三阶段：Typst生成
            self._update_progress("Typst生成", 0)
            
            # 创建输出目录
            output_dir = output_path.parent
            if self.config['create_output_dir']:
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建图像输出目录
            image_dir = None
            if self.config['save_images'] and analyzed_doc.images:
                image_dir = output_dir / f"{output_path.stem}_images"
                image_dir.mkdir(exist_ok=True)
            
            # 生成Typst文档
            typst_doc = self.generator.generate_document(analyzed_doc, image_dir)
            self._update_progress("Typst生成", 50)
            
            # 保存文档
            typst_doc.save(output_path)
            self._update_progress("Typst生成", 100)
            
            # 统计信息
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"转换完成! 耗时: {duration:.2f}秒")
            logger.info(f"输出文件: {output_path}")
            if image_dir and analyzed_doc.images:
                logger.info(f"图像目录: {image_dir}")
            
            return typst_doc
            
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            raise
    
    def convert_batch(self, input_dir: Path, output_dir: Path, 
                     pattern: str = "*.pdf") -> Dict[str, Any]:
        """
        批量转换PDF文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            pattern: 文件匹配模式
            
        Returns:
            Dict[str, Any]: 转换结果统计
        """
        pdf_files = list(input_dir.glob(pattern))
        
        if not pdf_files:
            logger.warning(f"未找到匹配的PDF文件: {input_dir}/{pattern}")
            return {"total": 0, "success": 0, "failed": 0, "files": []}
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        
        results = {
            "total": len(pdf_files),
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        for i, pdf_path in enumerate(pdf_files):
            try:
                # 生成输出路径
                output_file = output_dir / f"{pdf_path.stem}.typ"
                
                # 转换文件
                logger.info(f"转换文件 {i+1}/{len(pdf_files)}: {pdf_path.name}")
                
                typst_doc = self.convert(pdf_path, output_file)
                
                results["success"] += 1
                results["files"].append({
                    "input": str(pdf_path),
                    "output": str(output_file),
                    "status": "success",
                    "images": len(typst_doc.images)
                })
                
            except Exception as e:
                logger.error(f"转换失败 {pdf_path.name}: {str(e)}")
                
                results["failed"] += 1
                results["files"].append({
                    "input": str(pdf_path),
                    "output": "",
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"批量转换完成: {results['success']} 成功, {results['failed']} 失败")
        return results
    
    def _validate_input(self, pdf_path: Path, output_path: Path):
        """验证输入参数"""
        # 验证PDF文件
        if not pdf_path.exists():
            raise PDFParseError(f"PDF文件不存在: {pdf_path}")
        
        if not pdf_path.is_file():
            raise PDFParseError(f"不是有效的文件: {pdf_path}")
        
        if pdf_path.suffix.lower() != '.pdf':
            raise PDFParseError(f"不是PDF文件: {pdf_path}")
        
        # 验证输出路径
        if output_path.exists() and not self.config['overwrite_existing']:
            raise TypstGenerationError(f"输出文件已存在: {output_path}")
        
        # 验证输出目录
        if not output_path.parent.exists() and not self.config['create_output_dir']:
            raise TypstGenerationError(f"输出目录不存在: {output_path.parent}")
    
    def get_document_info(self, pdf_path: Path) -> Dict[str, Any]:
        """
        获取PDF文档信息（不进行完整转换）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Dict[str, Any]: 文档信息
        """
        try:
            # 验证文件
            if not self.parser.validate_pdf(pdf_path):
                return {"error": "无效的PDF文件"}
            
            # 提取基本信息
            metadata = self.parser.extract_metadata(pdf_path)
            pages = self.parser.get_page_info(pdf_path)
            
            # 快速统计
            text_blocks = self.parser.extract_text(pdf_path)
            tables = self.parser.extract_tables(pdf_path) if self.config.get('extract_tables', True) else []
            images = self.parser.extract_images(pdf_path) if self.config.get('extract_images', True) else []
            
            return {
                "file_path": str(pdf_path),
                "file_size_mb": pdf_path.stat().st_size / (1024 * 1024),
                "metadata": metadata.to_dict(),
                "pages": len(pages),
                "text_blocks": len(text_blocks),
                "tables": len(tables),
                "images": len(images),
                "page_info": [
                    {
                        "number": page.number,
                        "width": page.width,
                        "height": page.height,
                        "aspect_ratio": page.aspect_ratio
                    }
                    for page in pages[:5]  # 只返回前5页信息
                ]
            }
            
        except Exception as e:
            logger.error(f"获取文档信息失败: {str(e)}")
            return {"error": str(e)}
    
    def preview_conversion(self, pdf_path: Path, max_pages: int = 3) -> Dict[str, Any]:
        """
        预览转换结果（只处理前几页）
        
        Args:
            pdf_path: PDF文件路径
            max_pages: 最大页数
            
        Returns:
            Dict[str, Any]: 预览结果
        """
        try:
            logger.info(f"预览转换: {pdf_path} (前{max_pages}页)")
            
            # 解析文档
            parsed_doc = self.parser.parse_document(pdf_path)
            
            # 只保留前几页的内容
            parsed_doc.text_blocks = [
                block for block in parsed_doc.text_blocks 
                if block.page <= max_pages
            ]
            parsed_doc.tables = [
                table for table in parsed_doc.tables 
                if table.page <= max_pages
            ]
            parsed_doc.images = [
                image for image in parsed_doc.images 
                if image.page <= max_pages
            ]
            
            # 分析内容
            analyzed_doc = self.analyzer.analyze_document(parsed_doc)
            
            # 生成预览Typst内容
            preview_content = self.generator._generate_main_content(analyzed_doc, [])
            
            return {
                "preview_content": preview_content[:2000],  # 限制长度
                "statistics": {
                    "pages_processed": max_pages,
                    "text_blocks": len(analyzed_doc.text_blocks),
                    "headings": len(analyzed_doc.headings),
                    "paragraphs": len(analyzed_doc.paragraphs),
                    "tables": len(analyzed_doc.tables),
                    "images": len(analyzed_doc.images),
                    "lists": len(analyzed_doc.lists)
                }
            }
            
        except Exception as e:
            logger.error(f"预览转换失败: {str(e)}")
            return {"error": str(e)}
