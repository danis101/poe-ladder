import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        browser = await p.chromium.launch(headless=True)
        # Ustawiamy bardzo wysoki viewport, żeby wymusić renderowanie
        context = await browser.new_context(viewport={'width': 1280, 'height': 3000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. Fizyczny scroll kółkiem myszy na sam dół
            print("Scrolluję na dół...")
            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(3000)
            
            # 2. ROBIMY SCREENA CAŁEJ STRONY
            print("Robię pełny zrzut ekranu do debugowania...")
            await page.screenshot(path="data/debug_full_page.png", full_page=True)

            # 3. Próba znalezienia i kliknięcia dropdownu (nawet jeśli bot twierdzi że nie widzi)
            print("Próbuję wymusić limit 100 przez JS...")
            await page.evaluate("""
                const sel = document.querySelector('select.view-count-select');
                if (sel) {
                    sel.value = '100';
                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log('JS: Zmieniono wartość na 100');
                } else {
                    console.log('JS: Nie znaleziono dropdownu!');
                }
            """)
            
            # Czekamy chwilę na reakcję strony
            await page.wait_for_timeout(5000)
            
            # Sprawdzamy ile mamy wierszy
            rows = await page.locator('table.ladderTable tbody tr').count()
            print(f"Liczba wykrytych wierszy po zmianie: {rows}")

            # 4. Jeśli mamy dane, zapisujemy
            if rows > 0:
                content = await page.content()
                dfs = pd.read_html(io.StringIO(content))
                df = next(d for d in dfs if 'Rank' in d.columns)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                print(f"Zapisano plik ({len(df)} wierszy).")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_final.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
