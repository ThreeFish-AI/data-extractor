"""Form interaction MCP tools."""

import logging
from typing import Annotated, Any, Dict, Optional

from pydantic import Field

from ..config import settings
from ..form_handler import FormHandler
from ..rate_limiter import rate_limiter
from ..schemas import ScrapeResponse
from ..url_utils import URLValidator
from ._registry import app, ToolTimer
from ..validation_trace import trace_event

logger = logging.getLogger(__name__)


@app.tool()
async def fill_and_submit_form(
    url: Annotated[
        str,
        Field(
            ...,
            description="包含表单的网页 URL，必须包含协议前缀（http:// 或 https://）",
        ),
    ],
    form_data: Annotated[
        Dict[str, Any],
        Field(
            ...,
            description="""表单字段数据，格式为{"选择器": "值"}，支持各种表单元素。
                示例：{"#username": "admin", "input[name=password]": "secret", "select[name=country]": "US", "input[type=checkbox]": True}""",
        ),
    ],
    submit: Annotated[bool, Field(default=False, description="是否提交表单")],
    submit_button_selector: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""提交按钮的CSS选择器，如未指定则尝试自动查找。
                示例："button[type=submit]"、"#submit-btn\"""",
        ),
    ],
    method: Annotated[
        str,
        Field(
            default="selenium",
            description="""自动化方法选择，可选值：
                "selenium"（使用Selenium WebDriver）、
                "playwright"（使用Playwright浏览器自动化）""",
        ),
    ],
    wait_for_element: Annotated[
        Optional[str],
        Field(
            default=None,
            description="""表单填写前等待加载的元素CSS选择器。
                示例：".form-container"、"#login-form\"""",
        ),
    ],
) -> ScrapeResponse:
    """
    Fill and optionally submit a form on a webpage.

    This tool can handle various form elements including:
    - Text inputs
    - Checkboxes and radio buttons
    - Dropdown selects
    - File uploads
    - Form submission

    Useful for interacting with search forms, contact forms, login forms, etc.

    Returns:
        ScrapeResponse object containing success status, form interaction results, and optional submission response.
        Supports complex form automation workflows.
    """
    method_key = f"form_{method}"
    timer = ToolTimer(url, method_key)
    try:
        # Validate inputs
        if not URLValidator.is_valid_url(url):
            return ScrapeResponse(
                success=False, url=url, method=method, error="Invalid URL format",
            )

        if method not in ["selenium", "playwright"]:
            return ScrapeResponse(
                success=False, url=url, method=method,
                error="Method must be one of: selenium, playwright",
            )

        logger.info(f"Form interaction for: {url}")
        trace_event(
            "fill_and_submit_form",
            "interaction_started",
            url=url,
            method=method,
            submit=submit,
            field_count=len(form_data),
        )

        # Apply rate limiting
        await rate_limiter.wait()
        trace_event("fill_and_submit_form", "rate_limit_wait_completed")

        # Setup browser based on method
        if method == "selenium":
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions

            options = ChromeOptions()
            if settings.browser_headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            try:
                driver.get(url)

                # Wait for element if specified
                if wait_for_element:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.support.ui import WebDriverWait

                    WebDriverWait(driver, settings.browser_timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, wait_for_element)
                        )
                    )

                # Fill and submit form
                form_handler = FormHandler(driver)
                result = await form_handler.fill_form(
                    form_data=form_data,
                    submit=submit,
                    submit_button_selector=submit_button_selector,
                )

                # Get final page info
                final_url = driver.current_url
                final_title = driver.title
                trace_event(
                    "fill_and_submit_form",
                    "selenium_form_completed",
                    success=bool(result.get("success")),
                    final_url=final_url,
                )

            finally:
                driver.quit()

        elif method == "playwright":
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(
                    headless=settings.browser_headless
                )
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(url, timeout=60000)

                # Wait for element if specified
                if wait_for_element:
                    await page.wait_for_selector(
                        wait_for_element,
                        timeout=settings.browser_timeout * 1000,
                    )

                # Fill and submit form
                form_handler = FormHandler(page)
                result = await form_handler.fill_form(
                    form_data=form_data,
                    submit=submit,
                    submit_button_selector=submit_button_selector,
                )

                # Get final page info
                final_url = page.url
                final_title = await page.title()
                trace_event(
                    "fill_and_submit_form",
                    "playwright_form_completed",
                    success=bool(result.get("success")),
                    final_url=final_url,
                )

            finally:
                await browser.close()
                await playwright.stop()

        if result.get("success"):
            timer.record_success()
            return ScrapeResponse(
                success=True, url=url, method=method_key,
                data={
                    "form_results": result,
                    "final_url": final_url,
                    "final_title": final_title,
                    "original_url": url,
                },
            )
        else:
            return ScrapeResponse(
                success=False, url=url, method=method_key,
                error=timer.record_failure(Exception(result.get("error", "Form interaction failed"))),
            )

    except Exception as e:
        trace_event("fill_and_submit_form", "interaction_failed", error=str(e))
        return ScrapeResponse(
            success=False, url=url, method=method_key,
            error=timer.record_failure(e),
        )
