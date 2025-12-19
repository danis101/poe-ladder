import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2500})
        page = await context.new_page()
        
        try:
            print("1. Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 2. Próba zmiany limitu przez JS
            print("2. Wymuszam 100 per page...")
            await page.evaluate("""
                const sel = document.querySelector('select.view-count-select');
                if(sel) {
                    sel.value = '100';
                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy aż strona zareaguje
            print("3. Czekam na przeładowanie (7s)...")
            await page.wait_for_timeout(7000)
            
            # 4. SCREEN PO ZMIANIE (To pokaże prawdę)
            print("4. Robię screena po 'zmianie' limitu...")
            await page.screenshot(path="data/debug_after_limit_change.png", full_page=True)

            # 5. Sprawdzamy stan tabeli w kodzie
            rows_count = await page.locator('table.ladderTable tbody tr').count()
            print(f"Liczba wierszy wykryta przez bota: {rows_count}")

            # 6. Pobieramy i zapisujemy to co jest
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"Zapisano plik. Liczba rekordów: {len(df)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_capture.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
