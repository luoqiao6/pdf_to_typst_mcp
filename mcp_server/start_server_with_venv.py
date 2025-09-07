#!/usr/bin/env python3
"""
MCP服务器启动脚本（自动激活虚拟环境）
解决Trae/Cursor等Agent中的Python路径问题
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 虚拟环境Python路径
    venv_python = project_root / "venv" / "bin" / "python"
    
    # MCP服务器脚本路径
    server_script = project_root / "mcp_server" / "start_server.py"
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    # 检查虚拟环境是否存在
    if not venv_python.exists():
        print(f"❌ 虚拟环境不存在: {venv_python}", file=sys.stderr)
        print("请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    
    # 使用虚拟环境中的Python启动MCP服务器
    try:
        # 使用exec替换当前进程，这样信号处理更好
        os.execve(str(venv_python), [str(venv_python), str(server_script)], env)
    except Exception as e:
        print(f"❌ MCP服务器启动失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
