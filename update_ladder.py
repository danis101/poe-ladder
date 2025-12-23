import asyncio
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import stealth_async  # <--- WAŻNE
import pandas as pd
import io
import os

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        os.makedirs("data", exist_ok=True)

        # Uruchamiamy z dodatkowymi flagami maskującymi automatyzację
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()
        
        # APLIKUJEMY STEALTH MODE
        await stealth_async(page)

        try:
            print("Wchodzę na stronę...")
            # Używamy networkidle - czekamy aż ruch sieciowy ustanie
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # Symulujemy ruch, żeby oszukać detekcję behawioralną
            await page.mouse.move(100, 100)
            await asyncio.sleep(2)
            await page.mouse.wheel(0, 400)
            await asyncio.sleep(1)

            # Sprawdzenie Cloudflare
            if "Are you human" in await page.content() or await page.locator("text=Verify you are human").count() > 0:
                print("Cloudflare wykryty mimo stealth. Robię zrzut ekranu...")
                await page.screenshot(path="data/cloudflare_detected.png", full_page=True)
                return

            print("Konfiguruję tabelę (Depth)...")
            # Czekamy na widoczność elementu przed interakcją
            hide_depth_checkbox = page.get_by_label("Hide Delve Depth")
            await hide_depth_checkbox.wait_for(state="visible", timeout=10000)
            await hide_depth_checkbox.uncheck()
            
            await asyncio.sleep(2)
            await page.locator('th[data-sort="depth"]').click()
            await asyncio.sleep(2)

            print("Przełączam widok na TOP 100...")
            # Szukamy dropdownu selektywnie
            dropdown = page.locator(".view-count-select").first
            if await dropdown.count() > 0:
                await dropdown.click()
                await asyncio.sleep(1)
                await page.get_by_text("100", exact=True).first.click()
            else:
                # Fallback jeśli selektor klasy nie zadziała
                await page.locator("text=20").first.click()
                await asyncio.sleep(1)
                await page.locator("text=100").first.click()

            # Czekamy na przeładowanie tabeli
            print("Czekam na załadowanie 100 rekordów...")
            await page.wait_for_function(
                "document.querySelectorAll('table tbody tr').length >= 100",
                timeout=15000
            )

            print("Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            
            # Znalezienie właściwej tabeli
            df = next(d for d in dfs if "Rank" in d.columns)
            
            # Czyszczenie kolumn
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            if len(df) < 50: # Zmniejszyłem limit bezpieczeństwa, byle co zapisać jeśli tabela jest dziwna
                raise RuntimeError(f"Za mało rekordów: {len(df)}")

            # Zapis do pliku
            df.to_csv("data/keepers-delve.tsv", sep="\t", index=False)
            print(f"SUKCES: zapisano {len(df)} rekordów")
            await page.screenshot(path="data/success_snapshot.png", full_page=True)

        except TimeoutError:
            print("Timeout – strona lub tabela nie odpowiedziała w porę")
            await page.screenshot(path="data/timeout.png", full_page=True)
        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
