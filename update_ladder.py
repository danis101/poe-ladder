import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): 
            os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        # Ustawiamy standardową rozdzielczość
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        try:
            print("Otwieram stronę drabinki...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            
            # Czekamy na załadowanie skryptów
            await page.wait_for_timeout(3000)

            print("Wymuszam odznaczenie 'Hide Delve Depth' przez JS...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # CZEKANIE: Sprawdzamy stan 'attached' (obecność w kodzie), a nie 'visible'
            print("Czekam na pojawienie się kolumny Depth w kodzie HTML...")
            depth_header = page.locator('th:has-text("Depth")').first
            await depth_header.wait_for(state="attached", timeout=20000)

            # Dodatkowa sekunda na wyrenderowanie danych wierszy
            await page.wait_for_timeout(2000)

            print("Pobieram tabelę...")
            # Pobieramy HTML bezpośrednio z DOM
            table_html = await page.evaluate("document.querySelector('table.ladderTable').outerHTML")
            
            if table_html:
                # Konwersja na DataFrame
                df = pd.read_html(io.StringIO(table_html))[0]
                
                # Usuwamy kolumny bez nazw (ikony itp.)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Zapisujemy do TSV
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                
                print(f"SUKCES! Plik zapisany. Znalezione kolumny: {list(df.columns)}")
            else:
                print("BŁĄD: Nie znaleziono tabeli.")
                exit(1)

        except Exception as e:
            print(f"WYJĄTEK: {e}")
            # Zapisujemy screena dla 100% pewności
            await page.screenshot(path="data/final_debug.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
