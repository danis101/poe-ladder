import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            await page.wait_for_timeout(5000)

            # Odznaczamy Delve przez JS - to na screenie nadal było zaznaczone!
            print("Odznaczam 'Hide Delve Depth'...")
            await page.evaluate("document.querySelector('input[name=\"hide_delve\"]').checked = false")
            await page.evaluate("document.querySelector('input[name=\"hide_delve\"]').dispatchEvent(new Event('change'))")
            
            # Czekamy aż tabela się przeładuje po odznaczeniu
            await page.wait_for_timeout(5000)

            # BIERZEMY TABELĘ (po prostu pierwszą lepszą z brzegu)
            print("Szukam jakiejkolwiek tabeli...")
            table_content = await page.evaluate("document.querySelector('table').outerHTML")
            
            if table_content:
                df = pd.read_html(io.StringIO(table_content))[0]
                # Zapisujemy
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                print("SUKCES! Tabela znaleziona i zapisana.")
            else:
                print("Nadal nie widzę tabeli w kodzie...")
                exit(1)

        except Exception as e:
            print(f"Błąd: {e}")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
