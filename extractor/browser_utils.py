"""共享浏览器配置工具模块。"""

from selenium.webdriver.chrome.options import Options as ChromeOptions

from .config import settings


def build_chrome_options(
    *,
    headless: bool = True,
    stealth: bool = False,
    user_agent: str | None = None,
    proxy_url: str | None = None,
) -> ChromeOptions:
    """构建统一的 Chrome 浏览器选项配置。

    Args:
        headless: 是否启用无头模式
        stealth: 是否启用反检测选项
        user_agent: 自定义 User-Agent（为 None 时使用配置默认值）
        proxy_url: 代理服务器 URL
    """
    options = ChromeOptions()

    if headless:
        options.add_argument("--headless")

    # 基础稳定性选项
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    if stealth:
        # 反检测专用选项（模拟真实用户浏览器指纹）
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")

    # User-Agent 配置
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")
    else:
        options.add_argument(f"--user-agent={settings.default_user_agent}")

    # 代理配置
    if proxy_url:
        options.add_argument(f"--proxy-server={proxy_url}")
    elif settings.use_proxy and settings.proxy_url:
        options.add_argument(f"--proxy-server={settings.proxy_url}")

    return options
