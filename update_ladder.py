import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'):
            os.makedirs('data')

        # Uruchamiamy przeglądarkę z polskim/europejskim User Agentem
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        url = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100"
        print(f"Otwieram: {url}")
        
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            
            # Akceptujemy ciasteczka jeśli wyskoczą (częsty powód błędu na serwerach)
            cookie_btn = await page.query_selector('button:has-text("Accept"), .btn-accept')
            if cookie_btn: await cookie_btn.click()

            # 1. Odznaczamy Hide Delve (używając ID lub nazwy)
            print("Klikam checkbox...")
            await page.locator('input[name="hide_delve"]').evaluate("node => node.click()")
            await page.wait_for_timeout(2000)

            # 2. Sortujemy po głębokości
            print("Sortuję tabelę...")
            await page.locator('th.depth-column').click()
            await page.wait_for_timeout(2000)
            # Klikamy drugi raz dla pewności, by najwyższe wyniki były na górze
            await page.locator('th.depth-column').click()
            await page.wait_for_timeout(2000)

            # 3. Wyciągamy dane
            print("Pobieram kod HTML...")
            table_html = await page.eval_on_selector('.ladderTable', "el => el.outerHTML")
            
            df = pd.read_html(io.StringIO(table_html))[0]
            
            # Zapisujemy plik
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print("Sukces! Plik został nadpisany nowymi danymi.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            # Robimy zrzut ekranu błędu, żebyś mógł go zobaczyć w plikach akcji (opcjonalnie)
            await page.screenshot(path="error_screenshot.png")
            exit(1)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
