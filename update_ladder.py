import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os
import random

URL = "https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo"

async def run():
    async with async_playwright() as p:
        # Ustalenie ścieżek
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Uruchomienie w trybie headless (wymagane dla GitHub Actions)
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()
        # Ukrywanie śladów bota
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print(f"Wchodzę na stronę: {URL}")
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(random.uniform(5, 8)) # Dodatkowa losowość wewnątrz skryptu

            print("Konfiguruję tabelę (odznaczanie Hide Depth)...")
            try:
                # Szukamy checkboxa lub tekstu obok niego
                checkbox = page.get_by_label("Hide Delve Depth")
                if await checkbox.is_visible():
                    await checkbox.uncheck()
                else:
                    await page.click("text=Hide Delve Depth")
            except:
                print("Nie udało się zmienić checkboxa - pomijam.")

            await asyncio.sleep(2)
            # Sortowanie po Depth
            await page.click('th[data-sort="depth"]')
            print("Sortowanie Depth ustawione.")
            await asyncio.sleep(5)

            # Przełączanie na 100 rekordów (klasa znaleziona przez debugger)
            print("Zmieniam widok na 100 per page...")
            selector_100 = "select.perPageOptions"
            
            await page.locator(selector_100).scroll_into_view_if_needed()
            await page.select_option(selector_100, "100")
            
            print("Czekam na przeładowanie danych...")
            # Pętla sprawdzająca czy tabela urosła
            for i in range(15):
                await asyncio.sleep(2)
                count = await page.locator("table.ladderTable tbody tr").count()
                print(f"Obecna liczba wierszy: {count}")
                if count >= 100:
                    break

            # Pobieranie danych
            print("Zgrywam dane do TSV...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if "Rank" in d.columns)
            
            # Czyszczenie kolumn
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            
            # Zapis do pliku
            output_file = os.path.join(data_dir, "keepers-delve.tsv")
            df.to_csv(output_file, sep="\t", index=False)
            
            print(f"Sukces! Pobrano {len(df)} rekordów.")

        except Exception as e:
            print(f"Błąd podczas scrapowania: {e}")
            await page.screenshot(path=os.path.join(data_dir, "error_gh_actions.png"))
            raise e # Rzucamy błąd dalej, żeby GitHub Actions zaznaczyło fail w logach
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
