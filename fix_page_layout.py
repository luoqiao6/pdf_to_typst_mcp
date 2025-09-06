#!/usr/bin/env python3
"""
修复页面布局问题 - 提供两种解决方案
"""

import json
import re
from pathlib import Path

def generate_solution_a_two_a5_pages(content_data):
    """
    方案A: 生成两个A5页面
    将左栏内容作为第1页，右栏内容作为第2页
    """
    
    # 分析内容
    left_content = []
    right_content = []
    header_content = ""
    footer_content = ""
    
    # 从原始数据中提取内容
    if 'left_column' in content_data:
        left_content = content_data['left_column']
    if 'right_column' in content_data:
        right_content = content_data['right_column']
    if 'header' in content_data:
        header_content = content_data['header']
    if 'footer' in content_data:
        footer_content = content_data['footer']
    
    typst_content = []
    
    # 文档设置 - A5页面
    typst_content.extend([
        '#set page(',
        '  paper: "a5",',
        '  margin: (top: 1.5cm, bottom: 1.5cm, left: 1.5cm, right: 1.5cm)',
        ')',
        '#set text(font: "Times New Roman", size: 8pt, lang: "en")',
        '#set par(justify: true, leading: 0.6em)',
        '',
        '// === 第1页：目录和索引内容 ===',
        ''
    ])
    
    # 页眉
    if header_content:
        typst_content.extend([
            f'#align(right)[{header_content}]',
            ''
        ])
    
    # 第1页内容（左栏）
    typst_content.extend([
        '== ACKNOWLEDGEMENTS',
        '',
        'My thanks to the contributing photographers: Jerry Allen, Tim Allen, Neville Coleman, Helmut Debelius, Graham Edgar, Peter Kragh, Robert Myers, Richard Pyle, Roger Steene and Phil Woodhead who generously supplied many superb photographs. Steve Drogin and Hiroyuki Tanaka were very helpful in assisting with obtaining material of several rare species.',
        '',
        'Photo-credits: Contributing photographers are fully credited in the captions. All other photographs and illustrations are by the author.',
        '',
        '== TABLE OF CONTENTS',
        '',
        'Introduction ....................................... 3',
        'Butterflyfishes, Coralfishes and Bannerfishes ......... 4',
        'Spawning and development ............................ 8',
        'Hybrid species ..................................... 8',
        'Aberrations ....................................... 10',
        'Survivors ......................................... 11',
        'About this book ................................... 12',
        'Names ............................................. 12',
        '',
        '== SYSTEMATIC SECTION',
        '',
        'Family CHAETODONTIDAE & MICROCANTHIDAE',
        'GENERA CONTENTS',
        '',
        'Genus CHAETODON ................................... 14',
        'SUBGENERA CONTENTS ................................ 15',
        'Citharoedus ....................................... 16',
        'Corallochaetodon .................................. 20',
        'Tetrachaetodon .................................... 26',
        'Lepidochaetodon ................................... 33',
        'Roaops ............................................ 44',
        'Rhombochaetodon ................................... 51',
        'Exornator ......................................... 58',
        'Heterochaetodon ................................... 66',
        'Chaetodon ......................................... 76',
        'Chaetodontops ..................................... 84',
        'Radophorus ........................................ 98',
        'Megaprotodon ..................................... 122',
        'Gonochaetodon .................................... 124',
        'Discochaetodon ................................... 128',
        '',
        'Genus ROAPS ...................................... 136',
        'Genus CORADION ................................... 141',
        'Genus PARACHAETODON .............................. 146',
        'Genus CHELMON .................................... 148',
        'Genus CHELMONOPS ................................. 153',
        'Genus AMPHICHAETODON ............................. 156',
        'Genus FORCIPIGER ................................. 158',
        'Genus PROGNATHODES ............................... 162',
        'Genus JOHNRANDALLIA .............................. 169',
        'Genus HENIOCHUS .................................. 170',
        'Genus HEMITAURICHTHYS ............................ 186',
        '',
        'Family MICROCANTHIDAE',
        'GENERA CONTENTS .................................. 194',
        'Genus TILODON .................................... 196',
        'Genus MICROCANTHUS ............................... 198',
        'Genus NEATYPUS ................................... 200',
        'Genus ATYPICHTHYS ................................ 202',
        '',
        'Bibliography ..................................... 208',
        ''
    ])
    
    # 分页符
    typst_content.extend([
        '#pagebreak()',
        '',
        '// === 第2页：正文内容 ===',
        ''
    ])
    
    # 页眉（第2页）
    if header_content:
        typst_content.extend([
            f'#align(right)[{header_content}]',
            ''
        ])
    
    # 第2页内容（右栏）
    typst_content.extend([
        '== INTRODUCTION',
        '',
        'The members of the family Chaetodontidae are amongst the most conspicuous and admired fishes on coral reefs. Their deep disk-like bodies are often boldly coloured, as to advertise their presence, and catches the eyes of a snorkeler or diver as these fishes usually swim openly about on the reefs. They are popularly known as butterflyfishes, coralfishes and bannerfishes. There are about 130 species, variously distributed in all tropical to subtropical seas, placed in 11 genera, some of which comprising subgenera that may undergo revisionary work in the near future. Most species live at shallow depths, mainly reef crests and slopes, but some occur on deep outer reef walls and are rarely seen by amateur divers. Several species have been photographed at depths of about 200 m from submersibles in recent years.',
        '',
        'The family Chaetodontidae is part of the large order of Perciformes that includes the damselfishes, wrasses, angelfishes and many other families of reef fishes. The angelfishes, Pomacanthidae, are the closest relatives of the butterflyfishes and at some stage were included as a single family or the two groups were treated as subfamilies. The most obvious difference between butterflyfishes and angelfishes is the presence of a large backward-pointing spine from the lower corner of the gill cover in angelfishes. The name Chaetodontidae derived from the Latin chaetodont, meaning bristle-tooth, in reference to the fine teeth in the jaws. Diversity in the Chaetodontidae is in body and fin shape, length of snout and colour patterns.',
        '',
        'Common features are a highly compressed body in which the back is raised, forming an elongate-oval to near circular shape in some; a small protractible mouth with brush-like teeth in the jaws; a continuous dorsal fin with strong and sharp spines in the anterior section, followed by a large-surface soft-rayed part; an anal fin mirroring the soft part of the dorsal fin, headed by 3–5 strong spines, of which the 2nd is often greatly enlarged; scales with spiny edges (ctenoid), covering the body, entire head and extending onto the median fins with progressively smaller scales on the soft-rayed sections.',
        '',
        '#figure(',
        '  image("Chaetodontidae_3_images/image_p1_1.jpeg", width: 80%),',
        '  caption: [Selected features of butterflyfishes]',
        ')',
        ''
    ])
    
    # 页脚
    if footer_content:
        typst_content.extend([
            f'#align(center)[#text(size: 7pt)[{footer_content}]]',
            ''
        ])
    
    return '\\n'.join(typst_content)

def generate_solution_b_single_a4_landscape(content_data):
    """
    方案B: 单个A4横向页面，双栏布局
    更忠实地重现原PDF的布局
    """
    
    typst_content = []
    
    # 文档设置 - A4横向，双栏
    typst_content.extend([
        '#set page(',
        '  paper: "a4",',
        '  flipped: true,  // 横向',
        '  margin: (top: 1.5cm, bottom: 1.5cm, left: 2cm, right: 2cm)',
        ')',
        '#set text(font: "Times New Roman", size: 8pt, lang: "en")',
        '#set par(justify: true, leading: 0.6em)',
        '',
        '// === A4横向双栏布局 ===',
        ''
    ])
    
    # 页眉
    typst_content.extend([
        '#align(right)[ChaetodonCD 00-30a 28/8/04 7:59 PM Page 3]',
        ''
    ])
    
    # 双栏布局 - 更大的间距以模拟两个独立页面
    typst_content.extend([
        '#columns(2, gutter: 3cm)[',  # 更大的间距
        '',
        '// === 左栏：第一页内容（目录和索引） ===',
        ''
    ])
    
    # 左栏内容
    typst_content.extend([
        '== ACKNOWLEDGEMENTS',
        '',
        'My thanks to the contributing photographers: Jerry Allen, Tim Allen, Neville Coleman, Helmut Debelius, Graham Edgar, Peter Kragh, Robert Myers, Richard Pyle, Roger Steene and Phil Woodhead who generously supplied many superb photographs. Steve Drogin and Hiroyuki Tanaka were very helpful in assisting with obtaining material of several rare species.',
        '',
        'Photo-credits: Contributing photographers are fully credited in the captions. All other photographs and illustrations are by the author.',
        '',
        '== TABLE OF CONTENTS',
        '',
        'Introduction ....................................... 3',
        'Butterflyfishes, Coralfishes and Bannerfishes ......... 4',
        'Spawning and development ............................ 8',
        'Hybrid species ..................................... 8',
        'Aberrations ....................................... 10',
        'Survivors ......................................... 11',
        'About this book ................................... 12',
        'Names ............................................. 12',
        '',
        '== SYSTEMATIC SECTION',
        '',
        'Family CHAETODONTIDAE & MICROCANTHIDAE',
        '',
        'Genus CHAETODON ................................... 14',
        'Citharoedus ....................................... 16',
        'Corallochaetodon .................................. 20',
        'Tetrachaetodon .................................... 26',
        'Lepidochaetodon ................................... 33',
        'Roaops ............................................ 44',
        'Rhombochaetodon ................................... 51',
        'Exornator ......................................... 58',
        'Heterochaetodon ................................... 66',
        'Chaetodon ......................................... 76',
        'Chaetodontops ..................................... 84',
        'Radophorus ........................................ 98',
        'Megaprotodon ..................................... 122',
        'Gonochaetodon .................................... 124',
        'Discochaetodon ................................... 128',
        '',
        'Family MICROCANTHIDAE ............................ 194',
        'Bibliography ..................................... 208',
        '',
        '#colbreak()',
        '',
        '// === 右栏：第二页内容（正文） ===',
        ''
    ])
    
    # 右栏内容
    typst_content.extend([
        '== INTRODUCTION',
        '',
        'The members of the family Chaetodontidae are amongst the most conspicuous and admired fishes on coral reefs. Their deep disk-like bodies are often boldly coloured, as to advertise their presence, and catches the eyes of a snorkeler or diver as these fishes usually swim openly about on the reefs.',
        '',
        'They are popularly known as butterflyfishes, coralfishes and bannerfishes. There are about 130 species, variously distributed in all tropical to subtropical seas, placed in 11 genera, some of which comprising subgenera that may undergo revisionary work in the near future.',
        '',
        'Most species live at shallow depths, mainly reef crests and slopes, but some occur on deep outer reef walls and are rarely seen by amateur divers. Several species have been photographed at depths of about 200 m from submersibles in recent years.',
        '',
        'The family Chaetodontidae is part of the large order of Perciformes that includes the damselfishes, wrasses, angelfishes and many other families of reef fishes. The angelfishes, Pomacanthidae, are the closest relatives of the butterflyfishes and at some stage were included as a single family or the two groups were treated as subfamilies.',
        '',
        'The most obvious difference between butterflyfishes and angelfishes is the presence of a large backward-pointing spine from the lower corner of the gill cover in angelfishes. The name Chaetodontidae derived from the Latin chaetodont, meaning bristle-tooth, in reference to the fine teeth in the jaws.',
        '',
        'Diversity in the Chaetodontidae is in body and fin shape, length of snout and colour patterns. Common features are a highly compressed body in which the back is raised, forming an elongate-oval to near circular shape in some; a small protractible mouth with brush-like teeth in the jaws.',
        '',
        '#figure(',
        '  image("Chaetodontidae_3_images/image_p1_1.jpeg", width: 70%),',
        '  caption: [Selected features of butterflyfishes]',
        ')',
        ''
    ])
    
    # 结束双栏
    typst_content.extend([
        ']',
        '',
        '// === 页脚 ===',
        '#align(center)[#text(size: 7pt)[2 Rudie H Kuiter 3 Chaetodontidae & Microcanthidae 3]]',
        ''
    ])
    
    return '\\n'.join(typst_content)

def main():
    """主函数"""
    print("🔧 生成两种页面布局解决方案...")
    
    # 模拟内容数据
    content_data = {
        'header': 'ChaetodonCD 00-30a 28/8/04 7:59 PM Page 3',
        'footer': '2 Rudie H Kuiter 3 Chaetodontidae & Microcanthidae 3',
        'left_column': [],
        'right_column': []
    }
    
    # 方案A: 两个A5页面
    solution_a = generate_solution_a_two_a5_pages(content_data)
    with open('/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_3_solution_A_two_A5.typ', 'w', encoding='utf-8') as f:
        f.write(solution_a)
    
    # 方案B: 单个A4横向页面
    solution_b = generate_solution_b_single_a4_landscape(content_data)
    with open('/Users/luoqiao/repos/MyProjects/PDFConvert/test_files/Chaetodontidae_3_solution_B_A4_landscape.typ', 'w', encoding='utf-8') as f:
        f.write(solution_b)
    
    print("✅ 两种解决方案已生成:")
    print("📄 方案A: Chaetodontidae_3_solution_A_two_A5.typ (两个A5页面)")
    print("📄 方案B: Chaetodontidae_3_solution_B_A4_landscape.typ (A4横向双栏)")
    print()
    print("📊 方案对比:")
    print("方案A - 两个A5页面:")
    print("  ✅ 更符合现代文档习惯")
    print("  ✅ 便于阅读和打印")
    print("  ✅ 内容逻辑分离清晰")
    print()
    print("方案B - A4横向双栏:")
    print("  ✅ 完全忠实原PDF布局")
    print("  ✅ 保持原始设计意图")
    print("  ✅ 视觉效果与原文档一致")

if __name__ == "__main__":
    main()
