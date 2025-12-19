import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Ustawiamy User-Agent, żeby strona nie traktowała nas jak "twardego" bota
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 2000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("1. Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # --- KROK A: DROPDOWN ---
            print("2. Próba ustawienia 100 osób...")
            dropdown = page.locator('select.view-count-select')
            await dropdown.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            
            # Klikamy, żeby złapać focus (niebieska obwódka)
            await dropdown.focus()
            # Wybieramy opcję
            await dropdown.select_option("100")
            # Wysyłamy ręczny sygnał zmiany
            await page.evaluate("document.querySelector('select.view-count-select').dispatchEvent(new Event('change', {bubbles: true}))")
            
            # CZEKAMY: To jest kluczowe. Nie robimy nic, dopóki nie zobaczymy Rank 21
            print("Czekam na dociągnięcie 100 rekordów (strażnik)...")
            try:
                await page.wait_for_selector('tr:nth-child(21)', timeout=15000)
                print("Sukces: Tabela ma 100 rekordów.")
            except:
                print("OSTRZEŻENIE: Tabela nadal krótka. Spróbujemy pobrać to co jest.")

            # --- KROK B: SORTOWANIE (Dopiero teraz!) ---
            print("3. Ustawianie widoku Depth...")
            # Odznaczamy checkbox przez kliknięcie w label (bezpieczniejsze)
            await page.get_by_text("Hide Delve Depth").click()
            await page.wait_for_timeout(2000)
            
            print("4. Klikam w nagłówek Depth do sortowania...")
            # Klikamy w nagłówek i czekamy na zmianę w URL lub przeładowanie
            await page.locator('th[data-sort="depth"]').click()
            
            # Finalne czekanie na ułożenie danych
            print("Czekam na sortowanie...")
            await page.wait_for_timeout(5000)

            # --- KROK C: ZGRYWANIE ---
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"ZAPISANO: {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/step_by_step_fail.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
