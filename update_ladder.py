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

        # Używamy konkretnych flag, które utrudniają identyfikację centrum danych
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )

        # Losujemy User-Agent z listy najnowszych wersji Chrome
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=random.choice(user_agents),
            device_scale_factor=1,
        )

        page = await context.new_page()

        # Zaawansowany skrypt maskujący
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        try:
            print("Próba wejścia na stronę...")
            # Próbujemy wejść najpierw na główną, żeby "ogrzać" sesję
            await page.goto("https://www.pathofexile.com", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2, 5))
            
            # Teraz idziemy do laddera
            response = await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # Czekamy aż Cloudflare skończy mielić (tzw. "waiting room")
            await asyncio.sleep(10)

            if await page.locator("text=Verify you are human").count() > 0 or "Cloudflare" in await page.title():
                print("Cloudflare wciąż blokuje. Próbuję kliknąć weryfikację (jeśli dostępna)...")
                # Próba znalezienia i kliknięcia w checkbox (czasem działa w headless)
                try:
                    box = page.locator("div#turnstile-wrapper iframe").content_frame().locator("input")
                    if await box.count() > 0:
                        await box.click()
                        await asyncio.sleep(5)
                except:
                    pass
                
                await page.screenshot(path="data/cloudflare_detected.png", full_page=True)
                # Jeśli mimo wszystko nas blokuje, kończymy z błędem widocznym w logach
                if await page.locator("text=Verify you are human").count() > 0:
                     print("Brak dostępu: Cloudflare IP Block.")
                     return

            print("Sukces! Strona załadowana. Konfiguruję tabelę...")
            
            # Reszta logiki bez zmian, żeby nie psuć formatu
            depth_checkbox = page.get_by_label("Hide Delve Depth")
            await depth_checkbox.wait_for(state="visible", timeout=15000)
            await depth_checkbox.uncheck()
            await asyncio.sleep(2)
            await page.locator('th[data-sort="depth"]').click()
            await asyncio.sleep(3)

            print("Zmiana na 100 rekordów...")
            await page.locator("text=20").first.click()
            await asyncio.sleep(1)
            await page.get_by_text("100", exact=True).first.click()

            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=20000
            )

            print("Zgrywanie danych...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if "Rank" in d.columns)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)
            print(f"Zapisano {len(df)} rekordów.")
            await page.screenshot(path="data/final_success.png")

        except Exception as e:
            print(f"Błąd: {e}")
            await page.screenshot(path="data/error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
