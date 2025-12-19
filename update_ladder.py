import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io

async def run():
    async with async_playwright() as p:
        # Uruchamiamy przeglądarkę
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Wejście na stronę
        print("Wchodzę na stronę PoE...")
        await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", timeout=60000)
        
        # 2. Odznaczenie "Hide Delve Depth"
        print("Odznaczam 'Hide Delve Depth'...")
        await page.uncheck('input[name="hide_delve"]')
        await page.wait_for_timeout(2000)

        # 3. Zmiana na 100 osób na stronę
        print("Zmieniam widok na 100 osób...")
        # Wybieramy wartość 100 z dropdowna na dole
        await page.select_option('select.view-count-select', '100')
        await page.wait_for_timeout(3000)

        # 4. Sortowanie po Depth
        # Klikamy w nagłówek "Depth", aby wymusić sortowanie po głębokości
        print("Sortuję po Depth...")
        await page.click('th.depth-column') 
        await page.wait_for_timeout(3000)
        
        # Pobieramy tabelę po wszystkich zmianach
        print("Pobieram dane...")
        table_element = await page.query_selector('.ladderTable')
        table_html = await table_element.inner_html()
        
        # Parsowanie HTML do DataFrame
        df = pd.read_html(io.StringIO(f"<table>{table_html}</table>"))[0]
        
        # Czyścimy puste kolumny
        df = df.dropna(axis=1, how='all')
        
        # Zapisujemy do pliku
        df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
        print("Gotowe! Plik zapisany w data/keepers-delve.tsv")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
