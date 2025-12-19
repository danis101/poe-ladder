import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Wejście na stronę
        await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100")
        
        # Odznaczamy checkbox "Hide Delve Depth"
        # Używamy selektora tekstu, bo to najpewniejsze na stronie PoE
        await page.uncheck('text="Hide Delve Depth"')
        
        # Czekamy na odświeżenie tabeli
        await page.wait_for_timeout(3000)

        # Pobieramy tabelę
        table_element = await page.query_selector('.ladderTable')
        table_html = await table_element.inner_html()
        
        # Parsowanie do TSV
        df = pd.read_html(io.StringIO(f"<table>{table_html}</table>"))[0]
        
        # Czyścimy dane (usuwamy puste kolumny jeśli są)
        df = df.dropna(axis=1, how='all')
        
        # Zapis do folderu data/
        df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
