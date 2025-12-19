import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'):
            os.makedirs('data')

        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()

        try:
            print("Wchodzę na stronę...")
            await page.goto(
                "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo",
                wait_until="networkidle"
            )

            # Odsłonięcie depth + sortowanie
            print("Konfiguruję widok (Depth)...")
            await page.get_by_label("Hide Delve Depth").uncheck()
            await page.wait_for_timeout(1000)
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(1500)

            # 🔥 KLUCZOWE: przełączenie dropdowna na TOP 100
            print("Przełączam widok na TOP 100...")

            # Klikamy dropdown (Show: 20/50/100)
            await page.locator("select").select_option("100")

            # Czekamy aż tabela się przebuduje
            await page.wait_for_timeout(3000)

            # Screenshot kontrolny
            await page.screenshot(path="data/debug_top100.png", full_page=True)

            # Zgrywanie HTML
            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            file_path = "data/keepers-delve.tsv"
            df.to_csv(file_path, sep="\t", index=False)

            print(f"SUKCES: zapisano {len(df)} rekordów")

        except Exception as e:
            print(f"BŁĄD: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
