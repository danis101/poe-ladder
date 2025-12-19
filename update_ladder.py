import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Uruchamiamy z konkretnym nagłówkiem językowym, to czasem pomaga na Cloudflare
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            # Zwiększony timeout i czekanie na 'load'
            response = await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="load", timeout=90000)
            
            # DIAGNOSTYKA: Sprawdzamy status odpowiedzi
            print(f"Status HTTP: {response.status}")
            
            # Czekamy dodatkowo na JS
            await page.wait_for_timeout(5000)

            # 1. Wymuszamy odznaczenie checkboxa przez JS (omija problemy z klikalnością)
            print("Próba odznaczenia Delve przez JavaScript...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            
            # Czekamy aż tabela się przeładuje (pojawią się nowe kolumny)
            await page.wait_for_timeout(5000)

            # 2. Sprawdzamy czy tabela istnieje i pobieramy
            table_selector = "table.ladderTable"
            if await page.query_selector(table_selector):
                print("Tabela znaleziona, pobieram HTML...")
                html = await page.inner_html(table_selector)
                df = pd.read_html(io.StringIO(f"<table>{html}</table>"))[0]
                
                # Zapisujemy do TSV
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
                print("SUKCES: Plik zapisany.")
            else:
                print("BŁĄD: Tabela nie pojawiła się w DOM.")
                # ROBIMY SCREENSHOT - to kluczowe do diagnozy!
                await page.screenshot(path="data/error_view.png")
                print("Screenshot błędu zapisany w folderze data.")
                exit(1)

        except Exception as e:
            print(f"WYJĄTEK: {str(e)}")
            await page.screenshot(path="data/exception_view.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
