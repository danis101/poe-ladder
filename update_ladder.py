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
            
            # 1. Odznaczamy 'Hide Delve Depth'
            print("Odznaczam 'Hide Delve Depth'...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy na pojawienie się kolumny Depth
            await page.wait_for_selector('th.sortable[data-sort="depth"]', state="attached")
            await page.wait_for_timeout(2000)

            # 2. KLIKAMY W NAGŁÓWEK DEPTH (Sortowanie)
            print("Klikam w nagłówek Depth, aby posortować...")
            # Klikamy dwukrotnie lub upewniamy się, że sortuje malejąco (od najgłębszego)
            await page.click('th.sortable[data-sort="depth"]')
            await page.wait_for_timeout(3000)

            # 3. ZMIENIAMY LIMIT NA 100
            print("Zmieniam limit na 100 osób...")
            # Selektor dla dropdownu z wyborem liczby osób
            await page.select_option('select.view-count-select', '100')
            
            # Czekamy na załadowanie 100 rekordów
            print("Czekam na załadowanie 100 rekordów...")
            await page.wait_for_timeout(5000)

            # 4. POBIERAMY FINALNĄ TABELĘ
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyszczenie i zapis
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Zapisano {len(df)} rekordów. Kolumny: {list(df.columns)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_final_steps.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
