"""Browser plugin — automation via Playwright.

Requires: pip install playwright && playwright install chromium
"""

from __future__ import annotations

from actions.base import BaseAction, ActionResult


class BrowserNavigateAction(BaseAction):
    action_name = "browser_navigate"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        url = command["url"]
        if dry_run:
            return ActionResult(success=True, message=f"Перейти: {url}")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_load_state("networkidle")
                title = await page.title()
                await browser.close()
            return ActionResult(success=True, message=f"Открыт: {title}", data={"url": url, "title": title})
        except ImportError:
            return ActionResult(success=False, message="playwright не установлен")
        except Exception as e:
            return ActionResult(success=False, error=str(e), message=f"Ошибка: {e}")

    def get_capability(self) -> dict:
        return {"action": "browser_navigate", "description": "Перейти на URL", "params": {"url": "string"}}


class BrowserClickAction(BaseAction):
    action_name = "browser_click"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        selector = command["selector"]
        if dry_run:
            return ActionResult(success=True, message=f"Кликнуть: {selector}")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                el = await page.wait_for_selector(selector)
                await el.click()
                await browser.close()
            return ActionResult(success=True, message=f"Клик по {selector}")
        except ImportError:
            return ActionResult(success=False, message="playwright не установлен")
        except Exception as e:
            return ActionResult(success=False, error=str(e), message=f"Ошибка: {e}")

    def get_capability(self) -> dict:
        return {"action": "browser_click", "description": "Кликнуть по элементу", "params": {"selector": "string"}}


class BrowserExtractAction(BaseAction):
    action_name = "browser_extract"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        selector = command["selector"]
        attribute = command.get("attribute", "textContent")
        if dry_run:
            return ActionResult(success=True, message=f"Извлечь: {selector}")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                el = await page.wait_for_selector(selector)
                if attribute == "textContent":
                    text = await el.text_content()
                else:
                    text = await el.get_attribute(attribute)
                await browser.close()
            return ActionResult(success=True, message=f"Извлечено", data={"text": text})
        except ImportError:
            return ActionResult(success=False, message="playwright не установлен")
        except Exception as e:
            return ActionResult(success=False, error=str(e), message=f"Ошибка: {e}")

    def get_capability(self) -> dict:
        return {"action": "browser_extract", "description": "Извлечь данные со страницы", "params": {"selector": "string", "attribute": "string"}}
