# 版本管理统一化文档

## 📋 概述

本项目已实现了版本号的统一管理机制，通过 `pyproject.toml` 作为唯一的版本号源，所有其他位置都通过动态读取的方式获取版本信息。

## 🎯 实现目标

✅ **消除版本号分散问题**：将分散在多个文件中的硬编码版本号统一管理  
✅ **简化版本更新流程**：只需更新 `pyproject.toml` 中的版本号  
✅ **确保版本一致性**：避免不同位置版本号不一致的问题  
✅ **保持运行时动态性**：版本号在运行时动态读取，无需重新编译

## 🔧 技术实现

### 核心组件

#### 1. 动态版本读取函数 (`extractor/__init__.py`)

```python
def _get_version_from_pyproject():
    """从 pyproject.toml 中动态读取版本号"""
    try:
        # 定位项目根目录下的 pyproject.toml
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 解析 version = "x.y.z" 行
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('version = "') and line.endswith('"'):
                        return line.split('"')[1]
    except Exception:
        pass

    # 备用版本号
    return "0.1.4"

__version__ = _get_version_from_pyproject()
```

#### 2. 配置系统集成 (`extractor/config.py`)

```python
def _get_dynamic_version():
    """从 pyproject.toml 动态读取版本号"""
    # 实现与 __init__.py 相同的逻辑
    ...

class DataExtractorSettings(BaseSettings):
    server_version: str = Field(default_factory=_get_dynamic_version)
    ...

# 动态版本设置逻辑
settings = DataExtractorSettings()
if not hasattr(settings, '_version_set'):
    dynamic_version = _get_dynamic_version()
    if settings.server_version != dynamic_version:
        import os
        if "DATA_EXTRACTOR_SERVER_VERSION" not in os.environ:
            os.environ["DATA_EXTRACTOR_SERVER_VERSION"] = dynamic_version
            settings = DataExtractorSettings()
    setattr(settings, '_version_set', True)
```

### 版本号获取优先级

1. **环境变量** (`DATA_EXTRACTOR_SERVER_VERSION`) - 最高优先级
2. **动态读取** - 从 `pyproject.toml` 读取
3. **备用版本** - 硬编码的备用版本号

## 📁 项目结构变更

### 修改的文件

| 文件路径                | 修改类型 | 说明                 |
| ----------------------- | -------- | -------------------- |
| `extractor/__init__.py` | ✅ 重构  | 实现动态版本读取函数 |
| `extractor/config.py`   | ✅ 重构  | 配置系统使用动态版本 |
| `.env.example`          | ✅ 更新  | 注释版本号配置说明   |

### 新增的文件

| 文件路径                    | 说明               |
| --------------------------- | ------------------ |
| `scripts/update_version.py` | 版本号批量更新脚本 |
| `VERSION_MANAGEMENT.md`     | 版本管理文档       |

## 🚀 使用方法

### 日常版本更新

1. **修改版本号**：

   ```bash
   # 只需要修改 pyproject.toml 中的版本号
   vim pyproject.toml
   # 将 version = "0.1.4" 修改为 version = "0.1.5"
   ```

2. **验证更新效果**：
   ```bash
   uv run python -c "import extractor; print(extractor.__version__)"
   uv run python -c "from extractor.config import settings; print(settings.server_version)"
   ```

### 版本号获取

在代码中获取版本号的标准方式：

```python
# 方式 1：从包中获取
import extractor
version = extractor.__version__

# 方式 2：从配置中获取
from extractor.config import settings
version = settings.server_version

# 方式 3：直接调用函数
from extractor import _get_version_from_pyproject
version = _get_version_from_pyproject()
```

### 环境变量覆盖

如果需要在特定环境中使用不同版本号：

```bash
export DATA_EXTRACTOR_SERVER_VERSION="1.0.0-dev"
uv run python -c "from extractor.config import settings; print(settings.server_version)"
# 输出: 1.0.0-dev
```

## ✅ 验证测试

### 自动化测试

项目包含完整的版本管理测试：

```python
def test_version_consistency():
    """测试版本号一致性"""
    from extractor import __version__
    from extractor.config import settings, _get_dynamic_version

    # 所有版本号应该一致
    assert __version__ == settings.server_version
    assert __version__ == _get_dynamic_version()
```

### 手动验证步骤

1. **一致性检查**：

   ```bash
   uv run python -c "
   from extractor import __version__
   from extractor.config import settings
   print(f'包版本: {__version__}')
   print(f'配置版本: {settings.server_version}')
   print('一致性:', __version__ == settings.server_version)
   "
   ```

2. **动态更新测试**：
   - 修改 `pyproject.toml` 中的版本号
   - 重新启动 Python 进程
   - 验证所有位置的版本号都已更新

## 📊 效果对比

### 实现前 ❌

- **版本号分散**：`pyproject.toml`、`__init__.py`、`config.py`、`.env.example` 等多处硬编码
- **更新复杂**：需要手动修改多个文件
- **容易出错**：版本号不一致导致的部署问题
- **维护困难**：新增版本引用位置需要记住更新

### 实现后 ✅

- **统一管理**：`pyproject.toml` 作为唯一版本源
- **一键更新**：只需修改一个文件
- **自动同步**：所有位置自动获取最新版本
- **易于维护**：新增版本引用自动包含动态读取

## 🔄 最佳实践

### 版本发布流程

1. **更新版本号**：修改 `pyproject.toml` 中的 `version` 字段
2. **更新变更日志**：在 `CHANGELOG.md` 中记录变更
3. **运行测试**：确保版本管理功能正常
4. **提交变更**：
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore(release): bump version to v0.1.5"
   git tag -a v0.1.5 -m "Release version 0.1.5"
   ```

### 开发环境配置

如果需要在开发环境使用自定义版本标识：

```bash
# 设置开发版本标识
export DATA_EXTRACTOR_SERVER_VERSION="0.1.4-dev.$(git rev-parse --short HEAD)"
```

### CI/CD 集成

在持续集成中验证版本一致性：

```yaml
- name: Verify version consistency
  run: |
    VERSION=$(uv run python -c "import extractor; print(extractor.__version__)")
    CONFIG_VERSION=$(uv run python -c "from extractor.config import settings; print(settings.server_version)")
    if [ "$VERSION" != "$CONFIG_VERSION" ]; then
      echo "Version mismatch: $VERSION != $CONFIG_VERSION"
      exit 1
    fi
```

## 🛠️ 故障排除

### 常见问题

#### 1. 版本号读取失败

**症状**：返回备用版本号而不是 pyproject.toml 中的版本
**解决方案**：

- 检查 `pyproject.toml` 文件是否存在
- 确认版本号格式为 `version = "x.y.z"`
- 验证文件编码为 UTF-8

#### 2. 环境变量干扰

**症状**：版本号与 pyproject.toml 不一致
**解决方案**：

```bash
unset DATA_EXTRACTOR_SERVER_VERSION
```

#### 3. 导入循环问题

**症状**：模块导入错误
**解决方案**：

- 重启 Python 进程清理导入缓存
- 确保版本读取函数没有循环依赖

### 调试方法

```python
# 调试版本读取过程
from extractor.config import _get_dynamic_version
import os
from pathlib import Path

print(f"当前工作目录: {Path.cwd()}")
print(f"配置文件路径: {Path(__file__).parent.parent}")
print(f"动态版本结果: {_get_dynamic_version()}")
print(f"环境变量: {os.environ.get('DATA_EXTRACTOR_SERVER_VERSION', 'Not set')}")
```

## 📝 总结

版本管理统一化的实现大大简化了项目的版本控制流程，提高了开发效率和代码质量。通过单一源头的版本管理，确保了整个项目的版本一致性，减少了人为错误的可能性。

**关键优势：**

- 🎯 **单一源头**：pyproject.toml 作为唯一版本源
- 🚀 **自动同步**：所有引用位置自动更新
- 🛡️ **错误预防**：避免版本不一致问题
- 📈 **效率提升**：简化版本更新流程
- 🔧 **灵活性**：支持环境变量覆盖
