import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os
import random

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Uruchomienie bez zbędnych dodatków, aby przyspieszyć start
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # Szybsze ładowanie (czekamy tylko do momentu interaktywności)
            await page.goto(URL, wait_until="commit", timeout=60000)
            await asyncio.sleep(random.uniform(2, 4)) 

            # Konfiguracja tabeli
            try:
                await page.get_by_label("Hide Delve Depth").uncheck(timeout=2000)
            except:
                await page.click("text=Hide Delve Depth", timeout=2000)
            
            await page.click('th[data-sort="depth"]')
            
            # Zmiana na 100
            selector_100 = "select.perPageOptions"
            await page.select_option(selector_100, "100")
            
            # Szybka kontrola obecności danych (co 0.5s zamiast 2s)
            for _ in range(20):
                await asyncio.sleep(0.5)
                count = await page.locator("table.ladderTable tbody tr").count()
                if count >= 100:
                    break

            content = await page.content()
            # Parsowanie tylko niezbędnej tabeli
            df = pd.read_html(io.StringIO(content))[0]
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            
            output_file = os.path.join(data_dir, "keepers-delve.tsv")
            df.to_csv(output_file, sep="\t", index=False)
            print(f"Pobrano {len(df)} rekordów.")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
