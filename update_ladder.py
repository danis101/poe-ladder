import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Standardowe ustawienia, bez udziwnień
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            
            # Czekamy aż strona PoE załaduje swoje skrypty JS
            await page.wait_for_timeout(3000)

            # WYMUSZENIE: Skoro widzimy to na screenie, to ten element ISTNIEJE.
            # Używamy JavaScriptu, żeby go odznaczyć, bo JS nie obchodzi "klikalność" Playwrighta.
            print("Wymuszam zmianę checkboxa...")
            await page.evaluate("""
                const checkbox = document.querySelector('input[name="hide_delve"]');
                if (checkbox) {
                    checkbox.checked = false;
                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Dajemy tabeli czas na dociągnięcie kolumny Depth
            await page.wait_for_timeout(5000)

            # Pobieramy tabelę
            print("Próbuję odczytać tabelę...")
            table = await page.query_selector('table.ladderTable')
            if table:
                html = await table.outer_html()
                df = pd.read_html(io.StringIO(html))[0]
                
                # Zapisujemy do pliku
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                
                print(f"Sukces! Znalezione kolumny: {list(df.columns)}")
                if 'Depth' in df.columns or any('Depth' in str(c) for c in df.columns):
                    print("Kolumna Depth jest obecna!")
            else:
                print("Nie znaleziono tabeli po odznaczeniu checkboxa.")
                exit(1)

        except Exception as e:
            print(f"Błąd: {e}")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
