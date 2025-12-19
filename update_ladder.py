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
            
            # KROK 1: ODSŁANIANIE DEPTH (To co działało)
            print("2. Odsłaniam kolumnę Depth...")
            await page.get_by_label("Hide Delve Depth").uncheck()
            await page.wait_for_timeout(1000)
            
            # KROK 2: SORTOWANIE (To też działało)
            print("3. Sortuję po Depth...")
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(2000)

            # KROK 3: WYBÓR 100 OSÓB (Tutaj dodajemy 'Enter' dla pewności)
            print("4. Próbuję przełączyć na 100 per page...")
            dropdown = page.locator('select.view-count-select')
            await dropdown.scroll_into_view_if_needed()
            
            # Wybieramy 100 i symulujemy Enter, żeby strona "załapała" zmianę
            await dropdown.select_option(value="100")
            await dropdown.press("Enter") 
            
            # Czekamy aż tabela 'puchnie' (strażnik 20 rekordów)
            print("5. Czekam na załadowanie danych...")
            await page.wait_for_timeout(7000) 

            # KROK 4: KOPIOWANIE TABELI (To co działało)
            print("6. Kopiuję tabelę...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyścimy kolumny z obrazkami
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # ZAPIS
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"SUKCES! Zapisano {len(df)} rekordów.")

            # Dodatkowy screen, żebyśmy wiedzieli co finalnie bot widział
            await page.screenshot(path="data/final_view.png", full_page=True)

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
