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
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. WYMUSZAMY LIMIT 100 (Bez celowania myszką)
            print("Wymuszam 100 per page...")
            await page.evaluate("""
                const select = document.querySelector('select.view-count-select');
                if (select) {
                    select.value = '100';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy aż strona faktycznie przemieli te 100 wierszy
            print("Czekam na dociągnięcie wierszy (do 15s)...")
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=15000)

            # 2. ODZNACZAMY CHECKBOX (Bez celowania myszką)
            print("Włączam kolumnę Depth...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy na kolumnę w kodzie
            await page.wait_for_selector('th[data-sort="depth"]', state="attached")

            # 3. SORTUJEMY (Bez celowania myszką)
            print("Wymuszam sortowanie po Depth...")
            await page.evaluate("""
                const depthHeader = document.querySelector('th[data-sort="depth"]');
                if (depthHeader) {
                    depthHeader.click(); // To jest JS-owy click, zawsze trafia
                }
            """)
            
            # Czekamy na przeładowanie po sortowaniu
            print("Finalna stabilizacja...")
            await page.wait_for_timeout(5000)

            # 4. POBIERAMY DANE
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Usuwamy puste kolumny (ikony)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Zapisujemy do TSV
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Plik ma {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/debug_js_force.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
