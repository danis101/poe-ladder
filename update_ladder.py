import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        # Tworzymy folder jeśli go nie ma
        if not os.path.exists('data'): 
            os.makedirs('data')
            print("Utworzono folder data/")

        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # POWTARZAMY SUKCES: Odsłanianie i sortowanie
            print("Konfiguruję widok (Depth)...")
            await page.get_by_label("Hide Delve Depth").uncheck()
            await page.wait_for_timeout(1500)
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(3000)

            # KOPIOWANIE
            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # ZAPIS LOKALNY (na maszynie bota)
            file_path = 'data/keepers-delve.tsv'
            df.to_csv(file_path, sep='\t', index=False)
            
            print(f"LOKALNY SUKCES! Plik ma {len(df)} rekordów i czeka na commit.")

        except Exception as e:
            print(f"BŁĄD: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
