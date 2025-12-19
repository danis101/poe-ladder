import asyncio
from playwright.async_api import async_playwright, TimeoutError
import pandas as pd
import io
import os
import sys

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        os.makedirs("data", exist_ok=True)

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 2000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Europe/Warsaw"
        )

        page = await context.new_page()

        try:
            print("Wchodzę na stronę...")
            await page.goto(URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # 🛑 Cloudflare challenge – PRZERWIJ BEZ COMMITU
            if await page.locator("text=Are you human").count() > 0:
                print("Cloudflare challenge wykryty – kończę run")
                await page.screenshot(path="data/cloudflare.png", full_page=True)
                return

            print("Konfiguruję tabelę (Depth)...")
            await page.get_by_label("Hide Delve Depth").uncheck()
            await page.wait_for_timeout(1000)
            await page.locator('th[data-sort="depth"]').click()
            await page.wait_for_timeout(1500)

            # 🔥 TOP 20 → TOP 100 (custom dropdown PoE)
            print("Przełączam widok na TOP 100...")
            await page.locator("text=20").first.click()
            await page.wait_for_timeout(500)
            await page.locator("text=100").first.click()

            # Czekamy aż tabela faktycznie się przebuduje
            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=10000
            )

            # Screenshot kontrolny (tylko gdy wszystko OK)
            await page.screenshot(
                path="data/debug_top100.png",
                full_page=True
            )

            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if "Rank" in d.columns)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            if len(df) < 100:
                raise RuntimeError(f"Za mało rekordów: {len(df)}")

            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)
            print(f"SUKCES: zapisano {len(df)} rekordów")

        except TimeoutError:
            print("Timeout – tabela nie załadowała się poprawnie")
            await page.screenshot(path="data/timeout.png", full_page=True)

        except Exception as e:
            print("BŁĄD:", e)
            await page.screenshot(path="data/error.png", full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
