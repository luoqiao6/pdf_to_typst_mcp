# 开发文件目录

这个目录包含了项目开发过程中的测试文件、调试脚本、报告文档和其他辅助文件。

## 目录内容

### 测试相关
- `tests/` - 单元测试文件
- `test_*.py` - 各种测试脚本
- `pytest.ini` - pytest配置文件
- `api_test.http` - HTTP API测试文件

**注意**: `test_files/` 目录（包含测试用的PDF和图片文件）已移动到项目根目录，便于直接访问。

### 开发工具和脚本
- `demo_without_pymupdf.py` - 不使用PyMuPDF的演示脚本
- `generate_fixed_typst.py` - 生成修复Typst文件的脚本
- `verify_installation.py` - 安装验证脚本
- `start_http_api.sh` - HTTP API启动脚本
- `install_for_vscode.sh` - VS Code安装脚本

### 开发文档和报告
- `*_REPORT.md` - 各种测试和修复报告
- `*_SUMMARY.md` - 开发总结文档
- `COMPLEX_LAYOUT_ANALYSIS.md` - 复杂布局分析文档
- `INSTALLATION_*.md` - 安装相关文档
- `VSCODE_*.md` - VS Code集成相关文档
- `mcp_develop_docs/` - MCP开发文档

### API测试
- `api_test.http` - HTTP API测试文件

## 说明

这些文件主要用于：
1. 项目开发和调试
2. 功能测试和验证
3. 问题分析和报告
4. 开发过程记录

正式发布时这些文件通常不会包含在内，但对于开发和维护很重要。
