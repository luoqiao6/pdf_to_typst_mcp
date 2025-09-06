#!/usr/bin/env python3
"""
PDF转Typst MCP服务器启动脚本

使用方法:
1. 直接运行: python start_server.py
2. 配置到Claude Desktop: 在claude_desktop_config.json中添加配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入服务器
from mcp_server.server import main

if __name__ == "__main__":
    import asyncio
    
    try:
        # 设置环境变量
        os.environ.setdefault("PYTHONPATH", str(project_root))
        
        # 运行服务器
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print("\n✅ MCP服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
