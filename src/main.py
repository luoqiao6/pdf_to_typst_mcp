"""
PDF转Typst工具 - 主入口点

提供统一的应用入口，支持命令行和编程接口。
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from cli.main import cli

if __name__ == '__main__':
    cli()
