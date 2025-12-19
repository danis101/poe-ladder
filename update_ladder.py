import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Headless=True jest wymagane na GitHubie, ale emulujemy prawdziwy ekran
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("1. Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 2. LOKALIZACJA I KLIKNIĘCIE
            print("2. Namierzam dropdown '20 per page'...")
            dropdown = page.locator('select.view-count-select')
            await dropdown.scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)
            
            # Pobieramy pozycję, żeby kliknąć dokładnie tam gdzie kursor
            box = await dropdown.bounding_box()
            if box:
                # Klik w środek dropdowna
                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                print("Kliknięto w dropdown.")
                await page.wait_for_timeout(500)
                
                # SEKWENCJA KLAWIATUROWA
                print("Wysyłam: ArrowDown, ArrowDown, Enter...")
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(300)
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(300)
                await page.keyboard.press("Enter")
            
            # 3. WERYFIKACJA (Czekamy na 100 rekordów)
            print("3. Czekam na dociągnięcie tabeli (max 20s)...")
            # Czekamy aż selektor wiersza o indeksie 50 się pojawi (to gwarantuje > 20)
            try:
                await page.wait_for_selector('table.ladderTable tbody tr:nth-child(21)', timeout=20000)
                print("Mamy to! Tabela ma więcej niż 20 osób.")
            except:
                print("Tabela nie urosła automatycznie, wymuszam odświeżenie przez JS...")
                await page.evaluate("document.querySelector('select.view-count-select').dispatchEvent(new Event('change', {bubbles: true}))")
                await page.wait_for_timeout(5000)

            # 4. SORTOWANIE (Skoro to działało wcześniej, powtarzamy)
            print("4. Sortuję po Depth...")
            # Odznaczamy 'Hide Delve'
            await page.evaluate("const cb = document.querySelector('input[name=\"hide_delve\"]'); if(cb.checked) cb.click();")
            await page.wait_for_timeout(1000)
            # Klik w nagłówek Depth
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(5000)

            # 5. ZGRYWANIE DANYCH
            print("5. Pobieram finalną tabelę...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyścimy śmieci
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Zapisujemy
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"SUKCES! Plik zapisany, rekordów: {len(df)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/keyboard_fail_debug.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
