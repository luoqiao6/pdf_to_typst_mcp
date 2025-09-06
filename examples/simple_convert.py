#!/usr/bin/env python3
"""
简单的PDF转Typst示例

演示如何使用PDF转Typst工具进行基本的文档转换。
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import PDFToTypstPipeline


def simple_convert_example():
    """简单转换示例"""
    print("🚀 PDF转Typst工具 - 简单转换示例")
    print("=" * 50)
    
    # 检查输入文件
    input_file = Path("sample.pdf")
    if not input_file.exists():
        print("❌ 请在当前目录放置一个名为 'sample.pdf' 的PDF文件")
        return
    
    # 设置输出文件
    output_file = Path("output.typ")
    
    try:
        # 创建处理流水线
        pipeline = PDFToTypstPipeline({
            'save_images': True,
            'create_output_dir': True,
            'overwrite_existing': True
        })
        
        # 设置进度回调
        def show_progress(stage: str, progress: float):
            print(f"📊 {stage}: {progress:.1f}%")
        
        pipeline.set_progress_callback(show_progress)
        
        print(f"📄 输入文件: {input_file}")
        print(f"📝 输出文件: {output_file}")
        print()
        
        # 执行转换
        typst_doc = pipeline.convert(input_file, output_file)
        
        print()
        print("✅ 转换完成!")
        print(f"📄 输出文件: {output_file}")
        
        if typst_doc.images:
            print(f"🖼️  提取图像: {len(typst_doc.images)} 个")
            print(f"📁 图像目录: {output_file.parent / f'{output_file.stem}_images'}")
        
        # 显示文档统计
        if typst_doc.metadata.title:
            print(f"📋 文档标题: {typst_doc.metadata.title}")
        
        if typst_doc.metadata.pages:
            print(f"📊 页数: {typst_doc.metadata.pages}")
        
        print(f"\n💡 提示: 你可以使用Typst编译器编译生成的.typ文件:")
        print(f"   typst compile {output_file}")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return


def batch_convert_example():
    """批量转换示例"""
    print("🚀 PDF转Typst工具 - 批量转换示例")
    print("=" * 50)
    
    # 检查输入目录
    input_dir = Path("input_pdfs")
    if not input_dir.exists():
        print("❌ 请创建 'input_pdfs' 目录并放置PDF文件")
        return
    
    output_dir = Path("output_typst")
    
    try:
        # 创建处理流水线
        pipeline = PDFToTypstPipeline({
            'save_images': True,
            'create_output_dir': True,
            'overwrite_existing': True
        })
        
        print(f"📁 输入目录: {input_dir}")
        print(f"📁 输出目录: {output_dir}")
        print()
        
        # 执行批量转换
        results = pipeline.convert_batch(input_dir, output_dir)
        
        print()
        print("📊 批量转换结果:")
        print(f"   总计: {results['total']} 个文件")
        print(f"   成功: {results['success']} 个")
        print(f"   失败: {results['failed']} 个")
        
        if results['success'] > 0:
            print(f"\n✅ 成功转换的文件:")
            for file_result in results['files']:
                if file_result['status'] == 'success':
                    input_name = Path(file_result['input']).name
                    output_name = Path(file_result['output']).name
                    images_count = file_result.get('images', 0)
                    print(f"   - {input_name} → {output_name} ({images_count} 图像)")
        
        if results['failed'] > 0:
            print(f"\n❌ 失败的文件:")
            for file_result in results['files']:
                if file_result['status'] == 'failed':
                    input_name = Path(file_result['input']).name
                    error = file_result.get('error', '未知错误')
                    print(f"   - {input_name}: {error}")
        
    except Exception as e:
        print(f"❌ 批量转换失败: {e}")
        return


def document_info_example():
    """文档信息示例"""
    print("🚀 PDF转Typst工具 - 文档信息示例")
    print("=" * 50)
    
    input_file = Path("sample.pdf")
    if not input_file.exists():
        print("❌ 请在当前目录放置一个名为 'sample.pdf' 的PDF文件")
        return
    
    try:
        # 创建处理流水线
        pipeline = PDFToTypstPipeline()
        
        print(f"📄 分析文档: {input_file}")
        print()
        
        # 获取文档信息
        doc_info = pipeline.get_document_info(input_file)
        
        if 'error' in doc_info:
            print(f"❌ 分析失败: {doc_info['error']}")
            return
        
        # 显示信息
        print("📋 文档信息:")
        print(f"   文件大小: {doc_info['file_size_mb']:.2f} MB")
        print(f"   页数: {doc_info['pages']}")
        print(f"   文本块: {doc_info['text_blocks']}")
        print(f"   表格: {doc_info['tables']}")
        print(f"   图像: {doc_info['images']}")
        
        # 元数据
        metadata = doc_info['metadata']
        if any(metadata.values()):
            print(f"\n📄 元数据:")
            for key, value in metadata.items():
                if value:
                    print(f"   {key}: {value}")
        
        # 页面信息
        if doc_info['page_info']:
            print(f"\n📖 页面信息:")
            for page in doc_info['page_info']:
                print(f"   第{page['number']}页: {page['width']:.0f}×{page['height']:.0f} "
                      f"(比例: {page['aspect_ratio']:.2f})")
        
    except Exception as e:
        print(f"❌ 获取文档信息失败: {e}")
        return


def main():
    """主函数"""
    print("🎯 PDF转Typst工具示例")
    print("请选择要运行的示例:")
    print("1. 简单转换")
    print("2. 批量转换")
    print("3. 文档信息")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (0-3): ").strip()
            
            if choice == '0':
                print("👋 再见!")
                break
            elif choice == '1':
                simple_convert_example()
            elif choice == '2':
                batch_convert_example()
            elif choice == '3':
                document_info_example()
            else:
                print("❌ 无效选择，请输入 0-3")
                continue
                
            print("\n" + "=" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


if __name__ == '__main__':
    main()
