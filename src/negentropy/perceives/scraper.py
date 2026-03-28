"""向后兼容 shim，规范路径：scraping/engine.py。

通过 sys.modules 别名实现完全透明代理——mock.patch 在新旧路径上行为一致。
"""

import sys
from .scraping import engine as _canonical  # noqa: F401

sys.modules[__name__] = _canonical
