import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        browser = await p.chromium.launch(headless=True)
        # Ustawiamy viewport na taki, w którym na screenie widzieliśmy dropdown
        context = await browser.new_context(viewport={'width': 1280, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. CZEKAMY NA DROPDOWN I KLIKAMY GO
            print("Czekam aż '20 per page' będzie gotowe...")
            # Czekamy aż selektor fizycznie pojawi się w kodzie
            dropdown_selector = 'select.view-count-select'
            await page.wait_for_selector(dropdown_selector, state="visible")
            
            # Przewijamy do niego
            await page.locator(dropdown_selector).scroll_into_view_if_needed()
            await page.wait_for_timeout(2000)

            # 2. WYMUSZAMY ZMIANĘ PRZEZ JS + EVENT DISPATCH
            # Na Twoim screenie widać, że on tam jest, więc JS go teraz na 100% złapie
            print("Zmieniam limit na 100...")
            await page.evaluate("""
                const sel = document.querySelector('select.view-count-select');
                sel.value = '100';
                sel.dispatchEvent(new Event('change', { bubbles: true }));
            """)
            
            # 3. STRAŻNIK: Czekamy aż w tabeli pojawi się Rank 21
            print("Czekam aż tabela się rozszerzy...")
            # To sprawi, że bot nie ruszy dalej, póki nie zobaczy więcej niż 20 wierszy
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=20000)

            # 4. DODATKI: DEPTH I SORTOWANIE
            print("Odkrywam Depth i sortuję...")
            await page.evaluate("""
                document.querySelector('input[name="hide_delve"]').click();
                setTimeout(() => {
                    document.querySelector('th[data-sort="depth"]').click();
                }, 1000);
            """)
            
            await page.wait_for_timeout(5000)

            # 5. POBIERANIE DANYCH
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Zapisujemy finalny plik
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            print(f"SUKCES! Mamy {len(df)} rekordów w pliku.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/final_crash_debug.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
