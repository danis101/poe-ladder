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
            # Wchodzimy na bazowy URL
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. Zmiana limitu na 100 przez dropdown (najpewniejsza metoda)
            print("Ustawiam limit na 100 rekordów...")
            await page.select_option('select.view-count-select', '100')
            
            # 2. Odznaczamy 'Hide Delve Depth' przez JS
            print("Wymuszam wyświetlenie Depth...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # 3. Wymuszamy sortowanie po Depth przez JS (żeby nie było problemu z "widocznością" nagłówka)
            print("Sortuję po Depth...")
            await page.evaluate("""
                const depthHeader = document.querySelector('th[data-sort="depth"]');
                if (depthHeader) {
                    depthHeader.click();
                }
            """)

            # 4. KLUCZOWE: Czekamy, aż tabela będzie miała więcej niż 20 wierszy
            print("Czekam na załadowanie pełnej listy 100 rekordów...")
            await page.wait_for_function("""
                () => document.querySelectorAll('table.ladderTable tbody tr').length > 20
            """, timeout=20000)
            
            # Dodatkowa chwila na stabilizację danych
            await page.wait_for_timeout(3000)

            # 5. Pobieramy dane
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyszczenie nagłówków
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Zapis do TSV
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Pobrano {len(df)} wierszy.")
            print(f"Nagłówki: {list(df.columns)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/debug_limit_error.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
