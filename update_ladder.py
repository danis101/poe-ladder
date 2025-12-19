import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        # Ustawiamy bardzo wysokie okno, żeby uniknąć problemów z przykrywaniem elementów
        context = await browser.new_context(viewport={'width': 1920, 'height': 3000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. SCROLL NA SAM DÓŁ
            print("Scrolluję na dół do dropdowna...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            # 2. FIZYCZNE KLIKNIĘCIE W DROPDOWN I WYBÓR
            print("Klikam fizycznie w wybór limitu...")
            dropdown = page.locator('select.view-count-select')
            # Kliknięcie wymusza focus i aktywację skryptów PoE
            await dropdown.click()
            await dropdown.select_option(value="100")
            
            # Czekamy na przeładowanie tabeli (musi być > 20 wierszy)
            print("Czekam aż tabela 'puchnie' do 100 rekordów...")
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=20000)

            # 3. POWRÓT NA GÓRĘ I ODZNACZENIE CHECKBOXA
            print("Włączam kolumnę Depth...")
            await page.evaluate("window.scrollTo(0, 0)")
            checkbox = page.locator('input[name="hide_delve"]')
            await checkbox.set_checked(False)
            
            # 4. SORTOWANIE (Kliknięcie w nagłówek)
            print("Klikam w nagłówek Depth...")
            header = page.locator('th[data-sort="depth"]')
            await header.click()
            
            # Dajemy czas na finalne przeładowanie danych
            print("Finalne czekanie na dane...")
            await page.wait_for_timeout(5000)

            # 5. KOPIOWANIE TABELI
            print("Kopiuję tabelę...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyścimy plik z ikon i pustych kolumn
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Mamy {len(df)} rekordów w pliku.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            # Jeśli bot znowu nie trafi, screen powie nam dokładnie gdzie był kursor
            await page.screenshot(path="data/physical_click_debug.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
