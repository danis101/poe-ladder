import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        os.makedirs("data", exist_ok=True)

        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()

        try:
            print("Wchodzę na stronę...")
            await page.goto(
                "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo",
                wait_until="networkidle"
            )

            print("Odsłaniam Depth + sortuję...")
            await page.get_by_label("Hide Delve Depth").uncheck()
            await page.wait_for_timeout(1000)
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(1500)

            # ==========================
            # 🔥 KLUCZ: TOP 100
            # ==========================
            print("Przełączam TOP 20 → TOP 100")

            # klik w aktualny limit (20)
            await page.locator("text=20").first.click()
            await page.wait_for_timeout(500)

            # klik w 100
            await page.locator("text=100").first.click()

            # czekamy aż tabela faktycznie się przebuduje
            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=10000
            )

            # Screenshot KONTROLNY
            await page.screenshot(
                path="data/debug_top100.png",
                full_page=True
            )

            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)

            print(f"SUKCES: zapisano {len(df)} rekordów")

        except Exception as e:
            print("BŁĄD:", e)
            await page.screenshot(path="data/error.png", full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
