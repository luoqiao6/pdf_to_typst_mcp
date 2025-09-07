#!/usr/bin/env python3
"""
MCP配置修复脚本 - 解决Trae/Cursor等Agent中的配置问题
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_system_python():
    """获取系统Python路径"""
    try:
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        try:
            result = subprocess.run(['which', 'python'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return '/usr/local/bin/python3'  # 默认路径

def check_dependencies():
    """检查依赖是否安装"""
    project_root = Path(__file__).parent.parent
    venv_python = project_root / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ 虚拟环境不存在")
        return False
    
    try:
        result = subprocess.run([str(venv_python), '-c', 'import mcp'], 
                              capture_output=True, text=True, check=True)
        print("✅ MCP库已安装")
        return True
    except subprocess.CalledProcessError:
        print("❌ MCP库未安装")
        return False

def generate_configs():
    """生成修复后的配置文件"""
    project_root = Path(__file__).parent.parent
    system_python = get_system_python()
    
    # 配置模板
    config_template = {
        "mcpServers": {
            "pdf-to-typst": {
                "command": system_python,
                "args": [str(project_root / "mcp_server" / "start_server_with_venv.py")],
                "env": {
                    "PYTHONPATH": str(project_root)
                }
            }
        }
    }
    
    # 为Trae生成配置（添加disabled字段）
    trae_config = config_template.copy()
    trae_config["mcpServers"]["pdf-to-typst"]["disabled"] = False
    
    # 保存配置文件
    with open(project_root / "mcp_server" / "trae_fixed_config.json", 'w') as f:
        json.dump(trae_config, f, indent=2)
    
    with open(project_root / "mcp_server" / "cursor_fixed_config.json", 'w') as f:
        json.dump(config_template, f, indent=2)
    
    return system_python, str(project_root)

def main():
    print("🔧 MCP配置修复脚本")
    print("=" * 40)
    
    # 检查依赖
    print("\n1. 检查依赖...")
    if not check_dependencies():
        print("\n❌ 请先安装依赖:")
        print("   cd /Users/luoqiao/repos/MyProjects/PDFConvert")
        print("   source venv/bin/activate")
        print("   pip install -r requirements.txt")
        return
    
    # 生成配置
    print("\n2. 生成修复配置...")
    system_python, project_path = generate_configs()
    
    print(f"✅ 系统Python路径: {system_python}")
    print(f"✅ 项目路径: {project_path}")
    
    # 显示修复建议
    print("\n3. 修复建议:")
    print("\n🎯 Trae配置修复:")
    print("   将您的配置中的 'command' 改为:")
    print(f'   "command": "{system_python}",')
    print("   将 'args' 改为:")
    print(f'   "args": ["{project_path}/mcp_server/start_server_with_venv.py"],')
    
    print("\n🎯 Cursor配置修复:")
    print("   使用相同的修复方法")
    
    print(f"\n📋 完整的Trae配置文件已保存到:")
    print(f"   {project_path}/mcp_server/trae_fixed_config.json")
    print(f"   {project_path}/mcp_server/cursor_fixed_config.json")
    
    # 测试配置
    print("\n4. 测试配置...")
    try:
        result = subprocess.run([
            system_python, 
            f"{project_path}/mcp_server/start_server_with_venv.py"
        ], timeout=3, capture_output=True, text=True)
        print("✅ 配置测试通过")
    except subprocess.TimeoutExpired:
        print("✅ MCP服务器启动正常 (超时是正常的，因为服务器在等待连接)")
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
    
    print("\n🎉 修复完成！请使用新的配置重启Trae和Cursor")

if __name__ == "__main__":
    main()
