import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        # Uruchamiamy przeglądarkę z "ludzkimi" ustawieniami
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = await context.new_page()
        
        try:
            print("1. Otwieram stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 2. PRZEWIJANIE DO DROPDOWNA
            print("2. Szukam dropdowna na dole...")
            dropdown = page.locator('select.view-count-select')
            await dropdown.scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)

            # 3. KLIKNIĘCIE I WYBÓR (Symulacja UI)
            print("3. Wybieram '100 per page' przez kliknięcie...")
            # Najpierw klikamy w sam dropdown, żeby go aktywować
            await dropdown.click()
            # Teraz wybieramy opcję 100 – to odpali wewnętrzne skrypty PoE
            await dropdown.select_option(label="100 per page")
            
            # 4. KLUCZOWE: Czekamy na zmianę liczby wierszy (Strażnik)
            print("4. Czekam na załadowanie 100 osób...")
            # Czekamy aż liczba wierszy (tr) w tabeli będzie większa niż 20
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=30000)
            print("Sukces! Tabela urosła.")

            # 5. DODATKOWE OPCJE (Depth + Sortowanie)
            print("5. Odkrywam Depth i sortuję...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb && cb.checked) cb.click();
                setTimeout(() => {
                    const th = document.querySelector('th[data-sort="depth"]');
                    if (th) th.click();
                }, 2000);
            """)
            await page.wait_for_timeout(5000)

            # 6. ZGRYWANIE DANYCH
            print("6. Zapisuję dane do pliku...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyszczenie i zapis
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"FINAŁ: Zapisano {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_final_fix.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
