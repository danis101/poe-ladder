import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            # Wchodzimy od razu z parametrem limit=100 w URL - to pewniejsze niż klikanie
            url = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100"
            await page.goto(url, wait_until="networkidle")
            
            # 1. Odznaczamy 'Hide Delve Depth' przez JS
            print("Wymuszam wyświetlenie Depth...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy na obecność kolumny w kodzie
            await page.wait_for_selector('th[data-sort="depth"]', state="attached", timeout=15000)

            # 2. WYMUSZAMY SORTOWANIE PRZEZ JS
            # Zamiast klikać, wywołujemy skrypt strony odpowiedzialny za sortowanie
            print("Wymuszam sortowanie po Depth...")
            await page.evaluate("""
                const depthHeader = document.querySelector('th[data-sort="depth"]');
                if (depthHeader) {
                    depthHeader.click(); // JS-owy click nie potrzebuje widoczności elementu
                }
            """)
            
            # Czekamy na przeładowanie danych po sortowaniu
            print("Czekam na stabilizację danych...")
            await page.wait_for_timeout(5000)

            # 3. POBIERAMY DANE
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyszczenie nagłówków z ikon i pustych kolumn
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Zapisujemy do TSV
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Pobrano {len(df)} wierszy.")
            print(f"Kolumny: {list(df.columns)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/debug_click_error.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
