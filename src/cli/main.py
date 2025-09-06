"""
PDF转Typst工具 - 命令行接口

提供命令行工具来转换PDF文件到Typst格式。
"""

import sys
import json
from pathlib import Path
from typing import Optional
import click
import logging
from loguru import logger

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import PDFToTypstPipeline
from core.models import PDFParseError, TypstGenerationError


def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


def progress_callback(stage: str, progress: float):
    """进度回调函数"""
    click.echo(f"\r{stage}: {progress:.1f}%", nl=False)
    if progress >= 100:
        click.echo()  # 换行


@click.group()
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              help='日志级别')
@click.pass_context
def cli(ctx, log_level):
    """PDF转Typst工具 - 专业的学术文档转换工具"""
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    setup_logging(log_level)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              help='配置文件路径（JSON格式）')
@click.option('--no-images', is_flag=True, help='不提取图像')
@click.option('--no-tables', is_flag=True, help='不提取表格')
@click.option('--overwrite', is_flag=True, help='覆盖已存在的输出文件')
@click.pass_context
def convert(ctx, input_file: Path, output_file: Path, 
           config: Optional[Path], no_images: bool, no_tables: bool, overwrite: bool):
    """转换单个PDF文件到Typst格式"""
    
    try:
        # 加载配置
        pipeline_config = {}
        if config:
            with open(config, 'r', encoding='utf-8') as f:
                pipeline_config = json.load(f)
        
        # 更新配置
        pipeline_config.update({
            'save_images': not no_images,
            'overwrite_existing': overwrite,
            'log_level': ctx.obj['log_level']
        })
        
        if no_images:
            pipeline_config.setdefault('parser', {})['extract_images'] = False
        
        if no_tables:
            pipeline_config.setdefault('parser', {})['extract_tables'] = False
        
        # 创建处理流水线
        pipeline = PDFToTypstPipeline(pipeline_config)
        pipeline.set_progress_callback(progress_callback)
        
        click.echo(f"开始转换: {input_file} -> {output_file}")
        
        # 执行转换
        typst_doc = pipeline.convert(input_file, output_file)
        
        click.echo(f"✅ 转换完成!")
        click.echo(f"📄 输出文件: {output_file}")
        
        if typst_doc.images:
            click.echo(f"🖼️  提取图像: {len(typst_doc.images)} 个")
        
        # 显示文档统计
        if typst_doc.metadata.pages:
            click.echo(f"📊 页数: {typst_doc.metadata.pages}")
        
    except (PDFParseError, TypstGenerationError) as e:
        click.echo(f"❌ 转换失败: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("未预期的错误")
        click.echo(f"❌ 未预期的错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--pattern', default='*.pdf', help='文件匹配模式')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              help='配置文件路径（JSON格式）')
@click.option('--no-images', is_flag=True, help='不提取图像')
@click.option('--no-tables', is_flag=True, help='不提取表格')
@click.option('--overwrite', is_flag=True, help='覆盖已存在的输出文件')
@click.pass_context
def batch(ctx, input_dir: Path, output_dir: Path, pattern: str,
          config: Optional[Path], no_images: bool, no_tables: bool, overwrite: bool):
    """批量转换PDF文件到Typst格式"""
    
    try:
        # 加载配置
        pipeline_config = {}
        if config:
            with open(config, 'r', encoding='utf-8') as f:
                pipeline_config = json.load(f)
        
        # 更新配置
        pipeline_config.update({
            'save_images': not no_images,
            'overwrite_existing': overwrite,
            'log_level': ctx.obj['log_level']
        })
        
        if no_images:
            pipeline_config.setdefault('parser', {})['extract_images'] = False
        
        if no_tables:
            pipeline_config.setdefault('parser', {})['extract_tables'] = False
        
        # 创建处理流水线
        pipeline = PDFToTypstPipeline(pipeline_config)
        
        click.echo(f"开始批量转换: {input_dir} -> {output_dir}")
        click.echo(f"匹配模式: {pattern}")
        
        # 执行批量转换
        results = pipeline.convert_batch(input_dir, output_dir, pattern)
        
        # 显示结果
        click.echo(f"\n📊 批量转换完成:")
        click.echo(f"   总计: {results['total']} 个文件")
        click.echo(f"   成功: {results['success']} 个")
        click.echo(f"   失败: {results['failed']} 个")
        
        if results['failed'] > 0:
            click.echo(f"\n❌ 失败的文件:")
            for file_result in results['files']:
                if file_result['status'] == 'failed':
                    click.echo(f"   - {Path(file_result['input']).name}: {file_result['error']}")
        
    except Exception as e:
        logger.exception("批量转换失败")
        click.echo(f"❌ 批量转换失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              help='配置文件路径（JSON格式）')
@click.pass_context
def info(ctx, pdf_file: Path, config: Optional[Path]):
    """显示PDF文档信息"""
    
    try:
        # 加载配置
        pipeline_config = {}
        if config:
            with open(config, 'r', encoding='utf-8') as f:
                pipeline_config = json.load(f)
        
        pipeline_config['log_level'] = ctx.obj['log_level']
        
        # 创建处理流水线
        pipeline = PDFToTypstPipeline(pipeline_config)
        
        click.echo(f"分析PDF文档: {pdf_file}")
        
        # 获取文档信息
        doc_info = pipeline.get_document_info(pdf_file)
        
        if 'error' in doc_info:
            click.echo(f"❌ 分析失败: {doc_info['error']}", err=True)
            return
        
        # 显示信息
        click.echo(f"\n📄 文档信息:")
        click.echo(f"   文件大小: {doc_info['file_size_mb']:.2f} MB")
        click.echo(f"   页数: {doc_info['pages']}")
        click.echo(f"   文本块: {doc_info['text_blocks']}")
        click.echo(f"   表格: {doc_info['tables']}")
        click.echo(f"   图像: {doc_info['images']}")
        
        # 元数据
        metadata = doc_info['metadata']
        if any(metadata.values()):
            click.echo(f"\n📋 元数据:")
            for key, value in metadata.items():
                if value:
                    click.echo(f"   {key}: {value}")
        
        # 页面信息
        if doc_info['page_info']:
            click.echo(f"\n📖 页面信息 (前5页):")
            for page in doc_info['page_info']:
                click.echo(f"   第{page['number']}页: {page['width']:.0f}×{page['height']:.0f} "
                          f"(比例: {page['aspect_ratio']:.2f})")
        
    except Exception as e:
        logger.exception("获取文档信息失败")
        click.echo(f"❌ 获取文档信息失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option('--pages', default=3, help='预览页数')
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              help='配置文件路径（JSON格式）')
@click.pass_context
def preview(ctx, pdf_file: Path, pages: int, config: Optional[Path]):
    """预览PDF转换结果"""
    
    try:
        # 加载配置
        pipeline_config = {}
        if config:
            with open(config, 'r', encoding='utf-8') as f:
                pipeline_config = json.load(f)
        
        pipeline_config['log_level'] = ctx.obj['log_level']
        
        # 创建处理流水线
        pipeline = PDFToTypstPipeline(pipeline_config)
        
        click.echo(f"预览转换: {pdf_file} (前{pages}页)")
        
        # 获取预览
        preview_result = pipeline.preview_conversion(pdf_file, pages)
        
        if 'error' in preview_result:
            click.echo(f"❌ 预览失败: {preview_result['error']}", err=True)
            return
        
        # 显示统计
        stats = preview_result['statistics']
        click.echo(f"\n📊 预览统计:")
        click.echo(f"   处理页数: {stats['pages_processed']}")
        click.echo(f"   文本块: {stats['text_blocks']}")
        click.echo(f"   标题: {stats['headings']}")
        click.echo(f"   段落: {stats['paragraphs']}")
        click.echo(f"   表格: {stats['tables']}")
        click.echo(f"   图像: {stats['images']}")
        click.echo(f"   列表: {stats['lists']}")
        
        # 显示预览内容
        click.echo(f"\n📝 Typst预览内容:")
        click.echo("=" * 50)
        click.echo(preview_result['preview_content'])
        click.echo("=" * 50)
        
    except Exception as e:
        logger.exception("预览转换失败")
        click.echo(f"❌ 预览转换失败: {e}", err=True)
        sys.exit(1)


@cli.command()
def config_template():
    """生成配置文件模板"""
    
    template_config = {
        "parser": {
            "max_file_size_mb": 100,
            "extract_images": True,
            "extract_tables": True,
            "min_table_rows": 2,
            "min_table_cols": 2,
            "image_min_width": 50,
            "image_min_height": 50,
            "text_extraction_method": "layout",
            "table_settings": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3
            }
        },
        "analyzer": {
            "heading_font_size_threshold": 2.0,
            "paragraph_line_spacing_threshold": 5.0,
            "paragraph_indent_threshold": 20.0
        },
        "generator": {
            "paper_size": "a4",
            "margin": "2.5cm",
            "font_family": "Times New Roman",
            "font_size": "11pt",
            "line_spacing": "1.5em",
            "heading_numbering": True,
            "paragraph_spacing": "1em",
            "paragraph_indent": "2em",
            "table_stroke": "0.5pt",
            "image_width": "80%",
            "image_alignment": "center",
            "include_metadata": True,
            "include_toc": True,
            "include_page_numbers": True
        },
        "save_images": True,
        "create_output_dir": True,
        "overwrite_existing": False
    }
    
    config_json = json.dumps(template_config, indent=2, ensure_ascii=False)
    click.echo("# PDF转Typst工具配置文件模板")
    click.echo(config_json)


if __name__ == '__main__':
    cli()
