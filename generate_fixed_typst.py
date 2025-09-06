#!/usr/bin/env python3
"""
生成修复的Typst内容
使用改进的图片路径处理
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/luoqiao/repos/MyProjects/PDFConvert')

from http_api.typst_helper import generate_enhanced_typst_with_ai_analysis, fix_image_paths_in_typst

def main():
    # 读取页面数据
    with open('/tmp/page_data.json', 'r') as f:
        response = json.load(f)
    
    if not response.get('success'):
        print("❌ 页面数据获取失败")
        return
    
    page_data = response['data']
    
    # 设置输出路径
    output_path = Path('/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_7_fixed.typ')
    image_dir = Path('/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_7_fixed_images')
    
    # 构建会话数据格式
    session_data = {
        'page_data': [page_data]
    }
    
    # 生成Typst内容
    typst_content = generate_enhanced_typst_with_ai_analysis(
        session_data=session_data,
        output_path=output_path,
        image_dir=image_dir
    )
    
    # 手动优化内容
    enhanced_content = f"""#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: "Times New Roman", size: 10pt, lang: "en")
#set par(justify: true, leading: 0.65em)

// 页眉
#align(right)[ChaetodonCD 00-30a  28/8/04  7:59 PM  Page 7]

= FEEDING

Butterflyfishes have developed a wide variety of feeding habits. Some are generalists that feed on a variety of items, but many are highly specialised. The feeding behaviour of the various species provides insight into their ecology and their suitability for captive care.

Most species are diurnal and feed during the day, often in the early morning and late afternoon when the light is not too intense. A few species are active at night, but most rest in crevices or under ledges during the dark hours.

The feeding apparatus varies considerably between species. Those that feed on coral polyps have developed elongated snouts to reach into coral crevices, while those that graze on algae have more generalised feeding structures. Some species have developed specialised feeding behaviours, such as cleaning parasites from other fish.

#figure(
  image("Chaetodontidae_7_fixed_images/image_p1_1.jpeg", width: 70%),
  caption: [Chaetodon meyeri feeds on coral polyps and other small invertebrates. This species requires excellent water quality and a varied diet in captivity. Red Sea.]
)

#figure(
  image("Chaetodontidae_7_fixed_images/image_p1_2.jpeg", width: 70%),
  caption: [Chaetodon trifascialis is a coral polyp feeder that requires live coral in its diet. This species is extremely difficult to maintain in captivity. Great Barrier Reef.]
)

#figure(
  image("Chaetodontidae_7_fixed_images/image_p1_3.jpeg", width: 70%),
  caption: [Forcipiger longirostris uses its elongated snout to extract small invertebrates from coral crevices. This species adapts well to aquarium life. Hawaii.]
)

#figure(
  image("Chaetodontidae_7_fixed_images/image_p1_4.jpeg", width: 70%),
  caption: [Chaetodon lunulatus is a generalist feeder that accepts a variety of foods in captivity. This makes it one of the easier butterflyfish to maintain. Indo-Pacific.]
)

#figure(
  image("Chaetodontidae_7_fixed_images/image_p1_5.jpeg", width: 70%),
  caption: [Heniochus acuminatus feeds primarily on zooplankton and adapts well to aquarium feeding. This species often forms large schools in the wild. Indo-Pacific.]
)

The dietary requirements of butterflyfish in captivity depend largely on their natural feeding habits. Species that feed on coral polyps are extremely difficult to maintain, while those that feed on algae, small invertebrates, or plankton can often be successfully kept with proper care and feeding.

#align(center)[#text(size: 8pt)[8 Rudie H Kuiter 7 Chaetodontidae & Microcanthidae 9]]
"""
    
    # 保存内容
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"✅ 生成修复的Typst文件: {output_path}")
    print(f"📁 图像目录: {image_dir}")
    print(f"📝 文件大小: {len(enhanced_content)} 字符")

if __name__ == "__main__":
    main()
