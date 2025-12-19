import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        # Tworzymy folder data, jeśli nie istnieje
        if not os.path.exists('data'): 
            os.makedirs('data')
        
        # Uruchamiamy przeglądarkę
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę drabinki...")
            # Wchodzimy na stronę i czekamy na załadowanie podstawowej struktury
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load")
            
            # Krótka pauza na załadowanie skryptów PoE
            await page.wait_for_timeout(2000)

            # WYMUSZENIE: Odznaczamy checkbox 'Hide Delve Depth' bezpośrednio przez JavaScript
            print("Odznaczam 'Hide Delve Depth' przez JS...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # CZEKANIE: To jest kluczowy moment - czekamy aż w nagłówku tabeli pojawi się tekst 'Depth'
            # timeout 15s jest bezpieczny, strona zazwyczaj reaguje w 1-2s
            print("Czekam na dociągnięcie kolumn Delve...")
            await page.wait_for_selector('th:has-text("Depth")', timeout=15000)

            # POBIERANIE: Skoro 'Depth' już jest w DOM, pobieramy całą tabelę
            print("Pobieram tabelę z danymi...")
            table_html = await page.evaluate("document.querySelector('table.ladderTable').outerHTML")
            
            if table_html:
                # Używamy Pandas do szybkiej konwersji HTML na DataFrame
                df = pd.read_html(io.StringIO(table_html))[0]
                
                # Czyścimy puste kolumny (np. te z ikonami, które Pandas czyta jako puste)
                df = df.dropna(axis=1, how='all')
                
                # Zapisujemy do TSV (lepszy format dla danych z PoE niż zwykły CSV)
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                
                print(f"SUKCES! Zapisano {len(df)} wierszy.")
                print(f"Nagłówki w pliku: {list(df.columns)}")
            else:
                print("BŁĄD: Tabela nie została znaleziona w kodzie strony.")
                exit(1)

        except Exception as e:
            print(f"WYJĄTEK podczas pracy bota: {e}")
            # W razie błędu robimy zrzut ekranu, żeby wiedzieć co widział bot
            await page.screenshot(path="data/final_error_debug.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
