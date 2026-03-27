"""PDF 子系统共享的延迟导入辅助。"""


def import_fitz():
    """延迟导入 PyMuPDF (fitz)。"""
    try:
        import fitz

        return fitz
    except ImportError as e:
        raise ImportError(f"PyMuPDF (fitz) is required for PDF processing: {e}")


def import_pypdf():
    """延迟导入 pypdf。"""
    try:
        import pypdf

        return pypdf
    except ImportError as e:
        raise ImportError(f"pypdf is required for PDF processing: {e}")
