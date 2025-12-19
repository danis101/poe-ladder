import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import os

async def run():
    async with async_playwright() as p:
        if not os.path.exists('data'): os.makedirs('data')
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("KROK 1: Wchodzę na stronę od razu z parametrem limitu...")
            # Wymuszamy limit 100 bezpośrednio w URL i czekamy na pełne załadowanie sieci
            await page.goto("https://www.pathofexile.com/ladders/league/Keepers?type=depthsolo&limit=100", wait_until="networkidle")
            
            # KROK 2: Upewniamy się, że dropdown pokazuje 100 (oszukujemy skrypt strony)
            print("KROK 2: Synchronizuję stan dropdownu...")
            await page.evaluate("""
                const sel = document.querySelector('select.view-count-select');
                if(sel) {
                    sel.value = '100';
                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                }
            """)
            await page.wait_for_timeout(3000)

            # KROK 3: Odkrywamy Depth i sortujemy (przez JS, żeby nie 'pudłować')
            print("KROK 3: Włączam Depth i sortuję...")
            await page.evaluate("""
                const cb = document.querySelector('input[name="hide_delve"]');
                if (cb && cb.checked) {
                    cb.click();
                }
                setTimeout(() => {
                    const th = document.querySelector('th[data-sort="depth"]');
                    if (th) th.click();
                }, 1000);
            """)
            
            # Czekamy aż tabela się "uspokoi"
            print("Czekam na stabilizację danych...")
            await page.wait_for_timeout(7000)

            # KROK 4: Pobieranie danych
            print("KROK 4: Zgrywam dane...")
            content = await page.content()
            dfs = pd.read_html(io.StringIO(content))
            
            # Szukamy właściwej tabeli (tej z kolumną Rank)
            df = next(d for d in dfs if 'Rank' in d.columns)
            
            # Czyścimy puste kolumny z ikonami
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # ZAPIS DO PLIKU (wymuszony)
            file_path = 'data/keepers-delve.tsv'
            df.to_csv(file_path, sep='\t', index=False)
            
            print(f"SUKCES! Plik zapisany: {file_path}")
            print(f"Liczba wierszy: {len(df)}")

        except Exception as e:
            print(f"BŁĄD: {e}")
            await page.screenshot(path="data/error_save.png")
            # Nawet jeśli jest błąd, spróbujemy zapisać to co mamy, żebyś nie miał pustego repo
            if 'df' in locals():
                df.to_csv('data/keepers-delve.tsv', sep='\t', index=False)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
