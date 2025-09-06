"""
页面布局分析器

负责分析PDF页面的布局结构，包括：
- 多列布局识别
- 元素位置关系分析
- 文本环绕识别
- 精确位置还原
"""

from __future__ import annotations

import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import logging

from .models import (
    ParsedDocument, TextBlock, Image, Table, Heading, Paragraph,
    BoundingBox, ElementType
)

logger = logging.getLogger(__name__)


@dataclass
class LayoutRegion:
    """布局区域"""
    bbox: BoundingBox
    elements: List[Tuple[str, object]]  # (element_type, element)
    region_type: str  # 'column', 'header', 'footer', 'sidebar', 'main'
    column_index: int = 0


@dataclass
class PageLayout:
    """页面布局"""
    page_num: int
    page_width: float
    page_height: float
    regions: List[LayoutRegion]
    column_count: int
    has_header: bool = False
    has_footer: bool = False
    margins: Dict[str, float] = None


class LayoutAnalyzer:
    """页面布局分析器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化布局分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self._setup_config()
    
    def _setup_config(self):
        """设置默认配置"""
        default_config = {
            # 列检测参数
            'min_column_width': 150,  # 最小列宽
            'column_gap_threshold': 20,  # 列间距阈值
            'column_alignment_tolerance': 10,  # 列对齐容差
            
            # 区域检测参数
            'header_height_threshold': 100,  # 页眉高度阈值
            'footer_height_threshold': 80,   # 页脚高度阈值
            'margin_threshold': 50,          # 边距阈值
            
            # 元素关系参数
            'text_wrap_threshold': 20,       # 文本环绕阈值
            'vertical_spacing_threshold': 15, # 垂直间距阈值
            'horizontal_spacing_threshold': 10, # 水平间距阈值
            
            # 位置精度参数
            'position_precision': 2,         # 位置精度（小数点后位数）
            'size_precision': 2,             # 尺寸精度
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze_page_layout(self, parsed_doc: ParsedDocument, page_num: int) -> PageLayout:
        """
        分析页面布局
        
        Args:
            parsed_doc: 解析后的文档
            page_num: 页面号
            
        Returns:
            PageLayout: 页面布局信息
        """
        logger.info(f"分析第{page_num}页的布局")
        
        # 获取页面元素
        page_elements = parsed_doc.get_elements_by_page(page_num)
        
        # 获取真实页面尺寸
        page_width, page_height = self._get_real_page_size(parsed_doc, page_num)
        
        # 合并所有元素
        all_elements = self._collect_all_elements(page_elements)
        
        # 使用绝对定位布局而不是强制多列布局
        regions = self._create_absolute_layout(all_elements, page_width, page_height)
        
        # 分析元素关系
        self._analyze_element_relationships(regions)
        
        layout = PageLayout(
            page_num=page_num,
            page_width=page_width,
            page_height=page_height,
            regions=regions,
            column_count=1,  # 使用绝对定位，不分列
            has_header=any(r.region_type == 'header' for r in regions),
            has_footer=any(r.region_type == 'footer' for r in regions),
            margins=self._calculate_margins(all_elements, page_width, page_height)
        )
        
        logger.info(f"页面布局分析完成：使用绝对定位布局")
        return layout
    
    def _collect_all_elements(self, page_elements: Dict) -> List[Tuple[str, object]]:
        """收集页面中的所有元素"""
        all_elements = []
        
        # 添加各类元素
        for heading in page_elements.get('headings', []):
            all_elements.append(('heading', heading))
        
        for paragraph in page_elements.get('paragraphs', []):
            all_elements.append(('paragraph', paragraph))
        
        for table in page_elements.get('tables', []):
            all_elements.append(('table', table))
        
        for image in page_elements.get('images', []):
            all_elements.append(('image', image))
        
        for doc_list in page_elements.get('lists', []):
            all_elements.append(('list', doc_list))
        
        return all_elements
    
    def _get_real_page_size(self, parsed_doc: ParsedDocument, page_num: int) -> Tuple[float, float]:
        """获取真实的页面尺寸"""
        # 尝试从文档元数据中获取页面信息
        if hasattr(parsed_doc, 'pages') and parsed_doc.pages:
            for page_info in parsed_doc.pages:
                if page_info.number == page_num:
                    return page_info.width, page_info.height
        
        # 如果没有页面信息，回退到估算方法
        return self._estimate_page_size_from_elements(parsed_doc.get_elements_by_page(page_num))
    
    def _create_absolute_layout(self, elements: List[Tuple[str, object]], 
                               page_width: float, page_height: float) -> List[LayoutRegion]:
        """创建绝对定位布局"""
        if not elements:
            return []
        
        # 创建单个主要区域，包含所有元素，按位置排序
        sorted_elements = sorted(elements, key=lambda x: self._get_element_sort_key(x[1]))
        
        main_region = LayoutRegion(
            bbox=BoundingBox(0, 0, page_width, page_height),
            elements=sorted_elements,
            region_type='absolute',  # 新的区域类型
            column_index=0
        )
        
        return [main_region]
    
    def _estimate_page_size_from_elements(self, page_elements: Dict) -> Tuple[float, float]:
        """从元素估算页面尺寸"""
        all_elements = self._collect_all_elements(page_elements)
        
        if not all_elements:
            return 595.0, 842.0  # A4默认尺寸（点）
        
        # 从所有元素的边界框推断页面尺寸
        max_x = 0
        max_y = 0
        
        for element_type, element in all_elements:
            if hasattr(element, 'bbox') and element.bbox:
                max_x = max(max_x, element.bbox.x1)
                max_y = max(max_y, element.bbox.y1)
        
        # 添加一些边距
        page_width = max_x + 50 if max_x > 0 else 595.0
        page_height = max_y + 50 if max_y > 0 else 842.0
        
        return page_width, page_height
    
    def _detect_columns(self, elements: List[Tuple[str, object]], 
                       page_width: float, page_height: float) -> List[LayoutRegion]:
        """检测列布局"""
        if not elements:
            return []
        
        # 按x坐标分组元素
        x_positions = []
        for element_type, element in elements:
            if hasattr(element, 'bbox') and element.bbox:
                x_positions.append(element.bbox.x0)
        
        if not x_positions:
            return []
        
        # 聚类x坐标来识别列
        x_positions.sort()
        column_starts = self._cluster_positions(x_positions)
        
        # 如果只有一列，创建单列布局
        if len(column_starts) <= 1:
            return [LayoutRegion(
                bbox=BoundingBox(0, 0, page_width, page_height),
                elements=elements,
                region_type='column',
                column_index=0
            )]
        
        # 创建多列区域
        regions = []
        for i, start_x in enumerate(column_starts):
            # 计算列的右边界
            if i < len(column_starts) - 1:
                end_x = column_starts[i + 1] - self.config['column_gap_threshold'] / 2
            else:
                end_x = page_width
            
            # 分配元素到此列
            column_elements = []
            for element_type, element in elements:
                if (hasattr(element, 'bbox') and element.bbox and
                    start_x <= element.bbox.x0 < end_x):
                    column_elements.append((element_type, element))
            
            if column_elements:
                regions.append(LayoutRegion(
                    bbox=BoundingBox(start_x, 0, end_x, page_height),
                    elements=column_elements,
                    region_type='column',
                    column_index=i
                ))
        
        return regions
    
    def _cluster_positions(self, positions: List[float]) -> List[float]:
        """聚类位置坐标"""
        if not positions:
            return []
        
        clusters = [positions[0]]
        threshold = self.config['column_alignment_tolerance']
        
        for pos in positions[1:]:
            # 检查是否与现有聚类接近
            found_cluster = False
            for i, cluster_pos in enumerate(clusters):
                if abs(pos - cluster_pos) <= threshold:
                    found_cluster = True
                    break
            
            if not found_cluster:
                clusters.append(pos)
        
        return sorted(clusters)
    
    def _detect_special_regions(self, regions: List[LayoutRegion], 
                               page_height: float) -> List[LayoutRegion]:
        """检测特殊区域（页眉、页脚等）"""
        if not regions:
            return regions
        
        result_regions = []
        header_threshold = page_height - self.config['header_height_threshold']
        footer_threshold = self.config['footer_height_threshold']
        
        for region in regions:
            # 检查是否为页眉区域
            if region.bbox.y0 > header_threshold:
                # 将此区域标记为页眉
                header_elements = []
                main_elements = []
                
                for element_type, element in region.elements:
                    if hasattr(element, 'bbox') and element.bbox.y0 > header_threshold:
                        header_elements.append((element_type, element))
                    else:
                        main_elements.append((element_type, element))
                
                if header_elements:
                    result_regions.append(LayoutRegion(
                        bbox=BoundingBox(region.bbox.x0, header_threshold, 
                                       region.bbox.x1, page_height),
                        elements=header_elements,
                        region_type='header',
                        column_index=region.column_index
                    ))
                
                if main_elements:
                    result_regions.append(LayoutRegion(
                        bbox=BoundingBox(region.bbox.x0, region.bbox.y0,
                                       region.bbox.x1, header_threshold),
                        elements=main_elements,
                        region_type='column',
                        column_index=region.column_index
                    ))
            
            # 检查是否为页脚区域
            elif region.bbox.y1 < footer_threshold:
                # 类似的页脚处理逻辑
                footer_elements = []
                main_elements = []
                
                for element_type, element in region.elements:
                    if hasattr(element, 'bbox') and element.bbox.y1 < footer_threshold:
                        footer_elements.append((element_type, element))
                    else:
                        main_elements.append((element_type, element))
                
                if footer_elements:
                    result_regions.append(LayoutRegion(
                        bbox=BoundingBox(region.bbox.x0, 0,
                                       region.bbox.x1, footer_threshold),
                        elements=footer_elements,
                        region_type='footer',
                        column_index=region.column_index
                    ))
                
                if main_elements:
                    result_regions.append(LayoutRegion(
                        bbox=BoundingBox(region.bbox.x0, footer_threshold,
                                       region.bbox.x1, region.bbox.y1),
                        elements=main_elements,
                        region_type='column',
                        column_index=region.column_index
                    ))
            else:
                result_regions.append(region)
        
        return result_regions
    
    def _analyze_element_relationships(self, regions: List[LayoutRegion]):
        """分析元素之间的关系"""
        for region in regions:
            # 按位置排序区域内的元素
            region.elements.sort(key=lambda x: self._get_element_sort_key(x[1]))
            
            # 分析文本环绕等关系
            self._analyze_text_wrapping(region)
    
    def _get_element_sort_key(self, element) -> Tuple[float, float]:
        """获取元素排序键"""
        if hasattr(element, 'bbox') and element.bbox:
            # 先按y坐标（从上到下），再按x坐标（从左到右）
            return (-element.bbox.y0, element.bbox.x0)
        return (0, 0)
    
    def _analyze_text_wrapping(self, region: LayoutRegion):
        """分析文本环绕"""
        # 识别图像周围的文本环绕
        images = [(i, elem) for i, (elem_type, elem) in enumerate(region.elements) 
                 if elem_type == 'image']
        
        for img_idx, image in images:
            if not hasattr(image, 'bbox'):
                continue
            
            # 查找可能环绕此图像的文本
            for i, (text_type, text_elem) in enumerate(region.elements):
                if (text_type in ['paragraph', 'heading'] and 
                    hasattr(text_elem, 'bbox') and text_elem.bbox):
                    
                    # 检查文本是否在图像周围
                    if self._is_text_wrapping_image(text_elem.bbox, image.bbox):
                        # 标记为环绕文本（可以在元素上添加属性）
                        if hasattr(text_elem, 'wraps_around'):
                            text_elem.wraps_around = image
    
    def _is_text_wrapping_image(self, text_bbox: BoundingBox, 
                               image_bbox: BoundingBox) -> bool:
        """判断文本是否环绕图像"""
        threshold = self.config['text_wrap_threshold']
        
        # 简单的环绕检测：文本在图像的左侧或右侧，且垂直位置有重叠
        horizontal_adjacent = (
            abs(text_bbox.x1 - image_bbox.x0) < threshold or
            abs(image_bbox.x1 - text_bbox.x0) < threshold
        )
        
        vertical_overlap = not (
            text_bbox.y1 < image_bbox.y0 - threshold or
            text_bbox.y0 > image_bbox.y1 + threshold
        )
        
        return horizontal_adjacent and vertical_overlap
    
    def _calculate_margins(self, elements: List[Tuple[str, object]], 
                          page_width: float, page_height: float) -> Dict[str, float]:
        """计算页面边距"""
        if not elements:
            return {'top': 50, 'bottom': 50, 'left': 50, 'right': 50}
        
        min_x = page_width
        max_x = 0
        min_y = page_height
        max_y = 0
        
        for element_type, element in elements:
            if hasattr(element, 'bbox') and element.bbox:
                min_x = min(min_x, element.bbox.x0)
                max_x = max(max_x, element.bbox.x1)
                min_y = min(min_y, element.bbox.y0)
                max_y = max(max_y, element.bbox.y1)
        
        return {
            'left': round(min_x, self.config['position_precision']),
            'right': round(page_width - max_x, self.config['position_precision']),
            'top': round(page_height - max_y, self.config['position_precision']),
            'bottom': round(min_y, self.config['position_precision'])
        }
    
    def get_element_precise_position(self, element, page_layout: PageLayout) -> Dict[str, float]:
        """获取元素的精确位置信息"""
        if not hasattr(element, 'bbox') or not element.bbox:
            return {}
        
        bbox = element.bbox
        
        # 转换为相对位置（相对于页面尺寸的百分比）
        rel_x = round(bbox.x0 / page_layout.page_width * 100, 
                     self.config['position_precision'])
        rel_y = round((page_layout.page_height - bbox.y1) / page_layout.page_height * 100,
                     self.config['position_precision'])
        rel_width = round(bbox.width / page_layout.page_width * 100,
                         self.config['size_precision'])
        rel_height = round(bbox.height / page_layout.page_height * 100,
                          self.config['size_precision'])
        
        return {
            'abs_x': round(bbox.x0, self.config['position_precision']),
            'abs_y': round(bbox.y0, self.config['position_precision']),
            'abs_width': round(bbox.width, self.config['size_precision']),
            'abs_height': round(bbox.height, self.config['size_precision']),
            'rel_x': rel_x,
            'rel_y': rel_y,
            'rel_width': rel_width,
            'rel_height': rel_height
        }
