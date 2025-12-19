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
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        try:
            print("Otwieram stronę drabinki...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            await page.wait_for_timeout(2000)

            print("Odznaczam 'Hide Delve Depth'...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy aż kolumna Depth faktycznie się pojawi i zostanie w kodzie
            print("Czekam na stabilizację tabeli...")
            await page.wait_for_selector('th:has-text("Depth")', state="attached", timeout=20000)
            # Kluczowe: czekamy chwilę, aż dane wierszy się dociągną pod nagłówek
            await page.wait_for_timeout(3000)

            # Pobieramy CAŁY kod HTML strony zamiast konkretnego elementu
            # To eliminuje błąd "null" przy outerHTML
            content = await page.content()
            
            print("Konwertuję dane...")
            # Szukamy tabeli w całym kodzie strony
            dfs = pd.read_html(io.StringIO(content))
            
            # Wybieramy tabelę, która ma kolumnę 'Rank' (to ta właściwa)
            ladder_df = next(df for df in dfs if 'Rank' in df.columns)
            
            # Czyścimy zbędne kolumny (ikony/puste)
            ladder_df = ladder_df.loc[:, ~ladder_df.columns.str.contains('^Unnamed')]
            
            # Zapisujemy do TSV
            ladder_df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Zapisano kolumny: {list(ladder_df.columns)}")

        except Exception as e:
            print(f"WYJĄTEK: {e}")
            await page.screenshot(path="data/final_debug.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
