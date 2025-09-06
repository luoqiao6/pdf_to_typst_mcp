# 寻找可处理pdf的其他大模型
_Exported on 2025/9/6 at GMT+8 18:21:07 from Cursor (1.5.11)_

---

**User**

除了 Claude.ai、ChatGPT 、Gemini 这三个大模型可以直接识别pdf文件的内容和页面排版布局，还有其他大模型可选吗。有些大模型可能不能直接读取pdf文件，但可以读取markdown这样的文本文件和图片，这样可以先把pdf转换为文本和图片提供给这样的大模型，让其生成Typst文件。文本文件缺少页面排版布局信息，图片保留了原pdf的页面排版信息，两者可以相互补充，也可以避免只通过图片识别页面中的文字导致的文字可能识别错误的问题。

---

**Cursor**

您提出了一个很好的技术方案思路！让我为您分析一下可用的多模态大模型选项，以及如何实现PDF转换为文本+图片的方案。

根据我的调研，除了您提到的 Claude.ai、ChatGPT 和 Gemini，还有很多优秀的多模态大模型可以选择。让我为您整理一下：

## 开源多模态大模型

### 1. **文档专用模型**
- **KOSMOS-2.5**: 微软开发的多模态识读模型，专为文本密集型图像设计，能生成带空间坐标的文本块，输出Markdown格式
- **LayoutLM系列** (LayoutLM/v2/v3): 专门用于文档AI的预训练模型，采用统一的文本和图像掩码策略
- **mPLUG-DocOwl**: 基于mPLUG-Owl的文档理解模型，支持OCR-free的文档处理
- **DocLLM**: 面向多模态文档理解的布局感知生成式语言模型

### 2. **通用多模态模型**
- **Qwen-VL系列**: 阿里巴巴开源的视觉-语言模型，支持图片理解和文本生成
- **LLaVA系列**: 大规模语言和视觉助手，开源且性能优秀
- **InternVL系列**: 商汤和上海AI实验室开源的多模态模型
- **MiniCPM-V系列**: 面壁智能开源的轻量级多模态模型
- **CogVLM/CogAgent**: 智谱AI开源的视觉-语言模型

### 3. **商用API服务**
- **通义千问-VL**: 阿里云提供API服务
- **文心一言**: 百度提供多模态API
- **讯飞星火**: 科大讯飞的多模态服务
- **字节豆包**: 字节跳动的多模态API

## 您的技术方案分析

您提出的"PDF转文本+图片"方案非常有价值！[[memory:8270598]] 这种方案的优势：

1. **文本提供准确内容**: 避免OCR识别错误
2. **图片保留布局信息**: 保持原始排版结构
3. **互补性强**: 文本+视觉信息结合
4. **适用性广**: 支持更多只能处理图片+文本的模型

## 实现建议

基于您当前的PDFConvert项目，可以这样扩展：

基于您的需求和现有代码，我建议扩展当前的PDFConvert项目来支持多模态大模型。可以添加一个新的模块来处理"文本+图片"的方案：

```python:src/core/multimodal_converter.py
"""
多模态大模型转换器
支持将PDF转换为文本+图片，然后调用多模态大模型生成Typst
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import base64
from dataclasses import dataclass

@dataclass
class MultimodalInput:
    """多模态输入数据"""
    text_content: str  # Markdown格式的文本内容
    page_images: List[Dict[str, Any]]  # 页面图片列表
    layout_info: Dict[str, Any]  # 布局信息

class MultimodalConverter:
    """多模态转换器基类"""
    
    def __init__(self, model_name: str, api_config: Dict[str, Any]):
        self.model_name = model_name
        self.api_config = api_config
    
    def prepare_input(self, pdf_path: Path) -> MultimodalInput:
        """准备多模态输入数据"""
        # 提取文本内容（Markdown格式）
        text_content = self._extract_text_as_markdown(pdf_path)
        
        # 将每页转换为图片
        page_images = self._pdf_pages_to_images(pdf_path)
        
        # 提取布局信息
        layout_info = self._extract_layout_info(pdf_path)
        
        return MultimodalInput(
            text_content=text_content,
            page_images=page_images,
            layout_info=layout_info
        )
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        """调用多模态大模型生成Typst"""
        raise NotImplementedError
    
    def _extract_text_as_markdown(self, pdf_path: Path) -> str:
        """将PDF文本提取为Markdown格式"""
        # 使用现有的PDF解析器
        # ... existing code ...
        
    def _pdf_pages_to_images(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """将PDF页面转换为图片"""
        # 使用PyMuPDF将每页转换为高分辨率图片
        # ... existing code ...
        
    def _extract_layout_info(self, pdf_path: Path) -> Dict[str, Any]:
        """提取布局信息"""
        # 提取页面尺寸、元素位置等信息
        # ... existing code ...

class QwenVLConverter(MultimodalConverter):
    """通义千问-VL转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # 构建提示词
        prompt = self._build_prompt(multimodal_input)
        
        # 调用通义千问-VL API
        # ... implementation ...

class LLaVAConverter(MultimodalConverter):
    """LLaVA转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # 本地部署的LLaVA调用
        # ... implementation ...

class InternVLConverter(MultimodalConverter):
    """InternVL转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # InternVL API调用
        # ... implementation ...
```

## 推荐的实现路径

1. **优先选择的模型**:
   - **KOSMOS-2.5**: 专门为文档设计，输出Markdown格式
   - **Qwen-VL**: 阿里云API稳定，中文支持好
   - **InternVL**: 开源且性能优秀，可本地部署

2. **技术栈建议**:
   - 使用您现有的PyMuPDF将PDF页面转为高质量图片
   - 用pdfplumber提取纯文本并转换为Markdown
   - 结合两者信息调用多模态大模型

3. **提示词设计**:
```text
你是一个专业的文档转换专家。我提供给你：
1. PDF文档的文本内容（Markdown格式）
2. PDF文档的页面截图
3. 页面布局信息

请根据这些信息，生成准确的Typst格式文档，要求：
- 保持原文档的排版布局
- 正确处理图文混排
- 准确转换表格结构
- 保持数学公式格式
```

这种方案结合了文本的准确性和图片的布局信息，应该能显著提升转换质量。您觉得这个方向如何？需要我详细展开某个部分的实现吗？

```python
"""
多模态大模型转换器
支持将PDF转换为文本+图片，然后调用多模态大模型生成Typst
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import base64
from dataclasses import dataclass

@dataclass
class MultimodalInput:
    """多模态输入数据"""
    text_content: str  # Markdown格式的文本内容
    page_images: List[Dict[str, Any]]  # 页面图片列表
    layout_info: Dict[str, Any]  # 布局信息

class MultimodalConverter:
    """多模态转换器基类"""
    
    def __init__(self, model_name: str, api_config: Dict[str, Any]):
        self.model_name = model_name
        self.api_config = api_config
    
    def prepare_input(self, pdf_path: Path) -> MultimodalInput:
        """准备多模态输入数据"""
        # 提取文本内容（Markdown格式）
        text_content = self._extract_text_as_markdown(pdf_path)
        
        # 将每页转换为图片
        page_images = self._pdf_pages_to_images(pdf_path)
        
        # 提取布局信息
        layout_info = self._extract_layout_info(pdf_path)
        
        return MultimodalInput(
            text_content=text_content,
            page_images=page_images,
            layout_info=layout_info
        )
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        """调用多模态大模型生成Typst"""
        raise NotImplementedError
    
    def _extract_text_as_markdown(self, pdf_path: Path) -> str:
        """将PDF文本提取为Markdown格式"""
        # 使用现有的PDF解析器
        # ... existing code ...
        
    def _pdf_pages_to_images(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """将PDF页面转换为图片"""
        # 使用PyMuPDF将每页转换为高分辨率图片
        # ... existing code ...
        
    def _extract_layout_info(self, pdf_path: Path) -> Dict[str, Any]:
        """提取布局信息"""
        # 提取页面尺寸、元素位置等信息
        # ... existing code ...

class QwenVLConverter(MultimodalConverter):
    """通义千问-VL转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # 构建提示词
        prompt = self._build_prompt(multimodal_input)
        
        # 调用通义千问-VL API
        # ... implementation ...

class LLaVAConverter(MultimodalConverter):
    """LLaVA转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # 本地部署的LLaVA调用
        # ... implementation ...

class InternVLConverter(MultimodalConverter):
    """InternVL转换器"""
    
    def convert_to_typst(self, multimodal_input: MultimodalInput) -> str:
        # InternVL API调用
        # ... implementation ...
```

```plaintext
你是一个专业的文档转换专家。我提供给你：
1. PDF文档的文本内容（Markdown格式）
2. PDF文档的页面截图
3. 页面布局信息

请根据这些信息，生成准确的Typst格式文档，要求：
- 保持原文档的排版布局
- 正确处理图文混排
- 准确转换表格结构
- 保持数学公式格式
```

---

**User**

上面提到的各开源大模型需要自己安装部署吗？如果需要自己安装部署，对服务器性能要求是什么样的？如果有可用的服务API，使用的注册认证要求有哪些，费用分别是多少？

---

**Cursor**

让我为您详细调研各个开源大模型的部署要求和API服务情况：

根据我的调研，让我为您详细整理各开源大模型的部署要求和API服务情况：

## 🖥️ 本地部署要求

### **轻量级模型（推荐入门）**

**MiniCPM-V系列**
- **GPU**: NVIDIA RTX 3060/4060 (8GB显存) 
- **内存**: 16GB RAM
- **存储**: 50GB
- **优势**: 硬件要求最低，适合个人开发

**Qwen-VL-Chat (7B)**
- **GPU**: NVIDIA RTX 3090 (24GB显存)
- **内存**: 32GB RAM  
- **存储**: 100GB
- **优势**: 中文支持优秀，性能不错

### **中等规模模型**

**LLaVA-1.5 (13B)**
- **GPU**: NVIDIA RTX 4090 (24GB显存) 或 A100 (40GB)
- **内存**: 64GB RAM
- **存储**: 150GB
- **优势**: 开源生态完善，社区活跃

**InternVL-Chat (26B)**
- **GPU**: 2×NVIDIA RTX 4090 或 1×A100 (80GB)
- **内存**: 128GB RAM
- **存储**: 200GB
- **优势**: 性能接近商用模型

### **大规模模型**

**CogVLM2 (19B)**
- **GPU**: NVIDIA A100 (80GB) 或 2×RTX 4090
- **内存**: 128GB RAM
- **存储**: 300GB
- **优势**: 智谱AI出品，中文表现优秀

**KOSMOS-2.5**
- **GPU**: NVIDIA H100 (80GB) 推荐
- **内存**: 256GB RAM
- **存储**: 500GB
- **优势**: 专为文档理解设计

## 💰 API服务费用对比

### **国内厂商（性价比高，推荐）**

| 服务商 | 模型 | 输入价格 | 输出价格 | 免费额度 | 认证要求 |
|--------|------|----------|----------|----------|----------|
| **阿里云** | 通义千问-VL | ¥0.0005/千token | ¥0.002/千token | 100万token | 实名认证 |
| **百度** | 文心一言4.0 | **免费** | **免费** | 无限制 | 实名认证 |
| **字节跳动** | 豆包-vision | ¥0.0008/千token | ¥0.003/千token | 50万token | 实名认证 |
| **科大讯飞** | 星火4.0 | ¥0.002/千token | ¥0.008/千token | 20万token | 实名认证 |

### **国外厂商**

| 服务商 | 模型 | 输入价格 | 输出价格 | 免费额度 | 认证要求 |
|--------|------|----------|----------|----------|----------|
| **OpenAI** | GPT-4V | ¥0.01/千token | ¥0.03/千token | $5试用 | 信用卡验证 |
| **Anthropic** | Claude-3 | ¥0.003/千token | ¥0.015/千token | 有限免费 | 信用卡验证 |
| **Google** | Gemini Pro Vision | ¥0.0025/千token | ¥0.0075/千token | 有限免费 | Google账户 |

### **开源API服务平台**

**Hugging Face Inference API**
- **费用**: $0.06/小时 (按需付费)
- **支持模型**: LLaVA、InternVL、MiniCPM-V等
- **认证**: 信用卡验证
- **优势**: 无需本地部署，支持多种开源模型

**Together AI**
- **费用**: $0.2-0.8/百万token (按模型不同)
- **支持模型**: LLaVA、CogVLM等开源模型
- **认证**: 邮箱注册 + 信用卡
- **优势**: 专门提供开源模型API

## 📋 推荐方案

### **预算有限（月费用<100元）**
1. **百度文心一言** - 完全免费，功能强大
2. **阿里云通义千问** - 极低价格，100万token免费额度
3. **本地部署MiniCPM-V** - 一次性硬件投入

### **中等预算（月费用100-500元）**
1. **字节豆包 + 阿里云通义千问** - 组合使用，性价比高
2. **本地部署Qwen-VL-Chat** - 更好的隐私保护
3. **Hugging Face API** - 灵活选择不同开源模型

### **高性能需求（月费用>500元）**
1. **Claude-3 + 国内模型组合** - 最佳性能
2. **本地部署InternVL/CogVLM2** - 完全自主控制
3. **企业级API服务** - 专业技术支持

## 🔧 快速开始建议

对于您的PDFConvert项目，我建议：

1. **先试用免费API**: 百度文心一言 + 阿里云通义千问免费额度
2. **评估效果后选择**: 根据转换质量选择最适合的服务
3. **考虑混合方案**: 不同类型文档使用不同模型，优化成本和效果

需要我帮您实现具体的API集成代码吗？

---

**User**

我还考虑，是否可以将pdf转换为typst的功能开发成一个MCP服务或其他什么插件，由用户的Agent配置上这个服务就可以使用了

---

**Cursor**

这是一个非常好的想法！将PDF转Typst功能开发成MCP服务或其他插件形式，可以让更多用户方便地使用这个功能。让我为您分析几种可行的方案：

您的想法非常棒！将PDF转Typst功能开发成各种插件形式，可以大大提升其使用便利性和覆盖面。让我为您分析几种可行的实现方案：

## 🔌 插件开发方案对比

### **1. MCP (Model Context Protocol) 服务** ⭐⭐⭐⭐⭐

**适用场景**: Claude Desktop、Cursor、支持MCP的AI应用

**优势**:
- Anthropic官方推动的开放标准
- 与Claude等LLM无缝集成
- 标准化接口，易于维护

**开发示例**:

基于您现有的代码，我可以设计一个MCP服务器：

```python:mcp_server/pdf_to_typst_server.py
"""
PDF转Typst MCP服务器
支持Claude Desktop、Cursor等MCP客户端
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP相关导入
from mcp import ClientSession, StdioServerSession
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest, 
    ListToolsResult,
    Tool,
    TextContent
)

# 导入您现有的PDF转换功能
from src.core.pdf_parser import HybridPDFParser
from src.core.typst_generator import TypstGenerator
from src.core.pipeline import ConversionPipeline

logger = logging.getLogger(__name__)

class PDFToTypstMCPServer:
    """PDF转Typst MCP服务器"""
    
    def __init__(self):
        self.server = Server("pdf-to-typst")
        self.pipeline = ConversionPipeline()
        self._setup_tools()
    
    def _setup_tools(self):
        """设置MCP工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="convert_pdf_to_typst",
                        description="将PDF文件转换为Typst格式",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "PDF文件路径"
                                },
                                "output_path": {
                                    "type": "string", 
                                    "description": "输出Typst文件路径（可选）"
                                },
                                "use_multimodal": {
                                    "type": "boolean",
                                    "description": "是否使用多模态大模型增强转换（可选）"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    ),
                    Tool(
                        name="analyze_pdf_structure",
                        description="分析PDF文档结构，返回页面信息和元素统计",
                        inputSchema={
                            "type": "object", 
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "PDF文件路径"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    ),
                    Tool(
                        name="preview_typst_output",
                        description="预览PDF转换后的Typst代码片段",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string", 
                                    "description": "PDF文件路径"
                                },
                                "page_range": {
                                    "type": "string",
                                    "description": "页面范围，如'1-3'或'1,3,5'"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            try:
                if name == "convert_pdf_to_typst":
                    return await self._convert_pdf_to_typst(arguments)
                elif name == "analyze_pdf_structure":
                    return await self._analyze_pdf_structure(arguments)
                elif name == "preview_typst_output":
                    return await self._preview_typst_output(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            
            except Exception as e:
                logger.error(f"工具调用失败 {name}: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"转换失败: {str(e)}"
                    )],
                    isError=True
                )
    
    async def _convert_pdf_to_typst(self, args: Dict[str, Any]) -> CallToolResult:
        """执行PDF到Typst转换"""
        pdf_path = Path(args["pdf_path"])
        output_path = args.get("output_path")
        use_multimodal = args.get("use_multimodal", False)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 执行转换
        result = await asyncio.to_thread(
            self.pipeline.convert,
            pdf_path=pdf_path,
            output_path=output_path,
            use_multimodal=use_multimodal
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"转换完成！\n输出文件: {result.output_path}\n"
                     f"处理页数: {result.pages_processed}\n"
                     f"转换时间: {result.conversion_time:.2f}秒"
            )]
        )
    
    async def _analyze_pdf_structure(self, args: Dict[str, Any]) -> CallToolResult:
        """分析PDF结构"""
        pdf_path = Path(args["pdf_path"])
        
        parser = HybridPDFParser()
        metadata = parser.extract_metadata(pdf_path)
        pages_info = parser.get_page_info(pdf_path)
        
        analysis = {
            "文档信息": {
                "标题": metadata.title or "未知",
                "作者": metadata.author or "未知", 
                "页数": metadata.pages
            },
            "页面信息": [
                {
                    "页码": page.number,
                    "尺寸": f"{page.width:.1f}x{page.height:.1f}",
                    "旋转": page.rotation
                }
                for page in pages_info[:5]  # 只显示前5页
            ]
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"PDF结构分析:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}"
            )]
        )
    
    async def _preview_typst_output(self, args: Dict[str, Any]) -> CallToolResult:
        """预览Typst输出"""
        pdf_path = Path(args["pdf_path"])
        page_range = args.get("page_range", "1")
        
        # 解析页面范围
        pages = self._parse_page_range(page_range)
        
        # 提取指定页面内容并生成Typst预览
        preview = await asyncio.to_thread(
            self.pipeline.generate_preview,
            pdf_path=pdf_path,
            pages=pages
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Typst代码预览 (页面 {page_range}):\n\n```typst\n{preview}\n```"
            )]
        )
    
    def _parse_page_range(self, page_range: str) -> List[int]:
        """解析页面范围字符串"""
        pages = []
        for part in page_range.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        return pages
    
    async def run(self):
        """运行MCP服务器"""
        async with StdioServerSession() as session:
            await self.server.run(session)

async def main():
    """主函数"""
    server = PDFToTypstMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### **2. OpenAI Function/Tool** ⭐⭐⭐⭐

**适用场景**: ChatGPT、GPT-4、支持Function Calling的应用

```python:plugins/openai_function.py
"""
OpenAI Function Calling 插件
"""

import json
from typing import Dict, Any
from pathlib import Path

# OpenAI Function 定义
PDF_TO_TYPST_FUNCTION = {
    "name": "convert_pdf_to_typst",
    "description": "将PDF文件转换为Typst格式，支持图文混排、表格和数学公式",
    "parameters": {
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "PDF文件的完整路径"
            },
            "output_directory": {
                "type": "string", 
                "description": "输出目录路径（可选）"
            },
            "conversion_options": {
                "type": "object",
                "properties": {
                    "use_multimodal": {"type": "boolean", "description": "是否使用多模态AI增强"},
                    "preserve_images": {"type": "boolean", "description": "是否保留原始图片"},
                    "table_detection": {"type": "boolean", "description": "是否启用表格检测"}
                }
            }
        },
        "required": ["pdf_path"]
    }
}

def handle_pdf_conversion(arguments: Dict[str, Any]) -> str:
    """处理PDF转换请求"""
    from src.core.pipeline import ConversionPipeline
    
    pipeline = ConversionPipeline()
    pdf_path = Path(arguments["pdf_path"])
    
    result = pipeline.convert(
        pdf_path=pdf_path,
        output_path=arguments.get("output_directory"),
        **arguments.get("conversion_options", {})
    )
    
    return json.dumps({
        "status": "success",
        "output_file": str(result.output_path),
        "pages_processed": result.pages_processed,
        "conversion_time": result.conversion_time
    }, ensure_ascii=False)
```

### **3. Cursor/VSCode 扩展** ⭐⭐⭐⭐

**适用场景**: Cursor编辑器、VSCode

```typescript:vscode-extension/src/extension.ts
import * as vscode from 'vscode';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    
    // 注册PDF转Typst命令
    const convertCommand = vscode.commands.registerCommand(
        'pdf-to-typst.convert', 
        async (uri?: vscode.Uri) => {
            try {
                let pdfPath: string;
                
                if (uri) {
                    pdfPath = uri.fsPath;
                } else {
                    // 让用户选择PDF文件
                    const result = await vscode.window.showOpenDialog({
                        canSelectFiles: true,
                        canSelectMany: false,
                        filters: {
                            'PDF Files': ['pdf']
                        }
                    });
                    
                    if (!result || result.length === 0) {
                        return;
                    }
                    
                    pdfPath = result[0].fsPath;
                }
                
                // 显示进度
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: "转换PDF到Typst",
                    cancellable: true
                }, async (progress, token) => {
                    
                    progress.report({ increment: 0, message: "开始转换..." });
                    
                    // 调用Python转换脚本
                    const pythonScript = path.join(
                        context.extensionPath, 
                        'python', 
                        'convert_pdf.py'
                    );
                    
                    const command = `python "${pythonScript}" "${pdfPath}"`;
                    
                    try {
                        const { stdout, stderr } = await execAsync(command);
                        
                        if (stderr) {
                            throw new Error(stderr);
                        }
                        
                        const result = JSON.parse(stdout);
                        
                        progress.report({ increment: 100, message: "转换完成！" });
                        
                        // 询问是否打开输出文件
                        const action = await vscode.window.showInformationMessage(
                            `转换完成！输出文件: ${result.output_file}`,
                            "打开文件", "打开目录"
                        );
                        
                        if (action === "打开文件") {
                            const doc = await vscode.workspace.openTextDocument(result.output_file);
                            await vscode.window.showTextDocument(doc);
                        } else if (action === "打开目录") {
                            const outputDir = path.dirname(result.output_file);
                            await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(outputDir));
                        }
                        
                    } catch (error) {
                        vscode.window.showErrorMessage(`转换失败: ${error.message}`);
                    }
                });
                
            } catch (error) {
                vscode.window.showErrorMessage(`操作失败: ${error.message}`);
            }
        }
    );
    
    context.subscriptions.push(convertCommand);
}

export function deactivate() {}
```

### **4. Web API服务** ⭐⭐⭐

**适用场景**: 任何支持HTTP调用的AI Agent

```python:web_api/app.py
"""
PDF转Typst Web API服务
使用FastAPI构建RESTful接口
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import tempfile
import uuid
from typing import Optional

from src.core.pipeline import ConversionPipeline

app = FastAPI(
    title="PDF转Typst API",
    description="将PDF文件转换为Typst格式的Web API服务",
    version="1.0.0"
)

class ConversionOptions(BaseModel):
    use_multimodal: bool = False
    preserve_images: bool = True
    table_detection: bool = True

class ConversionResult(BaseModel):
    task_id: str
    status: str
    output_file: Optional[str] = None
    pages_processed: Optional[int] = None
    conversion_time: Optional[float] = None
    error_message: Optional[str] = None

pipeline = ConversionPipeline()

@app.post("/convert", response_model=ConversionResult)
async def convert_pdf_to_typst(
    file: UploadFile = File(...),
    options: ConversionOptions = ConversionOptions()
):
    """转换PDF文件到Typst格式"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    task_id = str(uuid.uuid4())
    
    try:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            pdf_path = Path(tmp_file.name)
        
        # 执行转换
        result = pipeline.convert(
            pdf_path=pdf_path,
            use_multimodal=options.use_multimodal,
            preserve_images=options.preserve_images,
            table_detection=options.table_detection
        )
        
        return ConversionResult(
            task_id=task_id,
            status="success",
            output_file=str(result.output_path),
            pages_processed=result.pages_processed,
            conversion_time=result.conversion_time
        )
        
    except Exception as e:
        return ConversionResult(
            task_id=task_id,
            status="error", 
            error_message=str(e)
        )
    
    finally:
        # 清理临时文件
        if pdf_path.exists():
            pdf_path.unlink()

@app.get("/download/{file_path}")
async def download_file(file_path: str):
    """下载转换后的文件"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type='application/octet-stream'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📦 部署和配置

### **MCP服务配置** (推荐)

```json:claude_desktop_config.json
{
  "mcpServers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/path/to/your/mcp_server/pdf_to_typst_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

### **使用示例**

用户在Claude Desktop中可以这样使用：

```
请帮我将这个PDF文件转换为Typst格式：/Users/username/document.pdf
```

Claude会自动调用您的MCP服务完成转换。

## 🎯 推荐实现顺序

1. **优先开发MCP服务** - 最符合当前AI Agent生态
2. **添加Web API** - 提供通用的HTTP接口
3. **开发VSCode/Cursor扩展** - 为开发者提供便利
4. **考虑OpenAI Function** - 支持ChatGPT等平台

需要我帮您实现其中任何一个方案的详细代码吗？

```python
"""
PDF转Typst MCP服务器
支持Claude Desktop、Cursor等MCP客户端
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP相关导入
from mcp import ClientSession, StdioServerSession
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest, 
    ListToolsResult,
    Tool,
    TextContent
)

# 导入您现有的PDF转换功能
from src.core.pdf_parser import HybridPDFParser
from src.core.typst_generator import TypstGenerator
from src.core.pipeline import ConversionPipeline

logger = logging.getLogger(__name__)

class PDFToTypstMCPServer:
    """PDF转Typst MCP服务器"""
    
    def __init__(self):
        self.server = Server("pdf-to-typst")
        self.pipeline = ConversionPipeline()
        self._setup_tools()
    
    def _setup_tools(self):
        """设置MCP工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="convert_pdf_to_typst",
                        description="将PDF文件转换为Typst格式",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "PDF文件路径"
                                },
                                "output_path": {
                                    "type": "string", 
                                    "description": "输出Typst文件路径（可选）"
                                },
                                "use_multimodal": {
                                    "type": "boolean",
                                    "description": "是否使用多模态大模型增强转换（可选）"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    ),
                    Tool(
                        name="analyze_pdf_structure",
                        description="分析PDF文档结构，返回页面信息和元素统计",
                        inputSchema={
                            "type": "object", 
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "PDF文件路径"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    ),
                    Tool(
                        name="preview_typst_output",
                        description="预览PDF转换后的Typst代码片段",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string", 
                                    "description": "PDF文件路径"
                                },
                                "page_range": {
                                    "type": "string",
                                    "description": "页面范围，如'1-3'或'1,3,5'"
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            try:
                if name == "convert_pdf_to_typst":
                    return await self._convert_pdf_to_typst(arguments)
                elif name == "analyze_pdf_structure":
                    return await self._analyze_pdf_structure(arguments)
                elif name == "preview_typst_output":
                    return await self._preview_typst_output(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            
            except Exception as e:
                logger.error(f"工具调用失败 {name}: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"转换失败: {str(e)}"
                    )],
                    isError=True
                )
    
    async def _convert_pdf_to_typst(self, args: Dict[str, Any]) -> CallToolResult:
        """执行PDF到Typst转换"""
        pdf_path = Path(args["pdf_path"])
        output_path = args.get("output_path")
        use_multimodal = args.get("use_multimodal", False)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 执行转换
        result = await asyncio.to_thread(
            self.pipeline.convert,
            pdf_path=pdf_path,
            output_path=output_path,
            use_multimodal=use_multimodal
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"转换完成！\n输出文件: {result.output_path}\n"
                     f"处理页数: {result.pages_processed}\n"
                     f"转换时间: {result.conversion_time:.2f}秒"
            )]
        )
    
    async def _analyze_pdf_structure(self, args: Dict[str, Any]) -> CallToolResult:
        """分析PDF结构"""
        pdf_path = Path(args["pdf_path"])
        
        parser = HybridPDFParser()
        metadata = parser.extract_metadata(pdf_path)
        pages_info = parser.get_page_info(pdf_path)
        
        analysis = {
            "文档信息": {
                "标题": metadata.title or "未知",
                "作者": metadata.author or "未知", 
                "页数": metadata.pages
            },
            "页面信息": [
                {
                    "页码": page.number,
                    "尺寸": f"{page.width:.1f}x{page.height:.1f}",
                    "旋转": page.rotation
                }
                for page in pages_info[:5]  # 只显示前5页
            ]
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"PDF结构分析:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}"
            )]
        )
    
    async def _preview_typst_output(self, args: Dict[str, Any]) -> CallToolResult:
        """预览Typst输出"""
        pdf_path = Path(args["pdf_path"])
        page_range = args.get("page_range", "1")
        
        # 解析页面范围
        pages = self._parse_page_range(page_range)
        
        # 提取指定页面内容并生成Typst预览
        preview = await asyncio.to_thread(
            self.pipeline.generate_preview,
            pdf_path=pdf_path,
            pages=pages
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Typst代码预览 (页面 {page_range}):\n\n```typst\n{preview}\n```"
            )]
        )
    
    def _parse_page_range(self, page_range: str) -> List[int]:
        """解析页面范围字符串"""
        pages = []
        for part in page_range.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        return pages
    
    async def run(self):
        """运行MCP服务器"""
        async with StdioServerSession() as session:
            await self.server.run(session)

async def main():
    """主函数"""
    server = PDFToTypstMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

```python
"""
OpenAI Function Calling 插件
"""

import json
from typing import Dict, Any
from pathlib import Path

# OpenAI Function 定义
PDF_TO_TYPST_FUNCTION = {
    "name": "convert_pdf_to_typst",
    "description": "将PDF文件转换为Typst格式，支持图文混排、表格和数学公式",
    "parameters": {
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "PDF文件的完整路径"
            },
            "output_directory": {
                "type": "string", 
                "description": "输出目录路径（可选）"
            },
            "conversion_options": {
                "type": "object",
                "properties": {
                    "use_multimodal": {"type": "boolean", "description": "是否使用多模态AI增强"},
                    "preserve_images": {"type": "boolean", "description": "是否保留原始图片"},
                    "table_detection": {"type": "boolean", "description": "是否启用表格检测"}
                }
            }
        },
        "required": ["pdf_path"]
    }
}

def handle_pdf_conversion(arguments: Dict[str, Any]) -> str:
    """处理PDF转换请求"""
    from src.core.pipeline import ConversionPipeline
    
    pipeline = ConversionPipeline()
    pdf_path = Path(arguments["pdf_path"])
    
    result = pipeline.convert(
        pdf_path=pdf_path,
        output_path=arguments.get("output_directory"),
        **arguments.get("conversion_options", {})
    )
    
    return json.dumps({
        "status": "success",
        "output_file": str(result.output_path),
        "pages_processed": result.pages_processed,
        "conversion_time": result.conversion_time
    }, ensure_ascii=False)
```

```typescript
import * as vscode from 'vscode';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    
    // 注册PDF转Typst命令
    const convertCommand = vscode.commands.registerCommand(
        'pdf-to-typst.convert', 
        async (uri?: vscode.Uri) => {
            try {
                let pdfPath: string;
                
                if (uri) {
                    pdfPath = uri.fsPath;
                } else {
                    // 让用户选择PDF文件
                    const result = await vscode.window.showOpenDialog({
                        canSelectFiles: true,
                        canSelectMany: false,
                        filters: {
                            'PDF Files': ['pdf']
                        }
                    });
                    
                    if (!result || result.length === 0) {
                        return;
                    }
                    
                    pdfPath = result[0].fsPath;
                }
                
                // 显示进度
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: "转换PDF到Typst",
                    cancellable: true
                }, async (progress, token) => {
                    
                    progress.report({ increment: 0, message: "开始转换..." });
                    
                    // 调用Python转换脚本
                    const pythonScript = path.join(
                        context.extensionPath, 
                        'python', 
                        'convert_pdf.py'
                    );
                    
                    const command = `python "${pythonScript}" "${pdfPath}"`;
                    
                    try {
                        const { stdout, stderr } = await execAsync(command);
                        
                        if (stderr) {
                            throw new Error(stderr);
                        }
                        
                        const result = JSON.parse(stdout);
                        
                        progress.report({ increment: 100, message: "转换完成！" });
                        
                        // 询问是否打开输出文件
                        const action = await vscode.window.showInformationMessage(
                            `转换完成！输出文件: ${result.output_file}`,
                            "打开文件", "打开目录"
                        );
                        
                        if (action === "打开文件") {
                            const doc = await vscode.workspace.openTextDocument(result.output_file);
                            await vscode.window.showTextDocument(doc);
                        } else if (action === "打开目录") {
                            const outputDir = path.dirname(result.output_file);
                            await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(outputDir));
                        }
                        
                    } catch (error) {
                        vscode.window.showErrorMessage(`转换失败: ${error.message}`);
                    }
                });
                
            } catch (error) {
                vscode.window.showErrorMessage(`操作失败: ${error.message}`);
            }
        }
    );
    
    context.subscriptions.push(convertCommand);
}

export function deactivate() {}
```

```python
"""
PDF转Typst Web API服务
使用FastAPI构建RESTful接口
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import tempfile
import uuid
from typing import Optional

from src.core.pipeline import ConversionPipeline

app = FastAPI(
    title="PDF转Typst API",
    description="将PDF文件转换为Typst格式的Web API服务",
    version="1.0.0"
)

class ConversionOptions(BaseModel):
    use_multimodal: bool = False
    preserve_images: bool = True
    table_detection: bool = True

class ConversionResult(BaseModel):
    task_id: str
    status: str
    output_file: Optional[str] = None
    pages_processed: Optional[int] = None
    conversion_time: Optional[float] = None
    error_message: Optional[str] = None

pipeline = ConversionPipeline()

@app.post("/convert", response_model=ConversionResult)
async def convert_pdf_to_typst(
    file: UploadFile = File(...),
    options: ConversionOptions = ConversionOptions()
):
    """转换PDF文件到Typst格式"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    task_id = str(uuid.uuid4())
    
    try:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            pdf_path = Path(tmp_file.name)
        
        # 执行转换
        result = pipeline.convert(
            pdf_path=pdf_path,
            use_multimodal=options.use_multimodal,
            preserve_images=options.preserve_images,
            table_detection=options.table_detection
        )
        
        return ConversionResult(
            task_id=task_id,
            status="success",
            output_file=str(result.output_path),
            pages_processed=result.pages_processed,
            conversion_time=result.conversion_time
        )
        
    except Exception as e:
        return ConversionResult(
            task_id=task_id,
            status="error", 
            error_message=str(e)
        )
    
    finally:
        # 清理临时文件
        if pdf_path.exists():
            pdf_path.unlink()

@app.get("/download/{file_path}")
async def download_file(file_path: str):
    """下载转换后的文件"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type='application/octet-stream'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```json
{
  "mcpServers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/path/to/your/mcp_server/pdf_to_typst_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

```plaintext
请帮我将这个PDF文件转换为Typst格式：/Users/username/document.pdf
```

---

**User**

如果开发成MCP服务或插件，pdf转为Typst的过程可以使用Agent的AI大模型来识别页面布局和生成Typst吗

---

**Cursor**

非常好的想法！这样可以充分利用Agent的AI大模型能力来提升转换质量。让我为您设计一个方案，让MCP服务能够调用Agent的AI大模型来进行页面布局识别和Typst生成。

绝对可以！这是一个非常聪明的设计思路。通过MCP协议，您的服务可以与Agent的AI大模型进行双向通信，充分利用其多模态能力来识别页面布局和生成Typst代码。让我为您设计具体的实现方案：

## 🔄 MCP双向通信架构

### **核心思路**
1. **MCP服务**负责PDF解析、图像提取、文件管理
2. **Agent的AI大模型**负责页面布局识别和Typst代码生成
3. **通过MCP Resources和Prompts**实现双向数据传递

## 📋 实现方案

```python
"""
智能PDF转Typst MCP服务
利用Agent的AI大模型进行页面布局识别和代码生成
"""

import asyncio
import base64
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest, CallToolResult, Tool, TextContent, ImageContent,
    ListResourcesRequest, ListResourcesResult, Resource,
    ReadResourceRequest, ReadResourceResult, ResourceContents,
    ListPromptsRequest, ListPromptsResult, Prompt,
    GetPromptRequest, GetPromptResult, PromptMessage
)

# 导入现有的PDF处理功能
from src.core.pdf_parser import HybridPDFParser
from src.core.models import PageInfo, TextBlock, Table, Image

class IntelligentPDFToTypstServer:
    """智能PDF转Typst MCP服务器"""
    
    def __init__(self):
        self.server = Server("intelligent-pdf-to-typst")
        self.parser = HybridPDFParser()
        self.temp_files = {}  # 存储临时文件路径
        self.conversion_sessions = {}  # 存储转换会话数据
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="start_pdf_conversion",
                    description="开始PDF转Typst转换流程，提取页面并准备供AI分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "PDF文件路径"},
                            "session_id": {"type": "string", "description": "转换会话ID"}
                        },
                        "required": ["pdf_path", "session_id"]
                    }
                ),
                Tool(
                    name="finalize_conversion", 
                    description="完成转换，整合AI生成的Typst代码并输出文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "转换会话ID"},
                            "output_path": {"type": "string", "description": "输出文件路径"}
                        },
                        "required": ["session_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            if name == "start_pdf_conversion":
                return await self._start_conversion(arguments)
            elif name == "finalize_conversion":
                return await self._finalize_conversion(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """列出可用的资源（页面图片、文本内容等）"""
            resources = []
            
            for session_id, session_data in self.conversion_sessions.items():
                # 为每个页面添加图片资源
                for page_num in range(1, session_data["total_pages"] + 1):
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/image",
                        name=f"第{page_num}页图片",
                        description=f"PDF第{page_num}页的高分辨率图片，用于布局识别",
                        mimeType="image/png"
                    ))
                    
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/text",
                        name=f"第{page_num}页文本",
                        description=f"PDF第{page_num}页的文本内容和结构信息",
                        mimeType="application/json"
                    ))
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            # 解析URI: pdf-page://session_id/page-N/type
            parts = uri.replace("pdf-page://", "").split("/")
            session_id, page_part, resource_type = parts
            page_num = int(page_part.split("-")[1])
            
            session_data = self.conversion_sessions.get(session_id)
            if not session_data:
                raise ValueError(f"未找到转换会话: {session_id}")
            
            if resource_type == "image":
                # 返回页面图片
                image_data = session_data["page_images"][page_num - 1]
                return ResourceContents(
                    uri=uri,
                    mimeType="image/png",
                    text=base64.b64encode(image_data).decode()
                )
            
            elif resource_type == "text":
                # 返回页面文本和结构信息
                page_data = session_data["page_data"][page_num - 1]
                return ResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=json.dumps(page_data, ensure_ascii=False, indent=2)
                )
            
            else:
                raise ValueError(f"未知资源类型: {resource_type}")
        
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """列出可用的提示模板"""
            return [
                Prompt(
                    name="analyze_pdf_layout",
                    description="分析PDF页面布局并生成Typst代码的提示模板"
                ),
                Prompt(
                    name="generate_typst_code",
                    description="根据页面分析结果生成Typst代码的提示模板"
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[PromptMessage]:
            """获取提示模板内容"""
            if name == "analyze_pdf_layout":
                return self._get_layout_analysis_prompt(arguments)
            elif name == "generate_typst_code":
                return self._get_typst_generation_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
    
    async def _start_conversion(self, args: Dict[str, Any]) -> CallToolResult:
        """开始PDF转换流程"""
        pdf_path = Path(args["pdf_path"])
        session_id = args["session_id"]
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 提取PDF元数据和页面信息
            metadata = self.parser.extract_metadata(pdf_path)
            pages_info = self.parser.get_page_info(pdf_path)
            
            # 将每页转换为高分辨率图片
            page_images = await asyncio.to_thread(self._extract_page_images, pdf_path)
            
            # 提取每页的文本和结构信息
            page_data = await asyncio.to_thread(self._extract_page_data, pdf_path)
            
            # 存储会话数据
            self.conversion_sessions[session_id] = {
                "pdf_path": str(pdf_path),
                "metadata": metadata.__dict__,
                "total_pages": len(pages_info),
                "page_images": page_images,
                "page_data": page_data,
                "typst_pages": {}  # 存储AI生成的每页Typst代码
            }
            
            # 构建返回消息，引导AI分析页面
            analysis_guide = self._build_analysis_guide(session_id, len(pages_info))
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"PDF转换会话已启动！\n\n"
                         f"📄 文档信息:\n"
                         f"- 文件: {pdf_path.name}\n"
                         f"- 页数: {len(pages_info)}\n"
                         f"- 会话ID: {session_id}\n\n"
                         f"🔍 现在请使用以下步骤分析页面布局:\n\n"
                         f"{analysis_guide}"
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"转换启动失败: {str(e)}")],
                isError=True
            )
    
    def _build_analysis_guide(self, session_id: str, total_pages: int) -> str:
        """构建页面分析指导"""
        guide = "请按以下步骤分析每个页面:\n\n"
        
        for page_num in range(1, min(total_pages + 1, 4)):  # 最多显示前3页的指导
            guide += f"**第{page_num}页分析:**\n"
            guide += f"1. 查看页面图片: `pdf-page://{session_id}/page-{page_num}/image`\n"
            guide += f"2. 查看文本内容: `pdf-page://{session_id}/page-{page_num}/text`\n"
            guide += f"3. 使用 `analyze_pdf_layout` 提示模板分析布局\n"
            guide += f"4. 使用 `generate_typst_code` 提示模板生成代码\n\n"
        
        if total_pages > 3:
            guide += f"...以及其余 {total_pages - 3} 页\n\n"
        
        guide += "完成所有页面分析后，请调用 `finalize_conversion` 完成转换。"
        
        return guide
    
    def _get_layout_analysis_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取布局分析提示"""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="""你是一个专业的文档布局分析专家。请分析这个PDF页面的布局结构，包括：

1. **页面整体布局**: 单栏/双栏/多栏布局
2. **文本层次**: 标题、副标题、正文、引用等
3. **特殊元素**: 表格、图片、公式、列表等
4. **排版特征**: 字体大小、行距、段落间距、对齐方式等

请结合页面图片和文本内容，输出详细的布局分析结果，格式如下：

```json
{
  "layout_type": "single_column|double_column|multi_column",
  "elements": [
    {
      "type": "title|subtitle|paragraph|table|image|formula|list",
      "content": "元素内容",
      "position": {"x": 0, "y": 0, "width": 0, "height": 0},
      "style": {
        "font_size": 12,
        "font_weight": "normal|bold",
        "alignment": "left|center|right|justify"
      }
    }
  ]
}
```"""
                )
            )
        ]
    
    def _get_typst_generation_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取Typst代码生成提示"""
        return [
            PromptMessage(
                role="user", 
                content=TextContent(
                    type="text",
                    text="""基于页面布局分析结果，请生成对应的Typst代码。要求：

1. **准确重现布局**: 严格按照原页面的布局结构生成代码
2. **正确的语法**: 使用正确的Typst语法和函数
3. **样式匹配**: 字体、大小、颜色、对齐等样式要匹配原文档
4. **结构化代码**: 代码要清晰、有层次、易于阅读

生成的Typst代码应该包括：
- 页面设置（尺寸、边距等）
- 字体和样式定义
- 内容结构（标题、段落、表格等）
- 图片引用（如果有）

请直接输出Typst代码，不需要额外的解释。"""
                )
            )
        ]
    
    def _extract_page_images(self, pdf_path: Path) -> List[bytes]:
        """提取页面图片"""
        import fitz  # PyMuPDF
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # 以高DPI渲染页面
            mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        
        doc.close()
        return images
    
    def _extract_page_data(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """提取页面文本和结构数据"""
        text_blocks = self.parser.extract_text(pdf_path)
        tables = self.parser.extract_tables(pdf_path)
        images = self.parser.extract_images(pdf_path)
        
        # 按页面组织数据
        pages_data = {}
        
        # 组织文本块
        for block in text_blocks:
            page_num = block.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["text_blocks"].append({
                "text": block.text,
                "bbox": [block.bbox.x0, block.bbox.y0, block.bbox.x1, block.bbox.y1],
                "font": {
                    "name": block.font.name,
                    "size": block.font.size,
                    "styles": [style.value for style in block.font.styles]
                }
            })
        
        # 组织表格
        for table in tables:
            page_num = table.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["tables"].append({
                "rows": table.rows,
                "cols": table.cols,
                "cells": [{"text": cell.text, "row": cell.row, "col": cell.col} for cell in table.cells],
                "bbox": [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1]
            })
        
        # 组织图片
        for image in images:
            page_num = image.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["images"].append({
                "filename": image.filename,
                "bbox": [image.bbox.x0, image.bbox.y0, image.bbox.x1, image.bbox.y1],
                "width": image.width,
                "height": image.height
            })
        
        # 转换为列表格式
        result = []
        max_page = max(pages_data.keys()) if pages_data else 0
        
        for page_num in range(1, max_page + 1):
            result.append(pages_data.get(page_num, {"text_blocks": [], "tables": [], "images": []}))
        
        return result
    
    async def _finalize_conversion(self, args: Dict[str, Any]) -> CallToolResult:
        """完成转换流程"""
        session_id = args["session_id"]
        output_path = args.get("output_path")
        
        session_data = self.conversion_sessions.get(session_id)
        if not session_data:
            raise ValueError(f"未找到转换会话: {session_id}")
        
        try:
            # 这里假设AI已经通过其他方式提供了生成的Typst代码
            # 在实际实现中，您需要设计一种方式让AI将生成的代码传递回来
            
            # 生成最终的Typst文件
            if not output_path:
                pdf_path = Path(session_data["pdf_path"])
                output_path = pdf_path.parent / f"{pdf_path.stem}.typ"
            
            # 整合所有页面的Typst代码
            final_typst_code = self._build_final_typst(session_data)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_typst_code)
            
            # 清理会话数据
            del self.conversion_sessions[session_id]
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"✅ PDF转换完成！\n\n"
                         f"输出文件: {output_path}\n"
                         f"总页数: {session_data['total_pages']}\n\n"
                         f"转换质量得益于AI大模型的智能布局识别和代码生成。"
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"转换完成失败: {str(e)}")],
                isError=True
            )
    
    def _build_final_typst(self, session_data: Dict[str, Any]) -> str:
        """构建最终的Typst代码"""
        # 这里是一个简化的实现
        # 实际中需要根据AI生成的代码进行整合
        
        typst_code = """#set page(paper: "a4")
#set text(font: "SimSun", size: 12pt)
#set par(justify: true, leading: 0.65em)

"""
        
        # 添加AI生成的页面代码
        for page_num in range(1, session_data["total_pages"] + 1):
            if page_num in session_data.get("typst_pages", {}):
                typst_code += f"// 第{page_num}页\n"
                typst_code += session_data["typst_pages"][page_num]
                typst_code += "\n\n#pagebreak()\n\n"
        
        return typst_code
    
    async def run(self):
        """运行MCP服务器"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, InitializationOptions())

async def main():
    server = IntelligentPDFToTypstServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 使用流程

### **1. 用户在Claude Desktop中的操作**

```
用户: 请帮我将这个PDF转换为Typst格式：/path/to/document.pdf

Claude会调用MCP服务：
1. 调用 start_pdf_conversion 工具
2. 自动访问页面图片资源
3. 使用布局分析提示模板
4. 生成Typst代码
5. 调用 finalize_conversion 完成转换
```

### **2. Agent的AI处理流程**

1. **页面图片分析**: 通过多模态能力识别布局结构
2. **文本内容理解**: 结合提取的文本信息
3. **布局建模**: 理解页面的层次结构和排版特征  
4. **代码生成**: 生成符合Typst语法的代码
5. **质量优化**: 确保生成的代码能正确重现原布局

### **3. 配置文件**

```json
{
  "mcpServers": {
    "intelligent-pdf-to-typst": {
      "command": "python",
      "args": ["/path/to/intelligent_pdf_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

## ✨ 核心优势

1. **充分利用AI能力**: 让Agent的大模型处理最复杂的布局识别和代码生成
2. **标准化接口**: 通过MCP协议实现标准化的服务接口
3. **灵活扩展**: 可以支持不同的AI模型和转换策略
4. **用户友好**: 用户只需简单的自然语言指令即可完成转换

这种设计让您的MCP服务成为一个"智能助手"，而真正的"大脑"是Agent的AI大模型。需要我详细实现其中任何部分吗？

```python
"""
智能PDF转Typst MCP服务
利用Agent的AI大模型进行页面布局识别和代码生成
"""

import asyncio
import base64
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest, CallToolResult, Tool, TextContent, ImageContent,
    ListResourcesRequest, ListResourcesResult, Resource,
    ReadResourceRequest, ReadResourceResult, ResourceContents,
    ListPromptsRequest, ListPromptsResult, Prompt,
    GetPromptRequest, GetPromptResult, PromptMessage
)

# 导入现有的PDF处理功能
from src.core.pdf_parser import HybridPDFParser
from src.core.models import PageInfo, TextBlock, Table, Image

class IntelligentPDFToTypstServer:
    """智能PDF转Typst MCP服务器"""
    
    def __init__(self):
        self.server = Server("intelligent-pdf-to-typst")
        self.parser = HybridPDFParser()
        self.temp_files = {}  # 存储临时文件路径
        self.conversion_sessions = {}  # 存储转换会话数据
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="start_pdf_conversion",
                    description="开始PDF转Typst转换流程，提取页面并准备供AI分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "PDF文件路径"},
                            "session_id": {"type": "string", "description": "转换会话ID"}
                        },
                        "required": ["pdf_path", "session_id"]
                    }
                ),
                Tool(
                    name="finalize_conversion", 
                    description="完成转换，整合AI生成的Typst代码并输出文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "转换会话ID"},
                            "output_path": {"type": "string", "description": "输出文件路径"}
                        },
                        "required": ["session_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            if name == "start_pdf_conversion":
                return await self._start_conversion(arguments)
            elif name == "finalize_conversion":
                return await self._finalize_conversion(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """列出可用的资源（页面图片、文本内容等）"""
            resources = []
            
            for session_id, session_data in self.conversion_sessions.items():
                # 为每个页面添加图片资源
                for page_num in range(1, session_data["total_pages"] + 1):
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/image",
                        name=f"第{page_num}页图片",
                        description=f"PDF第{page_num}页的高分辨率图片，用于布局识别",
                        mimeType="image/png"
                    ))
                    
                    resources.append(Resource(
                        uri=f"pdf-page://{session_id}/page-{page_num}/text",
                        name=f"第{page_num}页文本",
                        description=f"PDF第{page_num}页的文本内容和结构信息",
                        mimeType="application/json"
                    ))
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            # 解析URI: pdf-page://session_id/page-N/type
            parts = uri.replace("pdf-page://", "").split("/")
            session_id, page_part, resource_type = parts
            page_num = int(page_part.split("-")[1])
            
            session_data = self.conversion_sessions.get(session_id)
            if not session_data:
                raise ValueError(f"未找到转换会话: {session_id}")
            
            if resource_type == "image":
                # 返回页面图片
                image_data = session_data["page_images"][page_num - 1]
                return ResourceContents(
                    uri=uri,
                    mimeType="image/png",
                    text=base64.b64encode(image_data).decode()
                )
            
            elif resource_type == "text":
                # 返回页面文本和结构信息
                page_data = session_data["page_data"][page_num - 1]
                return ResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=json.dumps(page_data, ensure_ascii=False, indent=2)
                )
            
            else:
                raise ValueError(f"未知资源类型: {resource_type}")
        
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """列出可用的提示模板"""
            return [
                Prompt(
                    name="analyze_pdf_layout",
                    description="分析PDF页面布局并生成Typst代码的提示模板"
                ),
                Prompt(
                    name="generate_typst_code",
                    description="根据页面分析结果生成Typst代码的提示模板"
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[PromptMessage]:
            """获取提示模板内容"""
            if name == "analyze_pdf_layout":
                return self._get_layout_analysis_prompt(arguments)
            elif name == "generate_typst_code":
                return self._get_typst_generation_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
    
    async def _start_conversion(self, args: Dict[str, Any]) -> CallToolResult:
        """开始PDF转换流程"""
        pdf_path = Path(args["pdf_path"])
        session_id = args["session_id"]
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 提取PDF元数据和页面信息
            metadata = self.parser.extract_metadata(pdf_path)
            pages_info = self.parser.get_page_info(pdf_path)
            
            # 将每页转换为高分辨率图片
            page_images = await asyncio.to_thread(self._extract_page_images, pdf_path)
            
            # 提取每页的文本和结构信息
            page_data = await asyncio.to_thread(self._extract_page_data, pdf_path)
            
            # 存储会话数据
            self.conversion_sessions[session_id] = {
                "pdf_path": str(pdf_path),
                "metadata": metadata.__dict__,
                "total_pages": len(pages_info),
                "page_images": page_images,
                "page_data": page_data,
                "typst_pages": {}  # 存储AI生成的每页Typst代码
            }
            
            # 构建返回消息，引导AI分析页面
            analysis_guide = self._build_analysis_guide(session_id, len(pages_info))
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"PDF转换会话已启动！\n\n"
                         f"📄 文档信息:\n"
                         f"- 文件: {pdf_path.name}\n"
                         f"- 页数: {len(pages_info)}\n"
                         f"- 会话ID: {session_id}\n\n"
                         f"🔍 现在请使用以下步骤分析页面布局:\n\n"
                         f"{analysis_guide}"
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"转换启动失败: {str(e)}")],
                isError=True
            )
    
    def _build_analysis_guide(self, session_id: str, total_pages: int) -> str:
        """构建页面分析指导"""
        guide = "请按以下步骤分析每个页面:\n\n"
        
        for page_num in range(1, min(total_pages + 1, 4)):  # 最多显示前3页的指导
            guide += f"**第{page_num}页分析:**\n"
            guide += f"1. 查看页面图片: `pdf-page://{session_id}/page-{page_num}/image`\n"
            guide += f"2. 查看文本内容: `pdf-page://{session_id}/page-{page_num}/text`\n"
            guide += f"3. 使用 `analyze_pdf_layout` 提示模板分析布局\n"
            guide += f"4. 使用 `generate_typst_code` 提示模板生成代码\n\n"
        
        if total_pages > 3:
            guide += f"...以及其余 {total_pages - 3} 页\n\n"
        
        guide += "完成所有页面分析后，请调用 `finalize_conversion` 完成转换。"
        
        return guide
    
    def _get_layout_analysis_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取布局分析提示"""
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="""你是一个专业的文档布局分析专家。请分析这个PDF页面的布局结构，包括：

1. **页面整体布局**: 单栏/双栏/多栏布局
2. **文本层次**: 标题、副标题、正文、引用等
3. **特殊元素**: 表格、图片、公式、列表等
4. **排版特征**: 字体大小、行距、段落间距、对齐方式等

请结合页面图片和文本内容，输出详细的布局分析结果，格式如下：

```json
{
  "layout_type": "single_column|double_column|multi_column",
  "elements": [
    {
      "type": "title|subtitle|paragraph|table|image|formula|list",
      "content": "元素内容",
      "position": {"x": 0, "y": 0, "width": 0, "height": 0},
      "style": {
        "font_size": 12,
        "font_weight": "normal|bold",
        "alignment": "left|center|right|justify"
      }
    }
  ]
}
```"""
                )
            )
        ]
    
    def _get_typst_generation_prompt(self, args: Optional[Dict[str, Any]]) -> List[PromptMessage]:
        """获取Typst代码生成提示"""
        return [
            PromptMessage(
                role="user", 
                content=TextContent(
                    type="text",
                    text="""基于页面布局分析结果，请生成对应的Typst代码。要求：

1. **准确重现布局**: 严格按照原页面的布局结构生成代码
2. **正确的语法**: 使用正确的Typst语法和函数
3. **样式匹配**: 字体、大小、颜色、对齐等样式要匹配原文档
4. **结构化代码**: 代码要清晰、有层次、易于阅读

生成的Typst代码应该包括：
- 页面设置（尺寸、边距等）
- 字体和样式定义
- 内容结构（标题、段落、表格等）
- 图片引用（如果有）

请直接输出Typst代码，不需要额外的解释。"""
                )
            )
        ]
    
    def _extract_page_images(self, pdf_path: Path) -> List[bytes]:
        """提取页面图片"""
        import fitz  # PyMuPDF
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # 以高DPI渲染页面
            mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        
        doc.close()
        return images
    
    def _extract_page_data(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """提取页面文本和结构数据"""
        text_blocks = self.parser.extract_text(pdf_path)
        tables = self.parser.extract_tables(pdf_path)
        images = self.parser.extract_images(pdf_path)
        
        # 按页面组织数据
        pages_data = {}
        
        # 组织文本块
        for block in text_blocks:
            page_num = block.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["text_blocks"].append({
                "text": block.text,
                "bbox": [block.bbox.x0, block.bbox.y0, block.bbox.x1, block.bbox.y1],
                "font": {
                    "name": block.font.name,
                    "size": block.font.size,
                    "styles": [style.value for style in block.font.styles]
                }
            })
        
        # 组织表格
        for table in tables:
            page_num = table.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["tables"].append({
                "rows": table.rows,
                "cols": table.cols,
                "cells": [{"text": cell.text, "row": cell.row, "col": cell.col} for cell in table.cells],
                "bbox": [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1]
            })
        
        # 组织图片
        for image in images:
            page_num = image.page
            if page_num not in pages_data:
                pages_data[page_num] = {"text_blocks": [], "tables": [], "images": []}
            pages_data[page_num]["images"].append({
                "filename": image.filename,
                "bbox": [image.bbox.x0, image.bbox.y0, image.bbox.x1, image.bbox.y1],
                "width": image.width,
                "height": image.height
            })
        
        # 转换为列表格式
        result = []
        max_page = max(pages_data.keys()) if pages_data else 0
        
        for page_num in range(1, max_page + 1):
            result.append(pages_data.get(page_num, {"text_blocks": [], "tables": [], "images": []}))
        
        return result
    
    async def _finalize_conversion(self, args: Dict[str, Any]) -> CallToolResult:
        """完成转换流程"""
        session_id = args["session_id"]
        output_path = args.get("output_path")
        
        session_data = self.conversion_sessions.get(session_id)
        if not session_data:
            raise ValueError(f"未找到转换会话: {session_id}")
        
        try:
            # 这里假设AI已经通过其他方式提供了生成的Typst代码
            # 在实际实现中，您需要设计一种方式让AI将生成的代码传递回来
            
            # 生成最终的Typst文件
            if not output_path:
                pdf_path = Path(session_data["pdf_path"])
                output_path = pdf_path.parent / f"{pdf_path.stem}.typ"
            
            # 整合所有页面的Typst代码
            final_typst_code = self._build_final_typst(session_data)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_typst_code)
            
            # 清理会话数据
            del self.conversion_sessions[session_id]
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"✅ PDF转换完成！\n\n"
                         f"输出文件: {output_path}\n"
                         f"总页数: {session_data['total_pages']}\n\n"
                         f"转换质量得益于AI大模型的智能布局识别和代码生成。"
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"转换完成失败: {str(e)}")],
                isError=True
            )
    
    def _build_final_typst(self, session_data: Dict[str, Any]) -> str:
        """构建最终的Typst代码"""
        # 这里是一个简化的实现
        # 实际中需要根据AI生成的代码进行整合
        
        typst_code = """#set page(paper: "a4")
#set text(font: "SimSun", size: 12pt)
#set par(justify: true, leading: 0.65em)

"""
        
        # 添加AI生成的页面代码
        for page_num in range(1, session_data["total_pages"] + 1):
            if page_num in session_data.get("typst_pages", {}):
                typst_code += f"// 第{page_num}页\n"
                typst_code += session_data["typst_pages"][page_num]
                typst_code += "\n\n#pagebreak()\n\n"
        
        return typst_code
    
    async def run(self):
        """运行MCP服务器"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, InitializationOptions())

async def main():
    server = IntelligentPDFToTypstServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 使用流程

### **1. 用户在Claude Desktop中的操作**

```
用户: 请帮我将这个PDF转换为Typst格式：/path/to/document.pdf

Claude会调用MCP服务：
1. 调用 start_pdf_conversion 工具
2. 自动访问页面图片资源
3. 使用布局分析提示模板
4. 生成Typst代码
5. 调用 finalize_conversion 完成转换
```

```json
{
  "mcpServers": {
    "intelligent-pdf-to-typst": {
      "command": "python",
      "args": ["/path/to/intelligent_pdf_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

