"""
PDF转Typst MCP服务器

智能PDF转换服务，利用Agent的AI大模型进行页面布局识别和Typst代码生成。
通过MCP协议提供标准化的服务接口。
"""

import asyncio
import base64
import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest, CallToolResult, Tool, TextContent, ImageContent,
    ListResourcesRequest, ListResourcesResult, Resource,
    ReadResourceRequest, ReadResourceResult, ResourceContents,
    ListPromptsRequest, ListPromptsResult, Prompt,
    GetPromptRequest, GetPromptResult, PromptMessage,
    ListToolsResult
)

# 导入现有的PDF处理功能
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.pdf_parser import HybridPDFParser
from src.core.pipeline import PDFToTypstPipeline
from src.core.models import ParsedDocument, TypstDocument

logger = logging.getLogger(__name__)


class ConversionSession:
    """转换会话数据"""
    
    def __init__(self, session_id: str, pdf_path: Path):
        self.session_id = session_id
        self.pdf_path = pdf_path
        self.metadata = None
        self.total_pages = 0
        self.page_images = []  # 存储页面图像数据
        self.page_data = []    # 存储页面文本和结构数据
        self.typst_pages = {}  # 存储AI生成的每页Typst代码
        self.created_at = asyncio.get_event_loop().time()


class PDFToTypstMCPServer:
    """PDF转Typst MCP服务器"""
    
    def __init__(self):
        self.server = Server("pdf-to-typst")
        self.parser = HybridPDFParser()
        self.pipeline = PDFToTypstPipeline()
        self.sessions: Dict[str, ConversionSession] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "pdf_mcp_server"
        self.temp_dir.mkdir(exist_ok=True)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools():
            """列出可用的工具"""
            return [
                Tool(
                    name="check_multimodal_capability",
                    description="检测当前AI模型是否支持图片识别（多模态能力）- PDF转换需要多模态AI",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="start_pdf_conversion",
                    description="开始PDF转Typst转换流程，提取页面内容并准备供AI分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "PDF文件的完整路径"
                            },
                            "session_id": {
                                "type": "string", 
                                "description": "转换会话ID（可选，如不提供将自动生成）"
                            }
                        },
                        "required": ["pdf_path"]
                    }
                ),
                Tool(
                    name="analyze_pdf_structure",
                    description="快速分析PDF文档结构，获取基本信息和统计数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "PDF文件的完整路径"
                            }
                        },
                        "required": ["pdf_path"]
                    }
                ),
                Tool(
                    name="preview_typst_output",
                    description="预览PDF转换后的Typst代码（前几页）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "PDF文件的完整路径"
                            },
                            "max_pages": {
                                "type": "integer",
                                "description": "预览的最大页数（默认3页）",
                                "default": 3
                            }
                        },
                        "required": ["pdf_path"]
                    }
                ),
                Tool(
                    name="finalize_conversion",
                    description="完成转换，整合AI生成的Typst代码并输出文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "转换会话ID"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出文件路径（可选）"
                            },
                            "typst_content": {
                                "type": "string",
                                "description": "AI生成的完整Typst代码内容"
                            }
                        },
                        "required": ["session_id", "typst_content"]
                    }
                ),
                Tool(
                    name="list_active_sessions",
                    description="列出当前活跃的转换会话",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """处理工具调用"""
            try:
                if name == "check_multimodal_capability":
                    return await self._check_multimodal_capability(arguments)
                elif name == "start_pdf_conversion":
                    return await self._start_conversion(arguments)
                elif name == "analyze_pdf_structure":
                    return await self._analyze_pdf_structure(arguments)
                elif name == "preview_typst_output":
                    return await self._preview_typst_output(arguments)
                elif name == "finalize_conversion":
                    return await self._finalize_conversion(arguments)
                elif name == "list_active_sessions":
                    return await self._list_active_sessions(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            
            except Exception as e:
                logger.error(f"工具调用失败 {name}: {e}")
                raise Exception(f"❌ 操作失败: {str(e)}")
        
        @self.server.list_resources()
        async def list_resources():
            """列出可用的资源（页面图片、文本内容等）"""
            resources = []
            
            for session_id, session in self.sessions.items():
                # 为每个页面添加图片资源
                for page_num in range(1, session.total_pages + 1):
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/image",
                        name=f"会话{session_id[:8]}-第{page_num}页图片",
                        description=f"PDF第{page_num}页的高分辨率图片，用于AI布局识别",
                        mimeType="image/png"
                    ))
                    
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/text",
                        name=f"会话{session_id[:8]}-第{page_num}页文本",
                        description=f"PDF第{page_num}页的结构化文本内容和元数据",
                        mimeType="application/json"
                    ))
                
                # 添加文档整体信息资源
                resources.append(Resource(
                    uri=f"pdf-doc://{session_id}/metadata",
                    name=f"会话{session_id[:8]}-文档信息",
                    description="PDF文档的元数据和整体结构信息",
                    mimeType="application/json"
                ))
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            try:
                if uri.startswith("pdf-page://"):
                    # 解析页面资源URI: pdf-page://session_id/page-N/type
                    parts = uri.replace("pdf-page://", "").split("/")
                    session_id, page_part, resource_type = parts
                    page_num = int(page_part.split("-")[1])
                    
                    session = self.sessions.get(session_id)
                    if not session:
                        raise ValueError(f"未找到转换会话: {session_id}")
                    
                    if resource_type == "image":
                        # 返回页面图片
                        if page_num - 1 < len(session.page_images):
                            image_data = session.page_images[page_num - 1]
                            return ResourceContents(
                                uri=uri,
                                mimeType="image/png",
                                text=base64.b64encode(image_data).decode()
                            )
                        else:
                            raise ValueError(f"页面图片不存在: 第{page_num}页")
                    
                    elif resource_type == "text":
                        # 返回页面文本和结构信息
                        if page_num - 1 < len(session.page_data):
                            page_data = session.page_data[page_num - 1]
                            return ResourceContents(
                                uri=uri,
                                mimeType="application/json",
                                text=json.dumps(page_data, ensure_ascii=False, indent=2)
                            )
                        else:
                            raise ValueError(f"页面数据不存在: 第{page_num}页")
                    
                    else:
                        raise ValueError(f"未知资源类型: {resource_type}")
                
                elif uri.startswith("pdf-doc://"):
                    # 解析文档资源URI: pdf-doc://session_id/metadata
                    parts = uri.replace("pdf-doc://", "").split("/")
                    session_id, resource_type = parts
                    
                    session = self.sessions.get(session_id)
                    if not session:
                        raise ValueError(f"未找到转换会话: {session_id}")
                    
                    if resource_type == "metadata":
                        doc_info = {
                            "session_id": session_id,
                            "pdf_path": str(session.pdf_path),
                            "total_pages": session.total_pages,
                            "metadata": session.metadata.__dict__ if session.metadata else None,
                            "created_at": session.created_at
                        }
                        return ResourceContents(
                            uri=uri,
                            mimeType="application/json",
                            text=json.dumps(doc_info, ensure_ascii=False, indent=2)
                        )
                    else:
                        raise ValueError(f"未知文档资源类型: {resource_type}")
                
                else:
                    raise ValueError(f"未知资源URI格式: {uri}")
                    
            except Exception as e:
                logger.error(f"读取资源失败 {uri}: {e}")
                raise
        
        @self.server.list_prompts()
        async def list_prompts():
            """列出可用的提示模板"""
            return [
                Prompt(
                    name="analyze_pdf_layout",
                    description="分析PDF页面布局结构的AI提示模板，用于识别文档元素和排版特征"
                ),
                Prompt(
                    name="generate_typst_code",
                    description="根据页面分析结果生成Typst代码的AI提示模板"
                ),
                Prompt(
                    name="optimize_typst_output",
                    description="优化和完善生成的Typst代码的提示模板"
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None):
            """获取提示模板内容"""
            if name == "analyze_pdf_layout":
                messages = self._get_layout_analysis_prompt(arguments)
                return messages
            elif name == "generate_typst_code":
                messages = self._get_typst_generation_prompt(arguments)
                return messages
            elif name == "optimize_typst_output":
                messages = self._get_typst_optimization_prompt(arguments)
                return messages
            else:
                raise ValueError(f"未知提示模板: {name}")
    
    async def _check_multimodal_capability(self, args: Dict[str, Any]):
        """检测当前AI模型是否支持多模态（图片识别）能力"""
        
        # 创建一个简单的测试图片 (1x1像素的PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        # 返回包含图片的内容，让AI分析
        return [
                TextContent(
                    type="text", 
                    text="""🔍 **多模态能力检测**

⚠️ **重要提示**: 此PDF转Typst MCP服务需要AI具备图片识别能力！

🧪 **检测方法**: 下面有一个测试图片，请描述你能看到什么：

如果你能看到并描述这个图片，说明当前模型支持多模态 ✅
如果你无法处理图片，需要切换到支持图片的模型 ❌

📋 **支持的多模态模型**:
• Claude 3.5 Sonnet (推荐)
• GPT-4V, GPT-4o
• Gemini Pro Vision
• Qwen-VL, LLaVA, InternVL 等

❌ **不支持的模型**:
• GPT-3.5, Claude Instant
• 所有纯文本大模型

💡 **如何切换模型**:
- VSCode: 设置 → AI Model → 选择支持视觉的模型
- Cursor: Ctrl+Shift+P → Select Model → 选择多模态模型  
- Trae: 设置中选择多模态模型

🚀 **检测完成后**，如果当前模型支持多模态，就可以开始使用PDF转换功能了！"""
                ),
                ImageContent(
                    type="image",
                    data=base64.b64encode(test_image_data).decode('utf-8'),
                    mimeType="image/png"
                ),
                TextContent(
                    type="text",
                    text="""
📊 **检测结果判断**:

✅ **如果你能描述上面的图片内容** → 当前模型支持多模态，可以使用PDF转换服务
❌ **如果你提示无法处理图片** → 需要切换到支持图片的多模态大模型

🔄 **下一步**: 如果检测通过，使用 `start_pdf_conversion` 开始转换PDF文件。"""
                )
            ]

    async def _start_conversion(self, args: Dict[str, Any]):
        """开始PDF转换流程"""
        pdf_path = Path(args["pdf_path"])
        session_id = args.get("session_id") or str(uuid.uuid4())
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 创建转换会话
            session = ConversionSession(session_id, pdf_path)
            
            # 提取PDF元数据和页面信息
            logger.info(f"开始解析PDF: {pdf_path}")
            session.metadata = self.parser.extract_metadata(pdf_path)
            pages_info = self.parser.get_page_info(pdf_path)
            session.total_pages = len(pages_info)
            
            # 将每页转换为高分辨率图片
            logger.info("提取页面图像...")
            session.page_images = await asyncio.to_thread(self._extract_page_images, pdf_path)
            
            # 提取每页的文本和结构信息
            logger.info("提取页面文本和结构...")
            session.page_data = await asyncio.to_thread(self._extract_page_data, pdf_path)
            
            # 存储会话
            self.sessions[session_id] = session
            
            # 构建分析指导
            analysis_guide = self._build_analysis_guide(session_id, session.total_pages)
            
            return [TextContent(
                    type="text",
                    text=f"✅ PDF转换会话已启动！\n\n"
                         f"📄 **文档信息**:\n"
                         f"- 文件: {pdf_path.name}\n"
                         f"- 页数: {session.total_pages}\n"
                         f"- 会话ID: `{session_id}`\n"
                         f"- 文档标题: {session.metadata.title or '未知'}\n\n"
                         f"🔍 **AI分析指导**:\n\n"
                         f"{analysis_guide}\n\n"
                         f"💡 **提示**: 您现在可以访问页面图片和文本资源，使用AI提示模板进行智能分析。"
                )]
            
        except Exception as e:
            logger.error(f"启动转换失败: {e}")
            raise
    
    async def _analyze_pdf_structure(self, args: Dict[str, Any]):
        """分析PDF结构"""
        pdf_path = Path(args["pdf_path"])
        
        try:
            # 获取文档信息
            doc_info = await asyncio.to_thread(self.pipeline.get_document_info, pdf_path)
            
            if "error" in doc_info:
                raise Exception(f"❌ 分析失败: {doc_info['error']}")
            
            # 格式化输出
            analysis_text = f"""📊 **PDF结构分析报告**

📄 **基本信息**:
- 文件路径: {doc_info['file_path']}
- 文件大小: {doc_info['file_size_mb']:.2f} MB
- 总页数: {doc_info['pages']}

📋 **文档元数据**:
- 标题: {doc_info['metadata'].get('title') or '未知'}
- 作者: {doc_info['metadata'].get('author') or '未知'}
- 创建时间: {doc_info['metadata'].get('creation_date') or '未知'}

📈 **内容统计**:
- 文本块: {doc_info['text_blocks']} 个
- 表格: {doc_info['tables']} 个
- 图片: {doc_info['images']} 个

📏 **页面信息** (前5页):
"""
            
            for page in doc_info['page_info']:
                analysis_text += f"- 第{page['number']}页: {page['width']:.0f}×{page['height']:.0f} (比例 {page['aspect_ratio']:.2f})\n"
            
            if doc_info['pages'] > 5:
                analysis_text += f"- ... 以及其余 {doc_info['pages'] - 5} 页\n"
            
            analysis_text += f"\n💡 **建议**: 使用 `start_pdf_conversion` 开始详细转换流程。"
            
            return [TextContent(type="text", text=analysis_text)]
            
        except Exception as e:
            logger.error(f"结构分析失败: {e}")
            raise
    
    async def _preview_typst_output(self, args: Dict[str, Any]):
        """预览Typst输出"""
        pdf_path = Path(args["pdf_path"])
        max_pages = args.get("max_pages", 3)
        
        try:
            # 获取预览结果
            preview_result = await asyncio.to_thread(
                self.pipeline.preview_conversion, 
                pdf_path, 
                max_pages
            )
            
            if "error" in preview_result:
                raise Exception(f"❌ 预览失败: {preview_result['error']}")
            
            # 格式化输出
            stats = preview_result['statistics']
            preview_text = f"""🔍 **Typst转换预览** (前{stats['pages_processed']}页)

📊 **处理统计**:
- 文本块: {stats['text_blocks']} 个
- 标题: {stats['headings']} 个
- 段落: {stats['paragraphs']} 个
- 表格: {stats['tables']} 个
- 图片: {stats['images']} 个
- 列表: {stats['lists']} 个

📝 **Typst代码预览**:
```typst
{preview_result['preview_content']}
```

💡 **提示**: 这只是前{max_pages}页的预览。使用 `start_pdf_conversion` 进行完整转换。
"""
            
            return [TextContent(type="text", text=preview_text)]
            
        except Exception as e:
            logger.error(f"预览失败: {e}")
            raise
    
    async def _finalize_conversion(self, args: Dict[str, Any]):
        """完成转换流程"""
        session_id = args["session_id"]
        typst_content = args["typst_content"]
        output_path = args.get("output_path")
        
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"未找到转换会话: {session_id}")
        
        try:
            # 确定输出路径
            if not output_path:
                output_path = session.pdf_path.parent / f"{session.pdf_path.stem}.typ"
            else:
                output_path = Path(output_path)
            
            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建图像目录并复制图像文件（如果需要）
            image_dir = None
            if session.page_data:
                images_found = any(page.get('images') for page in session.page_data)
                if images_found:
                    image_dir = output_path.parent / f"{output_path.stem}_images"
                    image_dir.mkdir(exist_ok=True)
                    
                    # 提取并保存图像
                    await self._save_images_from_session(session, image_dir)
            
            # 始终尝试修复图片路径，即使没有检测到图片
            # 因为用户可能在Typst内容中手动添加了图片引用
            if image_dir:
                # 修复Typst内容中的图片路径
                typst_content = self._fix_image_paths_in_typst(typst_content, image_dir.name)
            else:
                # 即使没有图像目录，也尝试检测Typst内容中的图片引用
                import re
                if re.search(r'image\("([^"]+)"', typst_content):
                    # 如果发现图片引用，创建默认图像目录
                    image_dir = output_path.parent / f"{output_path.stem}_images"
                    image_dir.mkdir(exist_ok=True)
                    typst_content = self._fix_image_paths_in_typst(typst_content, image_dir.name)
            
            # 写入Typst文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(typst_content)
            
            # 清理会话
            del self.sessions[session_id]
            
            result_text = f"""✅ **PDF转换完成！**

📄 **输出信息**:
- 源文件: {session.pdf_path.name}
- 输出文件: {output_path}
- 总页数: {session.total_pages}
- 会话ID: {session_id}
"""
            
            if image_dir:
                result_text += f"- 图像目录: {image_dir}\n"
            
            result_text += f"""
📝 **文件大小**: {output_path.stat().st_size / 1024:.1f} KB

🎉 **转换成功！** 您的PDF已经转换为Typst格式，得益于AI大模型的智能布局识别和代码生成能力。
"""
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"完成转换失败: {e}")
            raise
    
    async def _list_active_sessions(self, args: Dict[str, Any]):
        """列出活跃会话"""
        if not self.sessions:
            return [TextContent(
                    type="text",
                    text="📭 **当前没有活跃的转换会话**\n\n使用 `start_pdf_conversion` 开始新的转换。"
                )]
        
        sessions_text = "📋 **活跃的转换会话**:\n\n"
        
        for session_id, session in self.sessions.items():
            sessions_text += f"🔹 **会话** `{session_id[:8]}...`\n"
            sessions_text += f"   - 文件: {session.pdf_path.name}\n"
            sessions_text += f"   - 页数: {session.total_pages}\n"
            sessions_text += f"   - 创建时间: {session.created_at:.0f}\n\n"
        
        sessions_text += "💡 使用会话ID调用 `finalize_conversion` 完成转换。"
        
        return [TextContent(type="text", text=sessions_text)]
    
    def _build_analysis_guide(self, session_id: str, total_pages: int) -> str:
        """构建AI分析指导"""
        guide = "请按以下步骤进行AI增强的PDF分析:\n\n"
        
        # 显示前几页的具体指导
        pages_to_show = min(total_pages, 3)
        
        for page_num in range(1, pages_to_show + 1):
            guide += f"**📄 第{page_num}页分析**:\n"
            guide += f"1. 📷 查看页面图片: `pdf-page://{session_id}/page-{page_num}/image`\n"
            guide += f"2. 📝 查看文本结构: `pdf-page://{session_id}/page-{page_num}/text`\n"
            guide += f"3. 🤖 使用 `analyze_pdf_layout` 提示模板进行AI布局分析\n"
            guide += f"4. ⚡ 使用 `generate_typst_code` 提示模板生成对应代码\n\n"
        
        if total_pages > 3:
            guide += f"**📚 剩余页面**: 对其余 {total_pages - 3} 页重复上述步骤\n\n"
        
        guide += "**🎯 完成步骤**:\n"
        guide += f"- 整合所有页面的分析结果\n"
        guide += f"- 使用 `optimize_typst_output` 优化最终代码\n"
        guide += f"- 调用 `finalize_conversion` 完成转换\n\n"
        guide += f"**📋 文档信息**: `pdf-doc://{session_id}/metadata`"
        
        return guide
    
    def _get_layout_analysis_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取布局分析提示模板"""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="""🤖 **PDF页面布局分析专家**

您是一个专业的文档布局分析AI。请仔细分析提供的PDF页面图片和文本数据，识别以下要素：

## 📋 分析要求

### 1. **页面整体结构**
- 布局类型：单栏/双栏/多栏/混合布局
- 页面方向：纵向/横向
- 边距和间距特征

### 2. **文本层次结构**
- 主标题、副标题、章节标题
- 正文段落
- 引用、注释、脚注
- 页眉、页脚

### 3. **特殊元素识别**
- 表格位置和结构
- 图片、图表位置
- 数学公式
- 列表（有序/无序）
- 代码块

### 4. **排版特征**
- 字体大小层次
- 字体样式（粗体、斜体）
- 文本对齐方式
- 行距和段落间距
- 颜色和背景

## 📤 输出格式

请以JSON格式输出分析结果：

```json
{
  "page_layout": {
    "type": "single_column|double_column|multi_column|mixed",
    "orientation": "portrait|landscape",
    "margins": {"top": 0, "bottom": 0, "left": 0, "right": 0}
  },
  "text_hierarchy": [
    {
      "level": 1,
      "type": "title|subtitle|heading|paragraph|quote|footnote",
      "content": "文本内容",
      "position": {"x": 0, "y": 0, "width": 0, "height": 0},
      "style": {
        "font_size": 16,
        "font_weight": "normal|bold",
        "font_style": "normal|italic",
        "alignment": "left|center|right|justify",
        "color": "#000000"
      }
    }
  ],
  "special_elements": [
    {
      "type": "table|image|formula|list|code",
      "position": {"x": 0, "y": 0, "width": 0, "height": 0},
      "properties": {}
    }
  ],
  "layout_notes": "布局特点和注意事项"
}
```

🎯 **目标**: 为后续的Typst代码生成提供准确、详细的布局信息。"""
                )
            )
        ]
    
    def _get_typst_generation_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取Typst代码生成提示模板"""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="""⚡ **Typst代码生成专家 - 复杂布局识别**

基于PDF页面布局分析结果，请生成高质量的Typst代码。特别注意处理复杂的多栏布局、表格和图文混排。

## 🎯 布局识别要求

### 1. **多栏布局检测**
- 分析文本块的X坐标，识别左栏(x<400)和右栏(x>=400)
- 使用`#columns(2, gutter: 1cm)`处理双栏布局
- 用`#colbreak()`在合适位置换栏

### 2. **文本块分类**
- **页眉**: Y坐标 < 30的文本，用`#align(right)[...]`
- **页脚**: Y坐标 > 500的文本，用`#align(center)[...]`
- **标题**: 字体较大或包含特殊关键词的文本
- **正文**: 按Y坐标排序的普通文本块

### 3. **内容完整性**
- **必须包含所有文本块**，不能遗漏任何内容
- 按照原文档的阅读顺序重新组织内容
- 保持文本的逻辑连贯性

## 📝 复杂布局处理模板

```typst
#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: "Times New Roman", size: 8pt, lang: "en")
#set par(justify: true, leading: 0.6em)

// 页眉
#align(right)[页眉内容]

// 双栏布局
#columns(2, gutter: 1cm)[
  // 左栏内容
  == 章节标题
  
  正文内容...
  
  #colbreak()
  
  // 右栏内容  
  == 另一章节
  
  更多内容...
]

// 图片（跨栏）
#figure(
  image("images/图片.jpg", width: 80%),
  caption: [图片说明]
)

// 页脚
#align(center)[#text(size: 7pt)[页脚信息]]
```

## 🔍 关键处理规则

### 文本块处理顺序
1. 提取所有文本块并按位置分类
2. 左栏内容按Y坐标排序
3. 右栏内容按Y坐标排序  
4. 识别章节标题和层次结构
5. 合并相关的文本片段

### 布局识别逻辑
- X < 400: 左栏内容
- X >= 400: 右栏内容
- Y < 30: 页眉区域
- Y > 500: 页脚区域
- 字体大小 > 8pt 且文本较短: 可能是标题

### 内容组织原则
- 保持原文档的阅读流程
- 正确识别目录、正文、参考文献等部分
- 处理表格和图片的位置关系

## ✅ 质量检查清单

- [ ] **完整性**: 包含了所有文本块的内容
- [ ] **布局**: 正确识别并重现了多栏布局
- [ ] **顺序**: 文本按照逻辑阅读顺序排列
- [ ] **格式**: 标题、正文、页眉页脚格式正确
- [ ] **语法**: Typst代码语法无误

🚀 **请基于提供的页面数据生成完整的Typst代码，确保不遗漏任何文本内容！**"""
                )
            )
        ]
    
    def _get_typst_optimization_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取Typst优化提示模板"""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="""🔧 **Typst代码优化专家**

请对生成的Typst代码进行优化和完善，提升代码质量和渲染效果。

## 🎯 优化目标

### 1. **代码质量**
- 消除语法错误和警告
- 优化代码结构和可读性
- 统一命名规范和风格

### 2. **性能优化**
- 减少重复代码
- 优化函数调用
- 提高编译效率

### 3. **视觉效果**
- 调整间距和对齐
- 优化字体和颜色
- 改善整体排版效果

### 4. **兼容性**
- 确保跨平台兼容
- 使用标准Typst功能
- 避免实验性特性

## 🔍 检查清单

- [ ] **语法检查**: 所有语法都正确
- [ ] **样式一致**: 全文样式保持统一
- [ ] **布局准确**: 与原文档布局匹配
- [ ] **元素完整**: 所有内容元素都包含
- [ ] **代码整洁**: 结构清晰，注释适当
- [ ] **性能良好**: 编译快速，无冗余

## 📤 输出要求

提供优化后的完整Typst代码，包括：
1. 文档配置和样式设置
2. 所有页面内容
3. 必要的注释说明

🎨 **目标**: 生成可直接使用的高质量Typst文档代码。"""
                )
            )
        ]
    
    def _extract_page_images(self, pdf_path: Path) -> List[bytes]:
        """提取页面图像"""
        try:
            import fitz  # PyMuPDF
            
            images = []
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # 以高DPI渲染页面，用于AI分析
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放提高清晰度
                pix = page.get_pixmap(matrix=mat)
                images.append(pix.tobytes("png"))
            
            doc.close()
            logger.info(f"成功提取 {len(images)} 页图像")
            return images
            
        except Exception as e:
            logger.error(f"提取页面图像失败: {e}")
            raise
    
    def _extract_page_data(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """提取页面文本和结构数据"""
        try:
            # 使用现有解析器提取内容
            text_blocks = self.parser.extract_text(pdf_path)
            tables = self.parser.extract_tables(pdf_path)
            images = self.parser.extract_images(pdf_path)
            
            # 按页面组织数据
            pages_data = {}
            
            # 组织文本块
            for block in text_blocks:
                page_num = block.page
                if page_num not in pages_data:
                    pages_data[page_num] = {
                        "text_blocks": [], 
                        "tables": [], 
                        "images": [],
                        "page_number": page_num
                    }
                
                pages_data[page_num]["text_blocks"].append({
                    "text": block.text,
                    "bbox": [block.bbox.x0, block.bbox.y0, block.bbox.x1, block.bbox.y1],
                    "font": {
                        "name": block.font.name,
                        "size": block.font.size,
                        "styles": [style.value for style in block.font.styles]
                    },
                    "element_type": block.element_type.value
                })
            
            # 组织表格
            for table in tables:
                page_num = table.page
                if page_num not in pages_data:
                    pages_data[page_num] = {
                        "text_blocks": [], 
                        "tables": [], 
                        "images": [],
                        "page_number": page_num
                    }
                
                pages_data[page_num]["tables"].append({
                    "rows": table.rows,
                    "cols": table.cols,
                    "cells": [
                        {"text": cell.text, "row": cell.row, "col": cell.col} 
                        for cell in table.cells
                    ],
                    "bbox": [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1],
                    "has_header": table.has_header
                })
            
            # 组织图像
            for image in images:
                page_num = image.page
                if page_num not in pages_data:
                    pages_data[page_num] = {
                        "text_blocks": [], 
                        "tables": [], 
                        "images": [],
                        "page_number": page_num
                    }
                
                pages_data[page_num]["images"].append({
                    "filename": image.filename,
                    "bbox": [image.bbox.x0, image.bbox.y0, image.bbox.x1, image.bbox.y1],
                    "width": image.width,
                    "height": image.height,
                    "format": image.format
                })
            
            # 转换为有序列表
            max_page = max(pages_data.keys()) if pages_data else 0
            result = []
            
            for page_num in range(1, max_page + 1):
                page_data = pages_data.get(page_num, {
                    "text_blocks": [], 
                    "tables": [], 
                    "images": [],
                    "page_number": page_num
                })
                result.append(page_data)
            
            logger.info(f"成功提取 {len(result)} 页数据")
            return result
            
        except Exception as e:
            logger.error(f"提取页面数据失败: {e}")
            raise
    
    async def _save_images_from_session(self, session: ConversionSession, image_dir: Path):
        """从会话中保存图像文件"""
        try:
            # 重新提取图像（这次保存到文件）
            images = self.parser.extract_images(session.pdf_path)
            
            for image in images:
                image_path = image_dir / image.filename
                with open(image_path, 'wb') as f:
                    f.write(image.data)
            
            logger.info(f"保存了 {len(images)} 个图像文件到 {image_dir}")
            
        except Exception as e:
            logger.warning(f"保存图像失败: {e}")
    
    def _fix_image_paths_in_typst(self, typst_content: str, correct_image_dir: str) -> str:
        """修复Typst内容中的图片路径"""
        import re
        
        logger.info(f"开始修复图片路径，目标目录: {correct_image_dir}")
        
        def fix_path(match):
            original_path = match.group(1)
            # 提取文件名（去掉可能错误的目录前缀）
            filename = original_path.split('/')[-1]
            # 使用正确的图像目录
            new_path = f'image("{correct_image_dir}/{filename}"'
            logger.info(f"修复图片路径: {original_path} -> {correct_image_dir}/{filename}")
            return new_path
        
        # 查找并替换所有image()调用中的路径
        fixed_content = re.sub(r'image\("([^"]+)"', fix_path, typst_content)
        
        if fixed_content != typst_content:
            logger.info("图片路径已修复")
        else:
            logger.warning("未发现需要修复的图片路径")
        
        return fixed_content
    
    def cleanup_old_sessions(self, max_age_seconds: float = 3600):
        """清理过期的会话"""
        current_time = asyncio.get_event_loop().time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.created_at > max_age_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"清理过期会话: {session_id}")
        
        return len(expired_sessions)
    
    async def run(self):
        """运行MCP服务器"""
        try:
            from mcp.server.stdio import stdio_server
            
            logger.info("启动PDF转Typst MCP服务器...")
            
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, 
                    write_stream, 
                    InitializationOptions(
                        server_name="pdf-to-typst",
                        server_version="1.0.0",
                        capabilities={}
                    )
                )
        
        except Exception as e:
            logger.error(f"MCP服务器运行失败: {e}")
            raise


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行服务器
    server = PDFToTypstMCPServer()
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
    finally:
        logger.info("PDF转Typst MCP服务器已关闭")


if __name__ == "__main__":
    asyncio.run(main())
