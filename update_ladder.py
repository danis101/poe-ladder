import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'):
            os.makedirs('data')

        # Uruchamiamy przeglądarkę z udawaniem prawdziwego użytkownika
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # URL z parametrem show_delve=1
        url = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100&show_delve=1"
        print(f"Otwieram: {url}")
        
        try:
            # Wchodzimy na stronę
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Czekamy chwilę na ewentualne banery
            await page.wait_for_timeout(3000)

            # 1. Próbujemy odznaczyć "Hide Delve Depth" klikając bezpośrednio w tekst obok checkboxa
            print("Próbuję odznaczyć 'Hide Delve Depth'...")
            try:
                # Szukamy tekstu i klikamy w niego (to zazwyczaj przełącza powiązany checkbox)
                await page.click('text="Hide Delve Depth"', timeout=10000)
                print("Kliknięto w tekst 'Hide Delve Depth'.")
            except:
                print("Nie udało się kliknąć w tekst, próbuję bezpośrednio w checkbox...")
                await page.locator('input[type="checkbox"]').first.click()

            # Czekamy na przeładowanie tabeli
            await page.wait_for_timeout(5000)

            # 2. Sortowanie po głębokości (kliknięcie w nagłówek 'Depth')
            print("Sortuję po Depth...")
            # Klikamy w nagłówek kolumny, który zawiera tekst 'Depth'
            depth_header = page.locator('th:has-text("Depth")').first
            await depth_header.click()
            await page.wait_for_timeout(2000)
            # Klikamy drugi raz, aby najwyższe wartości były na górze
            await depth_header.click()
            await page.wait_for_timeout(3000)

            # 3. Pobieramy tabelę
            print("Pobieram dane tabeli...")
            table = await page.query_selector('.ladderTable')
            if table:
                html = await table.outer_html()
                df = pd.read_html(io.StringIO(html))[0]
                
                # Czyszczenie danych
                df = df.dropna(axis=1, how='all')
                
                # Zapis do TSV
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                print("Sukces! Plik keepers-delve.tsv został zaktualizowany.")
            else:
                print("BŁĄD: Nie znaleziono tabeli .ladderTable")
                await page.screenshot(path="data/error_page.png")
                exit(1)

        except Exception as e:
            print(f"BŁĄD KRYTYCZNY: {e}")
            await page.screenshot(path="data/error_exception.png")
            exit(1)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
