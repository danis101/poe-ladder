import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os
import random

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        # Upewniamy się, że folder data istnieje
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # HEADLESS=TRUE pod GitHub Actions
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()
        # Ukrywamy fakt, że to automat
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print("Wchodzę na stronę...")
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)

            print("Konfiguruję tabelę (Depth)...")
            try:
                await page.get_by_label("Hide Delve Depth").uncheck(timeout=5000)
            except:
                print("Nie udało się odznaczyć labela, próba kliknięcia bezpośredniego...")
                await page.click("text=Hide Delve Depth")
            
            await asyncio.sleep(2)
            await page.locator('th[data-sort="depth"]').click()
            print("Sortowanie Depth ustawione.")
            await asyncio.sleep(5)

            # --- ZMIANA NA 100 REKORDÓW (perPageOptions) ---
            print("Zmieniam widok na 100 rekordów...")
            target_selector = "select.perPageOptions"
            
            # W trybie headless musimy upewnić się, że element jest w zasięgu
            await page.locator(target_selector).scroll_into_view_if_needed()
            await page.select_option(target_selector, "100")
            
            print("Czekam na przeładowanie tabeli...")
            # Sprawdzanie czy wiersze się dociągnęły
            for i in range(15):
                await asyncio.sleep(2)
                count = await page.locator("table.ladderTable tbody tr").count()
                print(f"Liczba rekordów w tabeli: {count}")
                if count >= 100:
                    break

            # --- ZGRYWANIE DANYCH ---
            print("Zgrywam dane...")
            html_content = await page.content()
            dfs = pd.read_html(io.StringIO(html_content))
            df = next(d for d in dfs if "Rank" in d.columns)
            
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            
            output_path = os.path.join(data_dir, "keepers-delve.tsv")
            df.to_csv(output_path, sep="\t", index=False)
            
            print(f"SUKCES! Zapisano {len(df)} rekordów w {output_path}")

        except Exception as e:
            print(f"Błąd krytyczny: {e}")
            # W GitHub Actions screenshoty zapisujemy do folderu data, żeby móc je pobrać z artefaktów
            await page.screenshot(path=os.path.join(data_dir, "error.png"))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
