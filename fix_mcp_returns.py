#!/usr/bin/env python3
"""
修复MCP工具方法的返回格式
"""

import re

def fix_mcp_returns():
    server_file = "/Users/luoqiao/repos/MyProjects/PDFConvert/mcp_server/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复所有工具方法的返回类型注解
    content = re.sub(
        r'async def (_\w+)\(self, args: Dict\[str, Any\]\) -> CallToolResult:',
        r'async def \1(self, args: Dict[str, Any]):',
        content
    )
    
    # 修复错误处理中的CallToolResult
    content = re.sub(
        r'return CallToolResult\(\s*content=\[([^]]+)\],\s*isError=True\s*\)',
        r'raise Exception(\1.text if hasattr(\1, "text") else str(\1))',
        content
    )
    
    # 修复普通返回中的CallToolResult
    # 这个需要更仔细的处理，因为结构比较复杂
    
    # 先处理简单的单行情况
    content = re.sub(
        r'return CallToolResult\(\s*content=\[([^]]+)\]\s*\)',
        r'return [\1]',
        content
    )
    
    # 处理多行情况 - 这个比较复杂，我们手动处理几个关键的
    replacements = [
        # 错误处理
        (
            'return CallToolResult(\n                    content=[TextContent(\n                        type="text",\n                        text=f"❌ 操作失败: {str(e)}"\n                    )],\n                    isError=True\n                )',
            'raise Exception(f"❌ 操作失败: {str(e)}")'
        ),
        # 分析失败
        (
            'return CallToolResult(\n                    content=[TextContent(type="text", text=f"❌ 分析失败: {doc_info[\'error\']}")],\n                    isError=True\n                )',
            'raise Exception(f"❌ 分析失败: {doc_info[\'error\']}")'
        ),
        # 预览失败
        (
            'return CallToolResult(\n                    content=[TextContent(type="text", text=f"❌ 预览失败: {preview_result[\'error\']}")],\n                    isError=True\n                )',
            'raise Exception(f"❌ 预览失败: {preview_result[\'error\']}")'
        ),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ MCP返回格式修复完成")

if __name__ == "__main__":
    fix_mcp_returns()
