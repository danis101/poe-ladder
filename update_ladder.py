import asyncio
from playwright.async_api import async_playwright, TimeoutError
import pandas as pd
import io
import os

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        os.makedirs("data", exist_ok=True)

        # Uruchamiamy przeglądarkę z flagami omijającymi detekcję
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        # RĘCZNY STEALTH: Usuwamy flagę webdriver bezpośrednio w przeglądarce
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            print("Wchodzę na stronę...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # Krótka pauza na załadowanie skryptów Cloudflare
            await asyncio.sleep(5)

            # Sprawdzenie czy nas nie wywaliło na start
            if await page.locator("text=Verify you are human").count() > 0:
                print("Wykryto Cloudflare. Próbuję poczekać...")
                await asyncio.sleep(10)
                await page.screenshot(path="data/cloudflare_block.png")

            print("Konfiguruję tabelę...")
            # Odznaczamy ukrywanie głębokości
            depth_checkbox = page.get_by_label("Hide Delve Depth")
            await depth_checkbox.wait_for(state="visible", timeout=15000)
            await depth_checkbox.uncheck()
            await asyncio.sleep(2)

            # Sortowanie
            await page.locator('th[data-sort="depth"]').click()
            await asyncio.sleep(2)

            print("Zmieniam na TOP 100...")
            # Klikamy w wybór ilości (domyślnie 20)
            await page.locator("text=20").first.click()
            await asyncio.sleep(1)
            # Wybieramy 100
            await page.get_by_text("100", exact=True).first.click()

            # Czekamy na załadowanie 100 wierszy
            print("Czekam na dane...")
            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=20000
            )

            # Pobranie danych
            print("Zgrywanie do TSV...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if "Rank" in d.columns)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            # Zapis pliku
            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)
            print(f"Sukces! Zapisano {len(df)} wierszy.")
            await page.screenshot(path="data/final_success.png")

        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            await page.screenshot(path="data/error_state.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
