import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        # Udajemy duży ekran, żeby wszystko się zmieściło
        context = await browser.new_context(viewport={'width': 1920, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. Wymuszamy limit 100 per page bez względu na to, gdzie jest dropdown
            print("Wymuszam limit 100 per page przez JS...")
            await page.evaluate("""
                const select = document.querySelector('select.view-count-select');
                if (select) {
                    select.value = '100';
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Dajemy stronie czas na przeładowanie tabeli do 100 wierszy
            print("Czekam 10 sekund na dociągnięcie 100 rekordów...")
            await page.wait_for_timeout(10000)

            # 2. Włączamy kolumnę Depth
            print("Włączam kolumnę Depth...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            await page.wait_for_timeout(3000)

            # 3. Sortujemy po Depth (klikamy w nagłówek)
            print("Sortuję po głębokości...")
            await page.evaluate("document.querySelector('th[data-sort=\"depth\"]').click()")
            
            # Finalne czekanie na odświeżenie sortowania
            print("Finalna stabilizacja danych...")
            await page.wait_for_timeout(5000)

            # 4. Pobieramy dane z całego kodu strony
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyścimy śmieciowe kolumny i zapisujemy
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Zapisano {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            # Zrzut ekranu zawsze pomoże nam w razie czego
            await page.screenshot(path="data/final_debug_error.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
