import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="networkidle")
            
            # DIAGNOSTYKA: Wypiszmy co bot widzi
            inputs = await page.locator('input').count()
            print(f"Znaleziono {inputs} elementów input na stronie.")

            # KLIKNIĘCIE: Szukamy elementu, który ma obok tekst ze screena
            print("Próbuję odznaczyć 'Hide Delve Depth'...")
            # Klikamy w etykietę (label) lub tekst - to zazwyczaj przełącza checkbox
            await page.click('text="Hide Delve Depth"')
            
            # Czekamy na przeładowanie tabeli (nowe kolumny)
            await page.wait_for_timeout(5000)

            # Sprawdzamy czy pojawiła się kolumna Depth
            table_selector = 'table.ladderTable'
            table_exists = await page.locator(table_selector).count()
            
            if table_exists > 0:
                print("Tabela znaleziona. Wyciągam dane...")
                html = await page.locator(table_selector).outer_html()
                df = pd.read_html(io.StringIO(html))[0]
                
                # Zapis do pliku
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                print(f"Sukces! Kolumny w pliku: {list(df.columns)}")
            else:
                print("BŁĄD: Tabela nie znaleziona po kliknięciu.")
                await page.screenshot(path="data/final_fail.png")
                exit(1)

        except Exception as e:
            print(f"WYJĄTEK: {e}")
            await page.screenshot(path="data/exception.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
