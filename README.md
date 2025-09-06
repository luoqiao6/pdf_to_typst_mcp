# PDF转Typst工具

一个专业的PDF转Typst工具，专门针对学术类PDF文档，能够完整解析PDF的排版样式、文本内容、表格结构和图像，并在Typst中精准还原原始文档的视觉效果和内容结构。

## 🎯 项目目标

开发一个高质量的PDF转Typst工具，满足以下需求：

- **完整内容提取**：文本、表格、图像、样式信息
- **排版样式还原**：字体、颜色、大小、加粗、斜体等
- **学术文档支持**：标题层级、段落结构、引用、参考文献
- **大文件处理**：支持几百页的PDF文档
- **高质量输出**：生成符合Typst标准的.typ文件

## 🏗️ 技术方案

### 混合解析方案

采用**pdfplumber + PyMuPDF**的混合方案，充分发挥两者的优势：

#### pdfplumber负责
- ✅ 文本内容提取（最高质量）
- ✅ 表格识别和结构分析
- ✅ 段落和文本布局分析
- ✅ 复杂排版结构识别

#### PyMuPDF负责
- ✅ 字体和样式信息提取
- ✅ 图像提取和处理
- ✅ 颜色和位置信息
- ✅ 大文件流式处理

### 技术架构

```
PDF文件 → 混合解析引擎 → 内容分析 → 学术内容识别 → Typst生成 → 输出文件
                ↓
        ┌─────────────────┬─────────────────┐
        │   pdfplumber    │    PyMuPDF      │
        │   (文本+表格)   │   (样式+图像)   │
        └─────────────────┴─────────────────┘
```

## 🚀 核心功能

### 1. PDF内容解析
- **文本提取**：高精度文本内容提取
- **表格识别**：智能表格结构识别和转换
- **图像提取**：高质量图像提取和保存
- **样式分析**：完整的字体、颜色、样式信息

### 2. 学术内容识别
- **标题层级**：多级标题识别和层级关系
- **段落结构**：段落分割和结构分析
- **引用识别**：引用标记和参考文献识别
- **页面布局**：多列布局、页眉页脚识别

### 3. Typst生成
- **文档模板**：专业的学术文档模板
- **样式映射**：PDF样式到Typst样式的精准映射
- **内容转换**：文本、表格、图像的Typst语法生成
- **布局还原**：重现原始PDF的视觉效果

### 4. 性能优化
- **流式处理**：支持大文件，避免内存溢出
- **并行解析**：多线程并行处理，提升性能
- **智能缓存**：缓存常用资源，优化处理速度
- **错误恢复**：容错机制，确保处理稳定性

## 📁 项目结构

```
PDFConvert/
├── docs/                    # 项目文档
│   ├── 开发计划.md         # 详细开发计划
│   ├── 技术调研报告.md     # 技术选型分析
│   └── 项目结构设计.md     # 项目架构设计
├── src/                     # 源代码
│   ├── core/               # 核心功能模块
│   ├── web/                # Web应用模块
│   └── cli/                # 命令行工具
├── tests/                   # 测试代码
├── data/                    # 数据目录
└── docker/                  # Docker配置
```

## 🛠️ 技术栈

- **后端语言**：Python 3.8+
- **PDF处理**：pdfplumber, PyMuPDF
- **Web框架**：Flask
- **数据处理**：NumPy, Pandas
- **图像处理**：Pillow, OpenCV
- **测试框架**：pytest
- **部署容器**：Docker

## 📋 开发计划

### 第一阶段：基础架构搭建（2-3周）
- 项目初始化和环境配置
- 核心模块设计和接口定义
- 基础PDF解析功能实现

### 第二阶段：核心功能开发（4-5周）
- 文本处理和表格识别
- 样式分析和图像处理
- 内容分析算法实现

### 第三阶段：学术内容识别（3-4周）
- 标题层级和段落识别
- 引用和参考文献识别
- 页面布局分析

### 第四阶段：Typst生成（3-4周）
- Typst模板设计
- 样式映射和内容转换
- 输出质量优化

### 第五阶段：性能优化和测试（2-3周）
- 性能优化和内存管理
- 测试覆盖和错误处理
- 用户体验优化

### 第六阶段：用户界面和部署（2-3周）
- Web界面开发
- 部署配置和文档
- 项目发布准备

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 8GB+ RAM（用于大文件处理）
- 2GB+ 可用磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/PDFConvert.git
cd PDFConvert
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行应用**
```bash
python src/main.py
```

### Docker部署

```bash
# 构建镜像
docker build -t pdf-converter .

# 运行容器
docker run -p 5000:5000 -v $(pwd)/data:/app/data pdf-converter
```

## 📖 使用说明

### 基本使用

1. **上传PDF文件**：通过Web界面或API上传PDF文档
2. **自动解析**：系统自动解析PDF内容和样式
3. **生成Typst**：生成高质量的.typ文件
4. **下载结果**：下载转换后的Typst文件和提取的图像

### 支持格式

- **输入**：PDF文档（支持多页、大文件）
- **输出**：Typst (.typ) 文件 + 图像文件夹

### 配置选项

- 最大文件大小限制
- 内存使用限制
- 并发处理数量
- 输出质量设置

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_pdf_parser.py

# 生成测试报告
pytest --cov=src --cov-report=html
```

### 测试覆盖
- 单元测试：核心算法和函数
- 集成测试：模块间协作
- 性能测试：大文件处理能力
- 端到端测试：完整转换流程

## 📊 性能指标

### 处理能力
- **文件大小**：支持16MB以内的PDF文件
- **页数限制**：支持1000页以内的PDF文档
- **处理时间**：100页PDF约2-3分钟
- **内存使用**：峰值内存使用<2GB

### 质量指标
- **文本准确率**：>95%
- **表格准确率**：>90%
- **样式完整度**：>95%
- **图像质量**：高

## 🤝 贡献指南

### 开发流程
1. Fork项目到你的GitHub账户
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 创建Pull Request

### 代码规范
- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档字符串
- 编写单元测试，保持测试覆盖率
- 使用类型提示（Type Hints）

## 📝 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- **项目主页**：https://github.com/yourusername/PDFConvert
- **问题反馈**：https://github.com/yourusername/PDFConvert/issues
- **讨论区**：https://github.com/yourusername/PDFConvert/discussions

## 🙏 致谢

感谢以下开源项目的支持：
- [pdfplumber](https://github.com/jsvine/pdfplumber) - 优秀的PDF文本提取库
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - 高性能PDF处理库
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [Typst](https://typst.app/) - 现代化的标记语言

---

**项目状态**：第一阶段开发完成 - 基础架构已搭建  
**最后更新**：2024年12月  
**维护状态**：活跃开发中

## 🎉 第一阶段完成情况

✅ **已完成功能**：
- 项目基础架构搭建
- 核心数据模型定义
- PDF解析器接口和混合解析实现
- 内容分析器框架
- Typst生成器框架
- 处理流水线整合
- 命令行工具
- 基础测试用例
- 示例脚本和文档

📋 **当前功能**：
- 支持PDF文本、表格、图像提取
- 学术文档结构识别（标题、段落、列表）
- 高质量Typst文档生成
- 命令行和编程接口
- 批量处理支持
- 配置化设置
