import asyncio
from playwright.async_api import async_playwright, TimeoutError
import pandas as pd
import io
import os
import random

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        os.makedirs("data", exist_ok=True)

        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        # Ukrywamy ślady automatyzacji
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print("Wchodzę na stronę...")
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # --- SYMULACJA LUDZKIEGO ZACHOWANIA PRZED KLIKNIĘCIEM ---
            await asyncio.sleep(random.uniform(3, 5))
            await page.mouse.wheel(0, 300) # Lekki scroll w dół
            await asyncio.sleep(1)
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            # -------------------------------------------------------

            print("Konfiguruję tabelę (Depth)...")
            depth_checkbox = page.get_by_label("Hide Delve Depth")
            await depth_checkbox.wait_for(state="visible", timeout=15000)
            
            # Klikamy z losowym opóźnieniem
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await depth_checkbox.uncheck()
            
            await asyncio.sleep(2)
            await page.locator('th[data-sort="depth"]').click()
            await asyncio.sleep(3)

            print("Przełączam na TOP 100 (wolna interakcja)...")
            # Zamiast gwałtownego kliknięcia, najeżdżamy i klikamy
            selector_20 = page.locator("text=20").first
            await selector_20.hover()
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await selector_20.click()
            
            await asyncio.sleep(random.uniform(1, 2))
            
            selector_100 = page.get_by_text("100", exact=True).first
            await selector_100.hover()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await selector_100.click()

            print("Czekam na przeładowanie danych...")
            # Zwiększony timeout na dociągnięcie większej tabeli
            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=30000
            )

            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if "Rank" in d.columns)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)
            print(f"Sukces! Pobrano {len(df)} rekordów.")
            await page.screenshot(path="data/final_success.png")

        except Exception as e:
            print(f"Błąd: {e}")
            await page.screenshot(path="data/error_state.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
