import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        
        browser = await p.chromium.launch(headless=True)
        # Zwiększamy okno, żeby widzieć całą stopkę
        context = await browser.new_context(viewport={'width': 1920, 'height': 2000})
        page = await context.new_page()
        
        try:
            print("Wchodzę na stronę...")
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo", wait_until="networkidle")
            
            # 1. SZUKAMY "20 per page" I KLIKAMY
            print("Szukam napisu '20 per page' do kliknięcia...")
            # Locator szuka elementu select, który zawiera tekst '20 per page'
            dropdown_trigger = page.get_by_text("20 per page")
            
            # Przewijamy do niego fizycznie
            await dropdown_trigger.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            
            # Klikamy w dropdown i wybieramy 100
            print("Wybieram 100 z listy...")
            await page.select_option('select.view-count-select', label="100 per page")
            
            # Czekamy aż tabela "urośnie"
            print("Czekam na załadowanie 100 rekordów...")
            await page.wait_for_function("document.querySelectorAll('table.ladderTable tbody tr').length > 20", timeout=20000)

            # 2. ODZNACZANIE I SORTOWANIE (przez JS dla pewności trafienia)
            print("Włączam kolumnę Depth i sortuję...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
                setTimeout(() => {
                    const header = document.querySelector('th[data-sort="depth"]');
                    if (header) header.click();
                }, 2000);
            """)
            
            # Finalna pauza na dociągnięcie posortowanych danych
            await page.wait_for_timeout(6000)

            # 3. ZAPIS DANYCH
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            df = next(d for d in dfs if 'Rank' in d.columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
            
            print(f"SUKCES! Mamy {len(df)} rekordów.")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/bot_search_text_error.png")
            exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
