import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("1. Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 2. PRÓBA KLIKNIĘCIA PRZEZ SELEKTOR OPCJI
            print("2. Szukam i wymuszam wybór 100 per page...")
            # Zamiast klikać w select, próbujemy namierzyć samą opcję 100
            try:
                # Scrollujemy do dropdowna
                await page.locator('select.view-count-select').scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                
                # Używamy akcji select_option z parametrem force=True
                # To najmocniejsza komenda Playwright do obsługi dropdownów
                await page.locator('select.view-count-select').select_option(value="100")
                
                # Dodatkowo 'budzimy' stronę ręcznie wysyłając event zmiany
                await page.evaluate("""
                    const el = document.querySelector('select.view-count-select');
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """)
            except Exception as e:
                print(f"Problem z wyborem: {e}")

            # 3. WERYFIKACJA (Czekamy na Rank 21)
            print("3. Czekam na dociągnięcie tabeli...")
            # Używamy selektora, który szuka 21. wiersza w tabeli
            try:
                await page.wait_for_selector('tr:nth-child(21)', timeout=15000)
                print("Sukces! Widzę więcej niż 20 rekordów.")
            except:
                print("TIMEOUT: Tabela nadal ma 20 wierszy. Robię screena do analizy.")
                await page.screenshot(path="data/still_20_error.png", full_page=True)

            # 4. SORTOWANIE
            print("4. Włączam Depth i klikam w nagłówek...")
            await page.evaluate("document.querySelector('input[name=\"hide_delve\"]').checked = false; document.querySelector('input[name=\"hide_delve\"]').dispatchEvent(new Event('change', {bubbles:true}));")
            await page.wait_for_timeout(1000)
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(5000)

            # 5. POBIERANIE DANYCH
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"Zapisano {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD KRYTYCZNY: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
