import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io

async def run():
    async with async_playwright() as p:
        # Uruchomienie przeglądarki
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Wejście na stronę
        url = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100"
        await page.goto(url)
        
        # Czekamy na załadowanie tabeli
        await page.wait_for_selector('.ladderTable')

        # KLIKNIĘCIE: Odznaczamy checkbox "Hide Delve Depth"
        # Na stronie PoE ten checkbox często ma id lub jest powiązany z tekstem
        # Szukamy checkboxa, który jest zaznaczony (checked) i go klikamy
        await page.click('input[name="hide_delve"]') 
        
        # Czekamy chwilę na przeładowanie danych przez skrypt PoE
        await page.wait_for_timeout(2000)

        # Pobieramy kod HTML tabeli po zmianach
        table_html = await page.inner_html('.ladderTable')
        
        # Konwertujemy HTML do DataFrame (pandas)
        df = pd.read_html(io.StringIO(f"<table>{table_html}</table>"))[0]
        
        # Zapisujemy do pliku TSV
        df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
