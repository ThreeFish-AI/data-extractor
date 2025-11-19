# 增强版 PDF 转 Markdown 工具使用指南

## 概述

`convert_pdf_to_markdown` 工具现在支持增强的内容提取功能，可以从 PDF 文档中智能提取并处理图像、表格和数学公式。

## 🆕 新增功能

### 🖼️ 图像提取
- **内容提取**：从 PDF 页面中提取所有图像元素
- **本地存储**：将提取的图像保存为本地文件（PNG/JPG格式）
- **Markdown集成**：在生成的 Markdown 文档中正确引用图像文件
- **Base64嵌入**：可选择将图像直接嵌入到 Markdown 文档中

### 📊 表格提取
- **智能识别**：自动识别各种格式的表格（管道符分隔、制表符分隔、空格分隔）
- **格式转换**：将表格转换为标准 Markdown 表格格式
- **结构保持**：保留表格的行列关系和内容完整性
- **标题提取**：自动识别表格标题和表头

### 🧮 数学公式提取
- **LaTeX识别**：识别多种 LaTeX 格式的数学公式
- **内联公式**：提取 `$...$` 或 `\(...\)` 格式的内联公式
- **块级公式**：提取 `$$...$$` 或 `\[...\]` 格式的块级公式
- **格式保持**：在 Markdown 中保持原始 LaTeX 格式

## 📖 使用方法

### 基本用法

```python
# 调用增强版 PDF 转 Markdown 工具
result = await convert_pdf_to_markdown(
    pdf_source="/path/to/document.pdf",
    method="auto",
    output_format="markdown"
)
```

### 启用增强功能

```python
# 启用所有增强功能
result = await convert_pdf_to_markdown(
    pdf_source="https://example.com/document.pdf",
    method="pymupdf",
    output_format="markdown",
    extract_images=True,      # 提取图像
    extract_tables=True,      # 提取表格
    extract_formulas=True,    # 提取数学公式
    embed_images=False,       # 不嵌入图像，使用本地文件引用
    enhanced_options={
        "output_dir": "./extracted_assets",  # 自定义输出目录
        "image_size": [800, 600]            # 图像尺寸调整
    }
)
```

### 选择性启用功能

```python
# 只提取图像和表格，不提取数学公式
result = await convert_pdf_to_markdown(
    pdf_source="document.pdf",
    extract_images=True,
    extract_tables=True,
    extract_formulas=False,  # 禁用公式提取
    embed_images=True        # 将图像嵌入到文档中
)
```

### 嵌入图像到 Markdown

```python
# 将图像以 base64 格式嵌入到 Markdown 文档中
result = await convert_pdf_to_markdown(
    pdf_source="document.pdf",
    extract_images=True,
    embed_images=True,        # 启用图像嵌入
    enhanced_options={
        "output_dir": "./temp"  # 临时目录
    }
)
```

## 📋 参数说明

### 新增参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `extract_images` | bool | True | 是否从PDF中提取图像并保存为本地文件 |
| `extract_tables` | bool | True | 是否从PDF中提取表格并转换为Markdown表格格式 |
| `extract_formulas` | bool | True | 是否从PDF中提取数学公式并保持LaTeX格式 |
| `embed_images` | bool | False | 是否将提取的图像以base64格式嵌入到Markdown文档中 |
| `enhanced_options` | dict | None | 增强处理选项 |

### enhanced_options 详细配置

```python
enhanced_options = {
    "output_dir": "./extracted_assets",  # 输出目录路径
    "image_size": [800, 600],            # 图像尺寸调整 [width, height]
    "image_format": "png",               # 图像格式 (png, jpg)
    "image_quality": 90,                 # 图像质量 (1-100，仅适用于JPEG)
}
```

## 📤 返回结果

增强版工具返回的 PDFResponse 对象包含额外的 `enhanced_assets` 字段：

```python
{
    "success": True,
    "content": "# 文档标题\n\n文档内容...",
    "metadata": {...},
    "enhanced_assets": {
        "images": {
            "count": 3,
            "files": ["img_0_0_001.png", "img_1_0_002.png"],
            "total_size_mb": 2.4
        },
        "tables": {
            "count": 2,
            "total_rows": 8,
            "total_columns": 6
        },
        "formulas": {
            "count": 5,
            "inline_count": 3,
            "block_count": 2
        },
        "output_directory": "/path/to/extracted_assets"
    }
}
```

## 📝 生成的 Markdown 结构

增强功能会在原始 Markdown 内容后添加结构化的资源章节：

```markdown
# 原始文档内容
...

## Extracted Images

![图表1](img_0_0_001.png)

*Dimensions: 800×600px*
*Source: Page 1*

## Extracted Tables

**数据统计表**

| 项目 | 数值 | 单位 |
| --- | --- | --- |
| 销售额 | 125000 | 元 |
| 利润 | 25000 | 元 |

*Table: 3 rows × 3 columns*
*Source: Page 2*

## Mathematical Formulas

爱因斯坦质能方程：$E = mc^2$

积分公式：
$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

*Source: Page 3*
```

## 🎯 使用场景

### 1. 学术论文处理
```python
# 处理包含大量数学公式的学术论文
result = await convert_pdf_to_markdown(
    pdf_source="research_paper.pdf",
    extract_formulas=True,    # 重点提取数学公式
    extract_images=True,      # 提取图表
    extract_tables=True       # 提取数据表格
)
```

### 2. 技术文档转换
```python
# 转换技术手册，保留所有图表和表格
result = await convert_pdf_to_markdown(
    pdf_source="technical_manual.pdf",
    extract_images=True,
    extract_tables=True,
    embed_images=True,        # 便于文档分享
    enhanced_options={
        "image_size": [1200, 900]  # 高清图像
    }
)
```

### 3. 数据报告处理
```python
# 处理包含大量数据表格的报告
result = await convert_pdf_to_markdown(
    pdf_source="financial_report.pdf",
    extract_images=False,     # 跳过图像
    extract_tables=True,      # 重点提取表格
    extract_formulas=False    # 跳过公式
)
```

## ⚠️ 注意事项

1. **性能考虑**：启用所有增强功能会增加处理时间，特别是图像提取
2. **存储空间**：提取的图像会占用本地存储空间
3. **文件权限**：确保输出目录具有写入权限
4. **PDF质量**：提取效果取决于原始PDF的质量和结构
5. **内存使用**：处理大型PDF文件时注意内存使用情况

## 🔧 故障排除

### 常见问题

**Q: 为什么没有提取到图像？**
A: 检查PDF是否包含矢量图像或加密的图像内容。某些PDF可能使用PyMuPDF无法识别的图像格式。

**Q: 表格格式不正确？**
A: 增强工具通过文本模式识别表格，对于复杂格式的表格可能需要手动调整。

**Q: 数学公式识别不准确？**
A: 确保PDF中的数学公式使用标准的LaTeX格式。手写公式或特殊格式的公式可能无法识别。

**Q: 图像文件很大？**
A: 可以通过 `enhanced_options` 调整图像尺寸和质量来减小文件大小。

### 调试模式

```python
# 启用详细日志记录
import logging
logging.basicConfig(level=logging.DEBUG)

# 处理PDF时会输出详细的提取信息
result = await convert_pdf_to_markdown(
    pdf_source="document.pdf",
    extract_images=True,
    extract_tables=True,
    extract_formulas=True
)
```

## 📊 性能对比

| 功能 | 处理时间 | 内存使用 | 输出大小 |
|------|----------|----------|----------|
| 仅文本 | 基准 | 基准 | 小 |
| +图像 | +30-50% | +100-200% | 大 |
| +表格 | +10-20% | +20-30% | 中 |
| +公式 | +5-15% | +10-20% | 小 |
| 全部功能 | +50-100% | +150-300% | 大 |

## 🚀 更新日志

### v2.0.0 (当前版本)
- ✨ 新增图像提取和本地存储功能
- ✨ 新增表格智能识别和Markdown转换
- ✨ 新增数学公式LaTeX格式提取
- ✨ 新增增强资源统计和管理
- ✨ 新增Base64图像嵌入选项
- ✨ 新增自定义输出目录支持
- 🔧 优化PDF处理性能和稳定性

### 计划中的功能
- 🔄 OCR文字识别支持
- 🔄 矢量图形转换
- 🔄 交互式图表生成
- 🔄 多语言文档支持