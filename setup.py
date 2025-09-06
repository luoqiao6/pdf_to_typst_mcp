"""
PDF转Typst工具安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# 读取requirements文件
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="pdf2typst",
    version="0.1.0",
    author="PDF2Typst Team",
    author_email="contact@pdf2typst.com",
    description="专业的PDF转Typst工具，专门针对学术类PDF文档",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/PDFConvert",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Markup",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    python_requires=">=3.8",
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "web": [
            "Flask>=2.3.0",
            "Werkzeug>=2.3.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "pdf2typst=cli.main:cli",
        ],
    },
    
    include_package_data=True,
    zip_safe=False,
)
