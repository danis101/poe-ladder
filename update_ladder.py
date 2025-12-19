import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        # Ustawiamy duży ekran, żeby wszystkie elementy były widoczne
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            
            # 1. Czekamy cierpliwie na checkbox i go odznaczamy
            print("Czekam na checkbox 'Hide Delve Depth'...")
            checkbox_selector = 'input[name="hide_delve"]'
            await page.wait_for_selector(checkbox_selector, timeout=20000)
            
            print("Odznaczam 'Hide Delve Depth'...")
            await page.uncheck(checkbox_selector)
            
            # 2. Czekamy na pojawienie się kolumny Depth w tabeli
            print("Czekam na aktualizację tabeli...")
            await page.wait_for_selector('th.depth-column', timeout=15000)
            
            # 3. Sortujemy po Depth (klikamy w nagłówek)
            print("Sortuję po Depth...")
            await page.click('th.depth-column')
            await page.wait_for_timeout(2000) # Krótka pauza na przeładowanie sortowania

            # 4. Wybieramy 100 osób na stronę (dropdown na dole)
            print("Ustawiam 100 osób na stronę...")
            await page.select_option('select.view-count-select', '100')
            await page.wait_for_timeout(5000) # Dajemy stronie czas na załadowanie 100 rekordów

            # 5. Pobieramy finalną tabelę
            print("Pobieram dane...")
            table = await page.query_selector('table.ladderTable')
            html = await table.outer_html()
            
            df = pd.read_html(io.StringIO(html))[0]
            
            # Czyścimy dane (wywalamy puste kolumny)
            df = df.dropna(axis=1, how='all')
            
            # Zapisujemy do TSV
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"SUKCES! Zapisano {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_final.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
