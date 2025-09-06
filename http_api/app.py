#!/usr/bin/env python3
"""
PDF转Typst HTTP API服务

为MCP服务提供HTTP API包装，使其可以被VSCode、Cursor等各种编辑器和Agent使用。
"""

import asyncio
import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入MCP服务器
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mcp_server.server import PDFToTypstMCPServer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="PDF转Typst API",
    description="AI增强的PDF转Typst转换服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局MCP服务器实例
mcp_server: Optional[PDFToTypstMCPServer] = None

# 请求/响应模型
class ConvertRequest(BaseModel):
    pdf_path: str
    output_path: Optional[str] = None
    session_id: Optional[str] = None

class AnalyzeRequest(BaseModel):
    pdf_path: str

class PreviewRequest(BaseModel):
    pdf_path: str
    max_pages: int = 3

class FinalizeRequest(BaseModel):
    session_id: str
    typst_content: str
    output_path: Optional[str] = None

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    session_id: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化MCP服务器"""
    global mcp_server
    try:
        mcp_server = PDFToTypstMCPServer()
        logger.info("MCP服务器初始化成功")
    except Exception as e:
        logger.error(f"MCP服务器初始化失败: {e}")
        raise


@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径，返回API信息"""
    return {
        "name": "PDF转Typst API",
        "version": "1.0.0",
        "description": "AI增强的PDF转Typst转换服务",
        "docs": "/docs",
        "mcp_status": "active" if mcp_server else "inactive"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mcp_server": mcp_server is not None,
        "active_sessions": len(mcp_server.sessions) if mcp_server else 0
    }


@app.post("/convert", response_model=APIResponse)
async def convert_pdf(request: ConvertRequest):
    """转换PDF文件"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    try:
        pdf_path = Path(request.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF文件不存在: {request.pdf_path}")
        
        # 启动转换会话
        session_id = request.session_id or str(uuid.uuid4())
        
        session_result = await mcp_server._start_conversion({
            "pdf_path": str(pdf_path),
            "session_id": session_id
        })
        
        if session_result.isError:
            raise HTTPException(status_code=400, detail=session_result.content[0].text)
        
        # AI增强转换 - 返回会话信息供进一步处理
        return APIResponse(
            success=True,
            data={
                "message": "转换会话已启动，请使用AI分析页面布局",
                "session_id": session_id,
                "total_pages": mcp_server.sessions[session_id].total_pages,
                "next_steps": [
                    f"获取页面图片: GET /session/{session_id}/page/{{page_num}}/image",
                    f"获取页面文本: GET /session/{session_id}/page/{{page_num}}/text", 
                    f"获取AI提示: GET /prompts/{{template_name}}",
                    f"完成转换: POST /finalize"
                ]
            },
            session_id=session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-convert")
async def upload_and_convert(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """上传并转换PDF文件（AI增强）"""
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # AI增强转换文件
        convert_request = ConvertRequest(
            pdf_path=tmp_path
        )
        
        result = await convert_pdf(convert_request)
        
        # 后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_file, tmp_path)
        
        return result
    
    except Exception as e:
        logger.error(f"上传转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=APIResponse)
async def analyze_pdf(request: AnalyzeRequest):
    """分析PDF结构"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    try:
        result = await mcp_server._analyze_pdf_structure({
            "pdf_path": request.pdf_path
        })
        
        if result.isError:
            raise HTTPException(status_code=400, detail=result.content[0].text)
        
        return APIResponse(
            success=True,
            data={"analysis": result.content[0].text}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preview", response_model=APIResponse)
async def preview_typst(request: PreviewRequest):
    """预览Typst输出"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    try:
        result = await mcp_server._preview_typst_output({
            "pdf_path": request.pdf_path,
            "max_pages": request.max_pages
        })
        
        if result.isError:
            raise HTTPException(status_code=400, detail=result.content[0].text)
        
        return APIResponse(
            success=True,
            data={"preview": result.content[0].text}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finalize", response_model=APIResponse)
async def finalize_conversion(request: FinalizeRequest):
    """完成转换"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    try:
        result = await mcp_server._finalize_conversion({
            "session_id": request.session_id,
            "typst_content": request.typst_content,
            "output_path": request.output_path
        })
        
        if result.isError:
            raise HTTPException(status_code=400, detail=result.content[0].text)
        
        return APIResponse(
            success=True,
            data={"message": result.content[0].text}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完成转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=APIResponse)
async def list_sessions():
    """列出活跃会话"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    try:
        result = await mcp_server._list_active_sessions({})
        
        return APIResponse(
            success=True,
            data={
                "sessions": list(mcp_server.sessions.keys()),
                "count": len(mcp_server.sessions),
                "details": result.content[0].text
            }
        )
    
    except Exception as e:
        logger.error(f"列出会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/page/{page_num}/image")
async def get_page_image(session_id: str, page_num: int):
    """获取页面图片"""
    if not mcp_server or session_id not in mcp_server.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        session = mcp_server.sessions[session_id]
        if page_num < 1 or page_num > len(session.page_images):
            raise HTTPException(status_code=404, detail="页面不存在")
        
        image_data = session.page_images[page_num - 1]
        
        # 保存临时图片文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(image_data)
            tmp_path = tmp_file.name
        
        return FileResponse(
            tmp_path,
            media_type="image/png",
            filename=f"page_{page_num}.png"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取页面图片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/page/{page_num}/text", response_model=APIResponse)
async def get_page_text(session_id: str, page_num: int):
    """获取页面文本数据"""
    if not mcp_server or session_id not in mcp_server.sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        session = mcp_server.sessions[session_id]
        if page_num < 1 or page_num > len(session.page_data):
            raise HTTPException(status_code=404, detail="页面不存在")
        
        page_data = session.page_data[page_num - 1]
        
        return APIResponse(
            success=True,
            data=page_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取页面文本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompts/{template_name}", response_model=APIResponse)
async def get_prompt_template(template_name: str):
    """获取AI提示模板"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP服务器未初始化")
    
    valid_templates = ["analyze_pdf_layout", "generate_typst_code", "optimize_typst_output"]
    if template_name not in valid_templates:
        raise HTTPException(status_code=404, detail=f"模板不存在。可用模板: {valid_templates}")
    
    try:
        if template_name == "analyze_pdf_layout":
            messages = mcp_server._get_layout_analysis_prompt(None)
        elif template_name == "generate_typst_code":
            messages = mcp_server._get_typst_generation_prompt(None)
        else:  # optimize_typst_output
            messages = mcp_server._get_typst_optimization_prompt(None)
        
        return APIResponse(
            success=True,
            data={
                "template_name": template_name,
                "content": messages[0].content.text
            }
        )
    
    except Exception as e:
        logger.error(f"获取提示模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


def cleanup_temp_file(file_path: str):
    """清理临时文件"""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"清理临时文件失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF转Typst HTTP API服务")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    
    args = parser.parse_args()
    
    print(f"""
🚀 PDF转Typst HTTP API服务启动

📡 服务地址: http://{args.host}:{args.port}
📚 API文档: http://{args.host}:{args.port}/docs
🔧 健康检查: http://{args.host}:{args.port}/health

💡 使用示例:
   curl -X POST "http://{args.host}:{args.port}/analyze" \\
        -H "Content-Type: application/json" \\
        -d '{{"pdf_path": "/path/to/file.pdf"}}'
""")
    
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
