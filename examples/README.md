# 使用示例

这个目录包含了PDF转Typst工具的使用示例。

## 文件说明

- `simple_convert.py` - 交互式示例脚本，演示基本功能
- `config_example.json` - 配置文件示例
- `README.md` - 本文件

## 运行示例

### 1. 准备环境

确保已安装所有依赖：

```bash
cd /Users/luoqiao/repos/MyProjects/PDFConvert
pip install -r requirements.txt
```

### 2. 运行交互式示例

```bash
cd examples
python simple_convert.py
```

这将启动一个交互式菜单，你可以选择不同的示例：

1. **简单转换** - 转换单个PDF文件
2. **批量转换** - 转换整个目录的PDF文件
3. **文档信息** - 分析PDF文档信息

### 3. 命令行工具使用

#### 转换单个文件

```bash
# 基本转换
python src/main.py convert sample.pdf output.typ

# 带选项的转换
python src/main.py convert sample.pdf output.typ --no-images --overwrite

# 使用配置文件
python src/main.py convert sample.pdf output.typ --config examples/config_example.json
```

#### 批量转换

```bash
# 批量转换目录中的所有PDF文件
python src/main.py batch input_pdfs/ output_typst/

# 指定文件模式
python src/main.py batch input_pdfs/ output_typst/ --pattern "*.pdf"
```

#### 获取文档信息

```bash
# 分析PDF文档
python src/main.py info sample.pdf

# 预览转换结果
python src/main.py preview sample.pdf --pages 3
```

#### 生成配置模板

```bash
# 生成配置文件模板
python src/main.py config-template > config.json
```

## 文件结构示例

### 简单转换
```
examples/
├── sample.pdf          # 输入PDF文件
├── output.typ          # 输出Typst文件
└── output_images/      # 提取的图像目录
    ├── image_p1_1.png
    └── image_p1_2.jpg
```

### 批量转换
```
examples/
├── input_pdfs/         # 输入目录
│   ├── doc1.pdf
│   ├── doc2.pdf
│   └── doc3.pdf
└── output_typst/       # 输出目录
    ├── doc1.typ
    ├── doc1_images/
    ├── doc2.typ
    ├── doc2_images/
    ├── doc3.typ
    └── doc3_images/
```

## 配置选项

你可以创建一个JSON配置文件来自定义转换行为。参考 `config_example.json` 文件。

主要配置选项：

- **parser** - PDF解析器设置
  - `extract_images` - 是否提取图像
  - `extract_tables` - 是否提取表格
  - `max_file_size_mb` - 最大文件大小限制

- **analyzer** - 内容分析器设置
  - `heading_font_size_threshold` - 标题字体大小阈值
  - `paragraph_line_spacing_threshold` - 段落行间距阈值

- **generator** - Typst生成器设置
  - `paper_size` - 纸张大小
  - `font_family` - 默认字体
  - `include_toc` - 是否包含目录

## 常见问题

### Q: 转换失败怎么办？

A: 检查以下几点：
1. PDF文件是否损坏
2. 文件大小是否超过限制
3. 是否有足够的磁盘空间
4. 查看错误日志获取详细信息

### Q: 如何提高转换质量？

A: 可以调整配置参数：
1. 降低 `heading_font_size_threshold` 来识别更多标题
2. 调整 `table_settings` 来改善表格识别
3. 设置 `image_min_width` 和 `image_min_height` 过滤小图像

### Q: 支持哪些PDF格式？

A: 支持大多数标准PDF文档，特别是：
- 文本类PDF（非扫描版）
- 学术论文和报告
- 技术文档
- 书籍和手册

### Q: 生成的Typst文件如何编译？

A: 使用Typst编译器：

```bash
# 安装Typst
curl -fsSL https://typst.community/typst-install/install.sh | sh

# 编译为PDF
typst compile output.typ

# 监视模式（自动重编译）
typst watch output.typ
```

## 性能提示

1. **大文件处理**：对于大文件，建议分页处理或使用预览模式先测试
2. **批量转换**：使用批量模式比逐个转换更高效
3. **图像处理**：如果不需要图像，可以禁用图像提取来提高速度
4. **内存使用**：处理大文件时注意内存使用情况

## 更多帮助

- 查看 `--help` 选项获取详细命令行帮助
- 阅读项目文档了解更多技术细节
- 提交Issue报告问题或建议
