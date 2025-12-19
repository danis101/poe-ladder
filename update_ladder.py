import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Uruchamiamy przeglądarkę
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("1. Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 2. SCROLL I KLIKNIĘCIE (Tak jak prosiłeś)
            print("2. Szukam dropdowna na dole...")
            # Czekamy aż tekst "per page" pojawi się na ekranie
            dropdown_trigger = page.get_by_text("per page")
            await dropdown_trigger.scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)

            # 3. FIZYCZNE KLIKNIĘCIE I WYBÓR 100
            print("3. Klikam w dropdown i wybieram 100...")
            # Klikamy fizycznie w element, który widzieliśmy na Twoim screenie
            await page.select_option('select.view-count-select', label="100 per page")
            
            # 4. STRAŻNIK (Czekamy na wynik kliknięcia)
            print("4. Czekam aż tabela dociągnie 100 osób...")
            # Jeśli kliknięcie zadziałało, tabela musi mieć więcej niż 20 wierszy
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=30000)

            # 5. SORTOWANIE (Dokładnie tak samo jak kliknięcie w dropdown)
            print("5. Klikam w sortowanie Depth...")
            # Najpierw odznaczamy checkbox
            await page.get_by_label("Hide Delve Depth").uncheck()
            # Klikamy w nagłówek Depth
            await page.locator('th[data-sort="depth"]').click()
            
            await page.wait_for_timeout(5000)

            # 6. POBIERANIE I ZAPIS
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"SUKCES! Zapisano {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/final_debug.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
