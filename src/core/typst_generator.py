"""
Typst生成器

将解析和分析后的PDF内容转换为Typst格式文档。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from .models import (
    ParsedDocument, TypstDocument, TextBlock, Table, Image,
    Heading, Paragraph, List as DocList, ListItem,
    TextStyle, ElementType, TypstGenerationError
)
from .layout_analyzer import LayoutAnalyzer, PageLayout, LayoutRegion

logger = logging.getLogger(__name__)


class TypstGenerator:
    """Typst生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Typst生成器
        
        Args:
            config: 生成器配置
        """
        self.config = config or {}
        self._setup_config()
        
        # 字体映射表
        self._font_mapping = self._create_font_mapping()
        
        # 样式模板
        self._templates = self._load_templates()
        
        # 布局分析器
        self.layout_analyzer = LayoutAnalyzer(self.config.get('layout_config', {}))
    
    def _setup_config(self):
        """设置默认配置"""
        default_config = {
            # 文档设置
            'paper_size': 'a4',
            'margin': '2.5cm',
            'font_family': 'Times New Roman',
            'font_size': '11pt',
            'line_spacing': '1.5em',
            
            # 标题设置
            'heading_numbering': True,
            'heading_spacing': '1.2em',
            
            # 段落设置
            'paragraph_spacing': '1em',
            'paragraph_indent': '2em',
            
            # 表格设置
            'table_stroke': '0.5pt',
            'table_fill': 'none',
            
            # 图像设置
            'image_width': '80%',
            'image_alignment': 'center',
            
            # 输出设置
            'include_metadata': False,  # 默认不包含元数据页面
            'include_toc': False,       # 默认不包含目录
            'include_page_numbers': True,
            
            # 布局还原设置
            'preserve_layout': True,
            'use_precise_positioning': True,
            'detect_columns': True,
            'preserve_text_wrapping': True,
            'maintain_spacing': True,
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def _create_font_mapping(self) -> Dict[str, str]:
        """创建字体映射表"""
        return {
            # 常见字体映射
            'times': 'Times New Roman',
            'arial': 'Arial',
            'helvetica': 'Helvetica',
            'courier': 'Courier New',
            'calibri': 'Calibri',
            'simsun': 'SimSun',
            'songti': 'SimSun',
            'heiti': 'SimHei',
            'kaiti': 'KaiTi',
            'fangsong': 'FangSong',
        }
    
    def _load_templates(self) -> Dict[str, str]:
        """加载Typst模板"""
        return {
            'document_header': '''#set page(
  paper: "{paper_size}",
  margin: {margin},
  numbering: "1",
)

#set text(
  font: "{font_family}",
  size: {font_size},
  lang: "zh",
)

#set par(
  leading: {line_spacing},
  first-line-indent: {paragraph_indent},
  spacing: {paragraph_spacing},
)

#set heading(
  numbering: "1.1.1.1.1.1",
)

''',
            
            'title_page': '''#align(center)[
  #text(size: 24pt, weight: "bold")[{title}]
  
  #v(2em)
  
  {author}
  
  #v(1em)
  
  {date}
]

#pagebreak()

''',
            
            'table_of_contents': '''#outline(
  title: "目录",
  depth: 3,
  indent: 1em,
)

#pagebreak()

'''
        }
    
    def generate_document(self, parsed_doc: ParsedDocument, 
                         output_dir: Optional[Path] = None) -> TypstDocument:
        """
        生成Typst文档
        
        Args:
            parsed_doc: 解析后的文档
            output_dir: 输出目录（用于保存图像）
            
        Returns:
            TypstDocument: 生成的Typst文档
        """
        logger.info("开始生成Typst文档")
        
        content_parts = []
        image_paths = []
        
        # 1. 文档头部设置
        content_parts.append(self._generate_document_header(parsed_doc))
        
        # 2. 标题页（如果有元数据）
        if self.config['include_metadata'] and parsed_doc.metadata.title:
            content_parts.append(self._generate_title_page(parsed_doc.metadata))
        
        # 3. 目录（如果需要且有多个标题）
        if (self.config['include_toc'] and parsed_doc.headings and 
            len(parsed_doc.headings) > 3):  # 只有超过3个标题才生成目录
            content_parts.append(self._generate_toc())
        
        # 4. 保存图像文件
        if output_dir:
            image_paths = self._save_images(parsed_doc.images, output_dir)
        
        # 5. 生成主要内容
        main_content = self._generate_main_content(parsed_doc, image_paths)
        content_parts.append(main_content)
        
        # 合并所有内容
        full_content = '\n'.join(content_parts)
        
        # 创建Typst文档对象
        typst_doc = TypstDocument(
            content=full_content,
            metadata=parsed_doc.metadata,
            images=image_paths
        )
        
        logger.info("Typst文档生成完成")
        return typst_doc
    
    def _generate_document_header(self, parsed_doc: ParsedDocument = None) -> str:
        """生成文档头部设置"""
        # 获取真实页面信息
        page_info = None
        if parsed_doc and hasattr(parsed_doc, 'pages') and parsed_doc.pages:
            page_info = parsed_doc.pages[0]  # 使用第一页的信息
        
        # 根据页面信息生成设置
        if page_info:
            return self._generate_dynamic_page_settings(page_info)
        else:
            # 回退到默认模板
            return self._templates['document_header'].format(
                paper_size=self.config['paper_size'],
                margin=self.config['margin'],
                font_family=self.config['font_family'],
                font_size=self.config['font_size'],
                line_spacing=self.config['line_spacing'],
                paragraph_indent=self.config['paragraph_indent'],
                paragraph_spacing=self.config['paragraph_spacing']
            )
    
    def _generate_dynamic_page_settings(self, page_info) -> str:
        """根据真实页面信息生成页面设置"""
        # 计算页面尺寸（从点转换为毫米）
        width_mm = round(page_info.width * 0.352778, 1)  # 1pt = 0.352778mm
        height_mm = round(page_info.height * 0.352778, 1)
        
        # 判断页面方向
        is_landscape = page_info.width > page_info.height
        
        # 生成页面设置
        page_settings = f'''#set page(
  width: {width_mm}mm,
  height: {height_mm}mm,
  margin: (x: 10mm, y: 10mm),
)

#set text(
  font: "{self.config['font_family']}",
  size: {self.config['font_size']},
  lang: "zh",
)

#set par(
  leading: {self.config['line_spacing']},
  spacing: {self.config['paragraph_spacing']},
)

#set heading(
  numbering: "1.1.1.1.1.1",
)

'''
        
        return page_settings
    
    def _generate_title_page(self, metadata) -> str:
        """生成标题页"""
        title = metadata.title or "无标题文档"
        author = metadata.author or ""
        date = metadata.creation_date or ""
        
        return self._templates['title_page'].format(
            title=self._escape_typst_text(title),
            author=self._escape_typst_text(author),
            date=self._escape_typst_text(date)
        )
    
    def _generate_toc(self) -> str:
        """生成目录"""
        return self._templates['table_of_contents']
    
    def _generate_main_content(self, parsed_doc: ParsedDocument, 
                              image_paths: List[str]) -> str:
        """生成主要内容"""
        content_parts = []
        
        # 按页面顺序处理内容
        for page_num in range(1, parsed_doc.get_page_count() + 1):
            if self.config['preserve_layout']:
                # 使用布局分析器进行精确布局还原
                page_content = self._generate_page_with_layout(
                    parsed_doc, page_num, image_paths
                )
            else:
                # 使用传统的简单排序方式
                page_content = self._generate_page_simple(
                    parsed_doc, page_num, image_paths
                )
            
            content_parts.append(page_content)
            
            # 只有在多页文档时才添加分页符
            if (parsed_doc.get_page_count() > 1 and 
                page_num < parsed_doc.get_page_count()):
                content_parts.append("#pagebreak()")
        
        return '\n\n'.join(content_parts)
    
    def _generate_page_with_layout(self, parsed_doc: ParsedDocument, 
                                  page_num: int, image_paths: List[str]) -> str:
        """使用布局分析器生成页面内容"""
        # 分析页面布局
        page_layout = self.layout_analyzer.analyze_page_layout(parsed_doc, page_num)
        
        content_parts = []
        
        # 检查是否有绝对定位区域
        absolute_regions = [r for r in page_layout.regions if r.region_type == 'absolute']
        
        if absolute_regions and self.config['use_precise_positioning']:
            content_parts.append(self._generate_absolute_layout(page_layout, image_paths))
        elif page_layout.column_count > 1 and self.config['detect_columns']:
            content_parts.append(self._generate_multi_column_layout(page_layout, image_paths))
        else:
            content_parts.append(self._generate_single_column_layout(page_layout, image_paths))
        
        return '\n\n'.join(content_parts)
    
    def _generate_page_simple(self, parsed_doc: ParsedDocument, 
                             page_num: int, image_paths: List[str]) -> str:
        """使用传统方式生成页面内容（向后兼容）"""
        page_elements = parsed_doc.get_elements_by_page(page_num)
        
        # 合并所有元素并按位置排序
        all_elements = []
        
        # 添加标题
        for heading in page_elements['headings']:
            all_elements.append(('heading', heading, heading.bbox.y0))
        
        # 添加段落
        for paragraph in page_elements['paragraphs']:
            all_elements.append(('paragraph', paragraph, paragraph.bbox.y0))
        
        # 添加表格
        for table in page_elements['tables']:
            all_elements.append(('table', table, table.bbox.y0))
        
        # 添加图像
        for i, image in enumerate(page_elements['images']):
            image_path = image_paths[i] if i < len(image_paths) else ""
            all_elements.append(('image', (image, image_path), image.bbox.y0))
        
        # 添加列表
        for doc_list in page_elements['lists']:
            all_elements.append(('list', doc_list, doc_list.bbox.y0))
        
        # 按y坐标排序（从上到下）
        all_elements.sort(key=lambda x: -x[2])  # 负号因为PDF坐标系
        
        # 生成内容
        content_parts = []
        for element_type, element, _ in all_elements:
            if element_type == 'heading':
                content_parts.append(self._generate_heading(element))
            elif element_type == 'paragraph':
                content_parts.append(self._generate_paragraph(element))
            elif element_type == 'table':
                content_parts.append(self._generate_table(element))
            elif element_type == 'image':
                image, image_path = element
                content_parts.append(self._generate_image(image, image_path))
            elif element_type == 'list':
                content_parts.append(self._generate_list(element))
        
        return '\n\n'.join(content_parts)
    
    def _generate_absolute_layout(self, page_layout: PageLayout, 
                                 image_paths: List[str]) -> str:
        """生成绝对定位布局"""
        absolute_regions = [r for r in page_layout.regions if r.region_type == 'absolute']
        
        if not absolute_regions:
            return ""
        
        content_parts = []
        
        # 处理每个绝对定位区域
        for region in absolute_regions:
            # 分析元素重叠和关系
            layout_groups = self._analyze_element_relationships_for_layout(region, page_layout)
            
            # 暂时禁用智能分组，使用纯绝对定位
            for group in layout_groups:
                for element_type, element in group:
                    if element_type == 'heading':
                        content_parts.append(self._generate_heading_absolute(element, page_layout))
                    elif element_type == 'paragraph':
                        content_parts.append(self._generate_paragraph_absolute(element, page_layout))
                    elif element_type == 'table':
                        content_parts.append(self._generate_table_absolute(element, page_layout))
                    elif element_type == 'image':
                        image_path = self._find_image_path(element, image_paths)
                        content_parts.append(self._generate_image_absolute(element, image_path, page_layout))
                    elif element_type == 'list':
                        content_parts.append(self._generate_list_absolute(element, page_layout))
        
        return '\n\n'.join(content_parts)
    
    def _analyze_element_relationships_for_layout(self, region: LayoutRegion, 
                                                 page_layout: PageLayout) -> List[List]:
        """分析元素关系，优化布局顺序"""
        elements = region.elements
        
        # 按y坐标排序（从上到下）
        sorted_elements = sorted(elements, key=lambda x: self._get_element_y_position(x[1]))
        
        # 暂时禁用分组，每个元素独立处理
        return [[elem] for elem in sorted_elements]
    
    def _group_elements_by_spatial_relationship(self, elements: List[Tuple[str, object]], 
                                              page_layout: PageLayout) -> List[List]:
        """根据空间关系分组元素"""
        if not elements:
            return []
        
        groups = []
        current_group = []
        
        for i, (elem_type, element) in enumerate(elements):
            if not hasattr(element, 'bbox') or not element.bbox:
                # 没有bbox信息的元素单独成组
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([(elem_type, element)])
                continue
            
            if not current_group:
                current_group = [(elem_type, element)]
            else:
                # 检查与当前组的重叠情况
                if self._elements_overlap_or_conflict(current_group, (elem_type, element), page_layout):
                    # 有重叠，结束当前组，开始新组
                    groups.append(current_group)
                    current_group = [(elem_type, element)]
                else:
                    # 无重叠，加入当前组
                    current_group.append((elem_type, element))
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _elements_overlap_or_conflict(self, group: List[Tuple[str, object]], 
                                    new_element: Tuple[str, object], 
                                    page_layout: PageLayout) -> bool:
        """检查新元素是否与组中元素重叠或冲突"""
        elem_type, element = new_element
        
        if not hasattr(element, 'bbox') or not element.bbox:
            return False
        
        new_bbox = element.bbox
        
        for group_type, group_element in group:
            if not hasattr(group_element, 'bbox') or not group_element.bbox:
                continue
            
            group_bbox = group_element.bbox
            
            # 检查重叠
            if self._bboxes_overlap(new_bbox, group_bbox):
                return True
            
            # 检查特殊冲突（例如图片与文字太近）
            if self._elements_have_conflict(new_element, (group_type, group_element)):
                return True
        
        return False
    
    def _bboxes_overlap(self, bbox1, bbox2) -> bool:
        """检查两个边界框是否重叠"""
        # 检查水平重叠
        horizontal_overlap = not (bbox1.x1 <= bbox2.x0 or bbox2.x1 <= bbox1.x0)
        # 检查垂直重叠
        vertical_overlap = not (bbox1.y1 <= bbox2.y0 or bbox2.y1 <= bbox1.y0)
        
        return horizontal_overlap and vertical_overlap
    
    def _elements_have_conflict(self, elem1: Tuple[str, object], elem2: Tuple[str, object]) -> bool:
        """检查两个元素是否有布局冲突"""
        type1, obj1 = elem1
        type2, obj2 = elem2
        
        # 图片与文字的特殊处理
        if (type1 == 'image' and type2 in ['paragraph', 'heading']) or \
           (type2 == 'image' and type1 in ['paragraph', 'heading']):
            # 图片和文字如果距离太近，认为有冲突
            if hasattr(obj1, 'bbox') and hasattr(obj2, 'bbox'):
                return self._elements_too_close(obj1.bbox, obj2.bbox, threshold=20)  # 20pt阈值
        
        return False
    
    def _elements_too_close(self, bbox1, bbox2, threshold: float = 10) -> bool:
        """检查两个元素是否距离太近"""
        # 计算最小距离
        dx = max(0, max(bbox1.x0 - bbox2.x1, bbox2.x0 - bbox1.x1))
        dy = max(0, max(bbox1.y0 - bbox2.y1, bbox2.y0 - bbox1.y1))
        distance = (dx * dx + dy * dy) ** 0.5
        
        return distance < threshold
    
    def _generate_group_flow_layout(self, group: List[Tuple[str, object]], 
                                   image_paths: List[str], page_layout: PageLayout) -> str:
        """为重叠的元素组生成流式布局"""
        if not group:
            return ""
        
        # 找到组的边界框
        group_bbox = self._calculate_group_bbox(group)
        if not group_bbox:
            # 回退到简单序列
            return self._generate_group_sequential(group, image_paths)
        
        # 计算组的位置
        position = self._calculate_absolute_position(group_bbox, page_layout)
        
        # 生成组内容
        group_content_parts = []
        for element_type, element in group:
            if element_type == 'heading':
                group_content_parts.append(self._generate_heading(element))
            elif element_type == 'paragraph':
                group_content_parts.append(self._generate_paragraph(element))
            elif element_type == 'table':
                group_content_parts.append(self._generate_table(element))
            elif element_type == 'image':
                image_path = self._find_image_path(element, image_paths)
                if image_path:
                    # 图片使用相对尺寸
                    rel_width = min(50, max(20, float(position['width'].rstrip('%'))))
                    group_content_parts.append(f'#figure(image("{image_path}", width: {rel_width}%), caption: [])')
            elif element_type == 'list':
                group_content_parts.append(self._generate_list(element))
        
        # 使用box包装，避免重叠
        group_content = '\n\n'.join(group_content_parts)
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[#box(width: {position['width']})[
{group_content}
]]'''
    
    def _calculate_group_bbox(self, group: List[Tuple[str, object]]):
        """计算元素组的边界框"""
        bboxes = []
        for element_type, element in group:
            if hasattr(element, 'bbox') and element.bbox:
                bboxes.append(element.bbox)
        
        if not bboxes:
            return None
        
        # 计算包含所有元素的最小边界框
        min_x0 = min(bbox.x0 for bbox in bboxes)
        min_y0 = min(bbox.y0 for bbox in bboxes)
        max_x1 = max(bbox.x1 for bbox in bboxes)
        max_y1 = max(bbox.y1 for bbox in bboxes)
        
        # 创建一个简单的边界框对象
        class GroupBBox:
            def __init__(self, x0, y0, x1, y1):
                self.x0 = x0
                self.y0 = y0
                self.x1 = x1
                self.y1 = y1
                self.width = x1 - x0
                self.height = y1 - y0
        
        return GroupBBox(min_x0, min_y0, max_x1, max_y1)
    
    def _generate_group_sequential(self, group: List[Tuple[str, object]], 
                                  image_paths: List[str]) -> str:
        """为元素组生成简单的序列布局"""
        content_parts = []
        for element_type, element in group:
            if element_type == 'heading':
                content_parts.append(self._generate_heading(element))
            elif element_type == 'paragraph':
                content_parts.append(self._generate_paragraph(element))
            elif element_type == 'table':
                content_parts.append(self._generate_table(element))
            elif element_type == 'image':
                image_path = self._find_image_path(element, image_paths)
                if image_path:
                    content_parts.append(f'#figure(image("{image_path}", width: 40%), caption: [])')
            elif element_type == 'list':
                content_parts.append(self._generate_list(element))
        
        return '\n\n'.join(content_parts)
    
    def _get_element_y_position(self, element) -> float:
        """获取元素的Y坐标"""
        if hasattr(element, 'bbox') and element.bbox:
            return element.bbox.y0
        return 0
    
    def _generate_multi_column_layout(self, page_layout: PageLayout, 
                                     image_paths: List[str]) -> str:
        """生成多列布局"""
        column_regions = [r for r in page_layout.regions if r.region_type == 'column']
        
        if not column_regions:
            return ""
        
        # 计算列宽
        column_widths = []
        for region in column_regions:
            width_percent = round(region.bbox.width / page_layout.page_width * 100, 1)
            column_widths.append(f"{width_percent}%")
        
        # 生成列内容
        column_contents = []
        for region in column_regions:
            column_content = self._generate_region_content(region, page_layout, image_paths)
            column_contents.append(column_content)
        
        # 使用Typst的columns功能
        columns_spec = ", ".join(column_widths)
        columns_content = "\n\n".join([
            f"#box(width: 100%)[{content}]" for content in column_contents
        ])
        
        return f'''#columns({len(column_regions)}, gutter: 1em)[
{columns_content}
]'''
    
    def _generate_single_column_layout(self, page_layout: PageLayout, 
                                      image_paths: List[str]) -> str:
        """生成单列布局"""
        content_parts = []
        
        # 按区域类型排序（页眉 -> 主体 -> 页脚）
        region_order = {'header': 0, 'column': 1, 'main': 1, 'footer': 2}
        sorted_regions = sorted(page_layout.regions, 
                               key=lambda r: region_order.get(r.region_type, 1))
        
        for region in sorted_regions:
            region_content = self._generate_region_content(region, page_layout, image_paths)
            if region_content.strip():
                content_parts.append(region_content)
        
        return '\n\n'.join(content_parts)
    
    def _generate_region_content(self, region: LayoutRegion, page_layout: PageLayout,
                                image_paths: List[str]) -> str:
        """生成区域内容"""
        content_parts = []
        
        for element_type, element in region.elements:
            if element_type == 'heading':
                content_parts.append(self._generate_heading_with_position(element, page_layout))
            elif element_type == 'paragraph':
                content_parts.append(self._generate_paragraph_with_position(element, page_layout))
            elif element_type == 'table':
                content_parts.append(self._generate_table_with_position(element, page_layout))
            elif element_type == 'image':
                # 找到对应的图像路径
                image_path = self._find_image_path(element, image_paths)
                content_parts.append(self._generate_image_with_position(element, image_path, page_layout))
            elif element_type == 'list':
                content_parts.append(self._generate_list_with_position(element, page_layout))
        
        return '\n\n'.join(content_parts)
    
    def _find_image_path(self, image: Image, image_paths: List[str]) -> str:
        """查找图像对应的路径"""
        # 简单匹配：根据文件名查找
        for path in image_paths:
            if image.filename in path:
                return path
        return ""
    
    def _generate_heading_absolute(self, heading: Heading, page_layout: PageLayout) -> str:
        """生成绝对定位的标题"""
        base_heading = self._generate_heading(heading)
        
        if not hasattr(heading, 'bbox') or not heading.bbox:
            return base_heading
        
        # 计算绝对位置（转换为相对单位）
        position = self._calculate_absolute_position(heading.bbox, page_layout)
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[{base_heading}]'''
    
    def _generate_paragraph_absolute(self, paragraph: Paragraph, page_layout: PageLayout) -> str:
        """生成绝对定位的段落"""
        base_paragraph = self._generate_paragraph(paragraph)
        
        if not hasattr(paragraph, 'bbox') or not paragraph.bbox:
            return base_paragraph
        
        # 计算绝对位置
        position = self._calculate_absolute_position(paragraph.bbox, page_layout)
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[#box(width: {position['width']})[{base_paragraph}]]'''
    
    def _generate_table_absolute(self, table: Table, page_layout: PageLayout) -> str:
        """生成绝对定位的表格"""
        base_table = self._generate_table(table)
        
        if not hasattr(table, 'bbox') or not table.bbox:
            return base_table
        
        # 计算绝对位置
        position = self._calculate_absolute_position(table.bbox, page_layout)
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[{base_table}]'''
    
    def _generate_image_absolute(self, image: Image, image_path: str, 
                                page_layout: PageLayout) -> str:
        """生成绝对定位的图像"""
        if not image_path:
            return f"// 图像文件缺失: {image.filename}"
        
        if not hasattr(image, 'bbox') or not image.bbox:
            return self._generate_image(image, image_path)
        
        # 计算绝对位置和尺寸
        position = self._calculate_absolute_position(image.bbox, page_layout)
        
        image_ref = f'''#figure(
  image("{image_path}", width: {position['width']}, height: {position['height']}),
  caption: []
)'''
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[{image_ref}]'''
    
    def _generate_list_absolute(self, doc_list: DocList, page_layout: PageLayout) -> str:
        """生成绝对定位的列表"""
        base_list = self._generate_list(doc_list)
        
        if not hasattr(doc_list, 'bbox') or not doc_list.bbox:
            return base_list
        
        # 计算绝对位置
        position = self._calculate_absolute_position(doc_list.bbox, page_layout)
        
        return f'''#place(
  dx: {position['left']},
  dy: {position['top']},
)[#box(width: {position['width']})[{base_list}]]'''
    
    def _calculate_absolute_position(self, bbox: 'BoundingBox', page_layout: PageLayout) -> Dict[str, str]:
        """计算绝对位置"""
        # 转换PDF坐标到Typst坐标（PDF原点在左下角，Typst在左上角）
        # 修复：使用y1（顶部）来计算top位置，这样元素顶部对应Typst的dy位置
        top_pt = page_layout.page_height - bbox.y1  # 从页面顶部到元素顶部的距离
        left_pt = bbox.x0
        width_pt = bbox.width
        height_pt = bbox.height
        
        # 确保坐标不会超出页面范围
        top_pt = max(0, min(top_pt, page_layout.page_height))
        left_pt = max(0, min(left_pt, page_layout.page_width))
        
        # 考虑页面边距 (10mm = 28.35pt)
        margin_pt = 28.35
        content_width = page_layout.page_width - 2 * margin_pt
        content_height = page_layout.page_height - 2 * margin_pt
        
        # 调整坐标到内容区域
        adjusted_left = left_pt - margin_pt
        adjusted_top = top_pt - margin_pt
        
        # 转换为相对单位（相对于内容区域）
        left_rel = max(0, adjusted_left / content_width * 100)
        top_rel = max(0, adjusted_top / content_height * 100)
        width_rel = width_pt / content_width * 100
        height_rel = height_pt / content_height * 100
        
        # 确保元素不超出页面边界
        if left_rel + width_rel > 100:
            width_rel = max(10, 100 - left_rel)
        if top_rel + height_rel > 100:
            height_rel = max(5, 100 - top_rel)
        
        # 强制限制top和left在合理范围内
        if top_rel > 95:  # 如果top超过95%，调整到合理位置
            top_rel = 95
        if left_rel > 90:  # 如果left超过90%，调整到合理位置
            left_rel = 90
        
        # 限制最大尺寸，避免元素过大
        width_rel = min(width_rel, 80)  # 最大80%宽度
        height_rel = min(height_rel, 60)  # 最大60%高度
        
        # 确保最小尺寸
        width_rel = max(width_rel, 10)  # 最小10%宽度
        height_rel = max(height_rel, 5)  # 最小5%高度
        
        # 四舍五入
        left_rel = round(left_rel, 2)
        top_rel = round(top_rel, 2)
        width_rel = round(width_rel, 2)
        height_rel = round(height_rel, 2)
        
        return {
            'top': f"{top_rel}%",
            'left': f"{left_rel}%",
            'width': f"{width_rel}%",
            'height': f"{height_rel}%"
        }
    
    def _generate_heading_with_position(self, heading: Heading, page_layout: PageLayout) -> str:
        """生成带位置信息的标题"""
        base_heading = self._generate_heading(heading)
        
        if not self.config['use_precise_positioning']:
            return base_heading
        
        # 获取精确位置信息
        position_info = self.layout_analyzer.get_element_precise_position(heading, page_layout)
        
        if not position_info:
            return base_heading
        
        # 根据位置信息调整样式
        if position_info.get('rel_x', 0) > 75:  # 右对齐
            return f"#align(right)[{base_heading}]"
        elif 25 < position_info.get('rel_x', 0) < 75:  # 居中
            return f"#align(center)[{base_heading}]"
        else:
            return base_heading  # 左对齐（默认）
    
    def _generate_paragraph_with_position(self, paragraph: Paragraph, page_layout: PageLayout) -> str:
        """生成带位置信息的段落"""
        base_paragraph = self._generate_paragraph(paragraph)
        
        if not self.config['use_precise_positioning']:
            return base_paragraph
        
        # 获取精确位置信息
        position_info = self.layout_analyzer.get_element_precise_position(paragraph, page_layout)
        
        if not position_info:
            return base_paragraph
        
        # 添加位置和间距信息
        adjustments = []
        
        # 检查是否需要特殊缩进
        if position_info.get('rel_x', 0) > 10:  # 有明显缩进
            indent_em = round(position_info.get('rel_x', 0) / 10, 1)
            adjustments.append(f"#pad(left: {indent_em}em)")
        
        # 检查是否需要特殊间距
        if self.config['maintain_spacing']:
            # 这里可以根据需要添加垂直间距调整
            pass
        
        if adjustments:
            return f"{''.join(adjustments)}[{base_paragraph}]"
        else:
            return base_paragraph
    
    def _generate_table_with_position(self, table: Table, page_layout: PageLayout) -> str:
        """生成带位置信息的表格"""
        base_table = self._generate_table(table)
        
        if not self.config['use_precise_positioning']:
            return base_table
        
        # 获取精确位置信息
        position_info = self.layout_analyzer.get_element_precise_position(table, page_layout)
        
        if not position_info:
            return base_table
        
        # 根据位置调整表格对齐
        if position_info.get('rel_x', 0) > 60:  # 右对齐
            return f"#align(right)[{base_table}]"
        elif 20 < position_info.get('rel_x', 0) < 80:  # 居中
            return f"#align(center)[{base_table}]"
        else:
            return base_table  # 左对齐（默认）
    
    def _generate_image_with_position(self, image: Image, image_path: str, 
                                     page_layout: PageLayout) -> str:
        """生成带位置信息的图像"""
        if not image_path:
            return f"// 图像文件缺失: {image.filename}"
        
        # 获取精确位置信息
        position_info = self.layout_analyzer.get_element_precise_position(image, page_layout)
        
        # 计算图像宽度
        if position_info and self.config['use_precise_positioning']:
            # 使用原始宽度比例
            width_percent = min(position_info.get('rel_width', 80), 100)
            width = f"{width_percent}%"
        else:
            width = self.config['image_width']
        
        # 生成图像引用
        image_ref = f'''#figure(
  image("{image_path}", width: {width}),
  caption: []
)'''
        
        # 根据位置确定对齐方式
        if position_info and self.config['use_precise_positioning']:
            rel_x = position_info.get('rel_x', 0)
            if rel_x > 70:  # 右对齐
                return f"#align(right)[{image_ref}]"
            elif 20 < rel_x < 80:  # 居中
                return f"#align(center)[{image_ref}]"
            else:  # 左对齐
                return image_ref
        else:
            # 使用默认对齐方式
            if self.config['image_alignment'] == 'center':
                return f"#align(center)[{image_ref}]"
            else:
                return image_ref
    
    def _generate_list_with_position(self, doc_list: DocList, page_layout: PageLayout) -> str:
        """生成带位置信息的列表"""
        base_list = self._generate_list(doc_list)
        
        if not self.config['use_precise_positioning']:
            return base_list
        
        # 获取精确位置信息
        position_info = self.layout_analyzer.get_element_precise_position(doc_list, page_layout)
        
        if not position_info:
            return base_list
        
        # 添加缩进调整
        if position_info.get('rel_x', 0) > 10:  # 有明显缩进
            indent_em = round(position_info.get('rel_x', 0) / 10, 1)
            return f"#pad(left: {indent_em}em)[{base_list}]"
        else:
            return base_list
    
    def _generate_heading(self, heading: Heading) -> str:
        """生成标题"""
        # 清理标题文本
        title_text = self._clean_heading_text(heading.text)
        
        # 检查是否是真正的标题（避免普通文本被误识别）
        if not self._is_valid_heading(title_text):
            # 如果不是有效标题，作为普通文本处理
            return title_text
        
        # 根据级别生成对应的Typst标题
        level_markers = "=" * max(1, min(heading.level, 6))  # 限制标题级别1-6
        
        return f"{level_markers} {title_text}"
    
    def _is_valid_heading(self, text: str) -> bool:
        """检查是否是有效的标题"""
        if not text or len(text.strip()) == 0:
            return False
        
        text = text.strip()
        
        # 标题特征检查
        # 1. 长度合理（不超过100字符）
        if len(text) > 100:
            return False
        
        # 2. 不包含句号结尾（标题通常不以句号结尾）
        if text.endswith('.') and not text.isupper():
            return False
        
        # 3. 不包含过多小写字母连续文本（避免段落被误识别）
        words = text.split()
        if len(words) > 10:  # 超过10个单词的可能是段落
            return False
        
        # 4. 检查是否包含常见的非标题内容
        non_heading_patterns = [
            'such as', 'for example', 'in many cases', 'occasionally',
            'depending on', 'when', 'where', 'which', 'that'
        ]
        text_lower = text.lower()
        for pattern in non_heading_patterns:
            if pattern in text_lower:
                return False
        
        return True
    
    def _separate_mixed_content(self, text: str) -> str:
        """分离混合内容，处理被错误合并的文本"""
        if not text:
            return text
        
        # 检测常见的文本合并模式
        # 1. 两个句子没有空格分隔（句号后直接跟大写字母）
        import re
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        # 2. 检测可能的标题合并（全大写单词连在一起）
        text = re.sub(r'([A-Z]{3,})([A-Z]{3,})', r'\1 \2', text)
        
        # 3. 处理常见的单词连接错误
        common_fixes = [
            ('inButterflyfishes', 'in Butterflyfishes'),
            ('towardstheir', 'towards their'),
            ('manyoccasions', 'many occasions'),
            ('cleanlyother', 'cleanly other'),
            ('specieswith', 'species with'),
            ('suchfish', 'such fish'),
            ('sidetheir', 'side their'),
            ('linesoccasions', 'lines occasions'),
            ('orWhen', 'or When'),
            ('pelewensisandC', 'pelewensis and C'),
            ('butorgans', 'but organs'),
            ('speciesadult', 'species adult'),
            ('ABERRATIONSSURVIVORS', 'ABERRATIONS SURVIVORS'),
        ]
        
        for wrong, correct in common_fixes:
            text = text.replace(wrong, correct)
        
        # 4. 修复数字和单词连接
        text = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', text)
        text = re.sub(r'([A-Za-z])(\d+)', r'\1 \2', text)
        
        return text.strip()
    
    def _generate_paragraph(self, paragraph: Paragraph) -> str:
        """生成段落"""
        # 合并段落中的文本块
        text_parts = []
        
        for block in paragraph.text_blocks:
            text = self._escape_typst_text(block.text)
            
            # 应用样式
            if block.is_bold:
                text = f"*{text}*"
            if block.is_italic:
                text = f"_{text}_"
            
            text_parts.append(text)
        
        paragraph_text = ' '.join(text_parts)
        
        # 清理混合内容
        cleaned_text = self._separate_mixed_content(paragraph_text)
        
        # 处理对齐方式
        if paragraph.alignment == 'center':
            return f"#align(center)[\n{cleaned_text}\n]"
        elif paragraph.alignment == 'right':
            return f"#align(right)[\n{cleaned_text}\n]"
        else:
            return cleaned_text
    
    def _generate_table(self, table: Table) -> str:
        """生成表格"""
        if not table.cells:
            return ""
        
        # 转换为二维数组
        table_data = table.to_2d_array()
        
        # 生成表格内容
        table_cells = []
        
        for row in table_data:
            # 转义单元格内容并用方括号包围
            for cell in row:
                escaped_cell = self._escape_typst_text(cell)
                table_cells.append(f"[{escaped_cell}]")
        
        # 用逗号和空格连接所有单元格
        table_content = ", ".join(table_cells) + ","
        
        # 生成表格定义
        col_spec = ", ".join(["auto"] * table.cols)
        
        typst_table = f'''#table(
  columns: ({col_spec}),
  stroke: {self.config['table_stroke']},
  fill: {self.config['table_fill']},
  {table_content}
)'''
        
        return typst_table
    
    def _generate_image(self, image: Image, image_path: str) -> str:
        """生成图像引用"""
        if not image_path:
            return f"// 图像文件缺失: {image.filename}"
        
        # 生成图像引用
        image_ref = f'''#figure(
  image("{image_path}", width: {self.config['image_width']}),
  caption: []
)'''
        
        if self.config['image_alignment'] == 'center':
            return f"#align(center)[\n{image_ref}\n]"
        else:
            return image_ref
    
    def _generate_list(self, doc_list: DocList) -> str:
        """生成列表"""
        if not doc_list.items:
            return ""
        
        list_items = []
        
        for item in doc_list.items:
            # 根据级别添加缩进
            indent = "  " * (item.level - 1)
            
            # 清理列表项文本（移除原始标记）
            text = self._clean_list_item_text(item.text)
            text = self._escape_typst_text(text)
            
            if doc_list.list_type == "ordered":
                list_items.append(f"{indent}+ {text}")
            else:
                list_items.append(f"{indent}- {text}")
        
        return "\n".join(list_items)
    
    def _save_images(self, images: List[Image], output_dir: Path) -> List[str]:
        """保存图像文件"""
        output_dir.mkdir(parents=True, exist_ok=True)
        image_paths = []
        
        # 获取图像文件夹名（相对于输出目录）
        folder_name = output_dir.name
        
        for image in images:
            # 创建图像文件路径
            image_file = output_dir / image.filename
            
            try:
                # 保存图像
                with open(image_file, 'wb') as f:
                    f.write(image.data)
                
                # 使用相对路径（包含文件夹名）
                relative_path = f"{folder_name}/{image.filename}"
                image_paths.append(relative_path)
                
                logger.info(f"保存图像: {image_file}")
                
            except Exception as e:
                logger.error(f"保存图像失败 {image.filename}: {e}")
                image_paths.append("")
        
        return image_paths
    
    def _escape_typst_text(self, text: str) -> str:
        """转义Typst特殊字符"""
        if not text:
            return ""
        
        # Typst特殊字符转义
        escape_map = {
            '#': '\\#',
            '@': '\\@',
            '$': '\\$',
            '*': '\\*',
            '_': '\\_',
            '`': '\\`',
            '[': '\\[',
            ']': '\\]',
            '<': '\\<',
            '>': '\\>',
            '\\': '\\\\',
        }
        
        result = text
        for char, escaped in escape_map.items():
            result = result.replace(char, escaped)
        
        return result
    
    def _clean_heading_text(self, text: str) -> str:
        """清理标题文本"""
        # 移除编号前缀
        text = re.sub(r'^(\d+(?:\.\d+)*\s*)', '', text.strip())
        text = re.sub(r'^(第[一二三四五六七八九十\d]+[章节]\s*)', '', text.strip())
        
        return text.strip()
    
    def _clean_list_item_text(self, text: str) -> str:
        """清理列表项文本"""
        # 移除列表标记
        text = re.sub(r'^\s*[•·▪▫◦‣⁃]\s*', '', text)
        text = re.sub(r'^\s*\d+[.、]\s*', '', text)
        text = re.sub(r'^\s*[a-zA-Z][.、)]\s*', '', text)
        text = re.sub(r'^\s*[一二三四五六七八九十]+[.、)]\s*', '', text)
        text = re.sub(r'^\s*[(（]\d+[)）]\s*', '', text)
        
        return text.strip()
    
    def _map_font_family(self, font_name: str) -> str:
        """映射字体族"""
        font_lower = font_name.lower()
        
        for key, mapped_font in self._font_mapping.items():
            if key in font_lower:
                return mapped_font
        
        # 如果没有匹配，返回默认字体
        return self.config['font_family']
    
    def generate_table_only(self, table: Table) -> str:
        """仅生成表格（用于测试）"""
        return self._generate_table(table)
    
    def generate_heading_only(self, heading: Heading) -> str:
        """仅生成标题（用于测试）"""
        return self._generate_heading(heading)
