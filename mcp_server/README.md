# PDF转Typst MCP服务

🚀 **智能PDF转换服务**，利用Agent的AI大模型进行页面布局识别和Typst代码生成。

## ✨ 功能特性

- 📄 **智能PDF解析**: 提取文本、表格、图像等元素
- 🤖 **AI增强转换**: 利用Agent的多模态AI进行布局识别
- ⚡ **高质量代码生成**: 生成符合Typst语法的高质量代码
- 🔌 **多平台支持**: 与Claude Desktop、VSCode、Cursor、Trae等AI应用无缝集成
- 🎯 **交互式转换**: AI引导的分步转换流程

## 🛠️ 安装配置

### 1. 自动安装（推荐）

```bash
cd /Users/luoqiao/repos/MyProjects/PDFConvert
./mcp_server/install_mcp.sh
```

### 2. 手动安装

#### 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装MCP库
pip install mcp
```

#### 配置不同Agent平台

##### Claude Desktop

在Claude Desktop的配置文件中添加以下内容：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/Users/luoqiao/repos/MyProjects/PDFConvert/mcp_server/start_server.py"],
      "env": {
        "PYTHONPATH": "/Users/luoqiao/repos/MyProjects/PDFConvert"
      }
    }
  }
}
```

##### VSCode (使用MCP扩展)

1. 安装MCP扩展：`MCP Client for VSCode`
2. 在VSCode设置中添加：

```json
{
  "mcp.servers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/Users/luoqiao/repos/MyProjects/PDFConvert/mcp_server/start_server.py"],
      "env": {
        "PYTHONPATH": "/Users/luoqiao/repos/MyProjects/PDFConvert"
      }
    }
  }
}
```

##### Cursor

1. 在Cursor设置中配置MCP服务器：

```json
{
  "mcpServers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/Users/luoqiao/repos/MyProjects/PDFConvert/mcp_server/start_server.py"],
      "env": {
        "PYTHONPATH": "/Users/luoqiao/repos/MyProjects/PDFConvert"
      }
    }
  }
}
```

##### Trae

Trae通常支持标准MCP协议，配置类似：

```json
{
  "mcp_servers": {
    "pdf-to-typst": {
      "command": "python",
      "args": ["/Users/luoqiao/repos/MyProjects/PDFConvert/mcp_server/start_server.py"],
      "env": {
        "PYTHONPATH": "/Users/luoqiao/repos/MyProjects/PDFConvert"
      }
    }
  }
}
```

## ⚠️ 重要：多模态大模型要求

### 🤖 支持的多模态大模型

此MCP服务**必须使用支持图片识别的多模态大模型**才能正常工作，因为需要AI分析PDF页面图像来识别布局。

#### ✅ 推荐的多模态大模型

**Claude系列**:
- Claude 3.5 Sonnet (推荐)
- Claude 3 Opus
- Claude 3 Haiku

**OpenAI系列**:
- GPT-4V (GPT-4 Vision)
- GPT-4o
- GPT-4o mini

**Google系列**:
- Gemini Pro Vision
- Gemini Ultra

**其他支持的模型**:
- Qwen-VL系列
- LLaVA系列
- InternVL系列

#### ❌ 不支持的模型

以下模型**无法**使用此MCP服务：
- GPT-3.5 (不支持图片)
- Claude Instant (不支持图片)
- 纯文本大模型

### 🔧 如何确保使用正确的模型

#### 在不同Agent中切换到多模态模型

##### Claude Desktop
- Claude Desktop默认使用Claude 3.5 Sonnet，天然支持多模态 ✅

##### VSCode
```
1. 打开VSCode设置
2. 搜索 "AI Model" 或 "Language Model"
3. 选择支持视觉的模型，如：
   - GPT-4V
   - Claude 3.5 Sonnet
   - Gemini Pro Vision
```

##### Cursor
```
1. 按 Ctrl+Shift+P (或 Cmd+Shift+P)
2. 搜索 "Select Model"
3. 选择支持图片的模型：
   - GPT-4o
   - Claude 3.5 Sonnet
   - Gemini Pro Vision
```

##### Trae
```
1. 在设置中找到模型选择
2. 确保选择的是多模态模型
3. 常见选项：GPT-4V, Claude 3.5, Gemini Pro Vision
```

### 🧪 测试多模态功能

在使用MCP服务前，可以先测试Agent的多模态能力：

```
用户: 请描述这张图片的内容 [上传一张图片]

如果AI能正确描述图片内容，说明当前模型支持多模态 ✅
如果AI提示无法处理图片，需要切换模型 ❌
```

### 🚨 常见问题解决

**问题1**: "无法分析PDF布局"
- **原因**: 当前使用的是纯文本模型
- **解决**: 切换到支持图片的多模态模型

**问题2**: "MCP服务返回空白内容"
- **原因**: 模型无法处理页面图像资源
- **解决**: 确认使用的是多模态大模型

**问题3**: "布局识别不准确"
- **原因**: 模型的视觉能力较弱
- **解决**: 切换到更强的多模态模型（如Claude 3.5 Sonnet或GPT-4V）

## 🎮 使用方法

### 在不同Agent中使用

此MCP服务在所有支持MCP协议的Agent中使用方法基本相同：

#### 基本使用流程

1. **确保使用多模态大模型** (如Claude 3.5 Sonnet, GPT-4V等)
2. **重启Agent应用** (加载MCP服务配置)
3. **直接与AI对话**：

```
用户: 请帮我将这个PDF转换为Typst格式：/path/to/document.pdf

AI会自动：
1. 调用MCP服务分析PDF结构
2. 提取页面图像和文本数据
3. 使用多模态AI进行布局识别
4. 生成高质量的Typst代码
5. 输出转换后的文件
```

#### 各Agent平台特定说明

##### Claude Desktop
- 默认支持多模态，无需额外配置
- 重启应用后即可使用

##### VSCode
- 需要安装MCP扩展
- 确保选择支持视觉的AI模型
- 通过命令面板或聊天界面使用

##### Cursor
- 内置MCP支持
- 使用Ctrl+L打开AI聊天
- 确保选择多模态模型 (GPT-4o/Claude 3.5)

##### Trae
- 支持标准MCP协议
- 在AI聊天中直接使用
- 确保配置了多模态模型

### 主要工具功能

#### 0. 🔍 首次使用：检测多模态能力
```
请检测当前AI模型是否支持图片识别
```

#### 1. 📊 快速分析PDF结构
```
请分析这个PDF的结构：/path/to/document.pdf
```

#### 2. 🔍 预览转换效果
```
请预览这个PDF转换为Typst的效果：/path/to/document.pdf
```

#### 3. 🚀 完整转换流程
```
请将这个PDF转换为Typst格式：/path/to/document.pdf
```

### 🎯 完整使用示例

#### 在Claude Desktop中的完整对话流程：

```
用户: 请检测当前AI模型是否支持图片识别

Claude: [调用check_multimodal_capability工具，显示测试图片]
我可以看到这是一个1x1像素的透明PNG图片。这说明当前模型支持多模态能力 ✅

用户: 很好！请将这个PDF转换为Typst格式：/Users/xxx/document.pdf

Claude: [调用start_pdf_conversion工具]
已开始转换流程，正在分析PDF结构...
[调用相关资源和提示模板进行AI分析]
[调用finalize_conversion完成转换]
转换完成！生成的文件保存在：/Users/xxx/document.typ
```

#### 在Cursor中的使用：

```
1. 确保选择了多模态模型（如GPT-4o或Claude 3.5）
2. 按Ctrl+L打开AI聊天
3. 输入：请检测AI模型多模态能力
4. 确认支持后：请转换PDF文件 /path/to/file.pdf
```

## 🔧 高级功能

### AI增强的转换流程

1. **启动转换会话**
   - PDF解析和页面提取
   - 生成转换会话ID

2. **AI布局分析**
   - 访问页面图像资源
   - 使用AI提示模板分析布局
   - 识别文档结构和元素

3. **智能代码生成**
   - 基于布局分析生成Typst代码
   - AI优化代码质量
   - 确保语法正确性

4. **完成转换**
   - 整合所有页面代码
   - 输出最终Typst文件
   - 保存相关图像资源

### 可用的AI提示模板

- **`analyze_pdf_layout`**: 页面布局分析专家提示
- **`generate_typst_code`**: Typst代码生成专家提示  
- **`optimize_typst_output`**: 代码优化专家提示

## 📋 工具列表

| 工具名称 | 功能描述 |
|---------|---------|
| `check_multimodal_capability` | 🔍 检测AI模型多模态能力（必须先检测） |
| `start_pdf_conversion` | 开始PDF转换流程，提取页面内容 |
| `analyze_pdf_structure` | 快速分析PDF文档结构 |
| `preview_typst_output` | 预览转换后的Typst代码 |
| `finalize_conversion` | 完成转换并输出文件 |
| `list_active_sessions` | 列出当前活跃的转换会话 |

## 📚 资源类型

### 页面资源
- **图像资源**: `pdf-page://session_id/page-N/image` - 高分辨率页面图片
- **文本资源**: `pdf-page://session_id/page-N/text` - 结构化文本数据

### 文档资源  
- **元数据资源**: `pdf-doc://session_id/metadata` - 文档信息和统计

## 🧪 测试验证

### 手动测试服务

```bash
# 启动MCP服务器（测试模式）
python mcp_server/start_server.py

# 服务器将在stdio模式下运行，等待MCP客户端连接
```

### 使用测试PDF

项目包含多个测试PDF文件：

```bash
# 测试简单文档
/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_2.pdf

# 测试复杂文档
/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_5.pdf
```

## 🔍 故障排除

### 常见问题

1. **MCP服务无法启动**
   ```bash
   # 检查依赖
   pip list | grep mcp
   
   # 检查Python路径
   python -c "import sys; print(sys.path)"
   ```

2. **Claude Desktop无法识别服务**
   - 确认配置文件路径正确
   - 重启Claude Desktop应用
   - 检查日志文件

3. **PDF解析失败**
   - 确认PDF文件路径正确
   - 检查文件权限
   - 验证PDF文件完整性

### 日志查看

服务器日志会输出到stderr，可以通过以下方式查看：

```bash
# 直接运行查看日志
python mcp_server/start_server.py 2>&1 | tee mcp_server.log
```

## 🚀 性能优化

### 推荐配置

- **内存**: 至少4GB可用内存
- **存储**: 足够的临时文件空间
- **网络**: 如使用云端AI服务，需稳定网络连接

### 优化建议

1. **大文件处理**: 对于大型PDF，考虑分批处理
2. **会话管理**: 定期清理过期的转换会话
3. **缓存策略**: 重复转换时利用缓存加速

## 📈 更新日志

### v1.0.0 (2024-12-19)
- ✨ 初始版本发布
- 🤖 集成AI增强的布局识别
- 🔌 完整的MCP协议支持
- 📚 丰富的提示模板库

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

---

🎉 **开始使用吧！** 享受AI增强的PDF转Typst转换体验。
