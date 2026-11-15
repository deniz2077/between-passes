"""Element screenshots of the live app (served locally) for the decks and video."""
import asyncio, os, sys
from playwright.async_api import async_playwright
OUT = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        await pg.goto(BASE); await pg.wait_for_timeout(1500)
        await pg.add_style_tag(content=".nav{position:static!important}")
        await pg.click('.steps button[data-step="2"]'); await pg.wait_for_timeout(1500)
        await pg.locator(".demo").screenshot(path=f"{OUT}/n_demo.png")
        await pg.screenshot(path=f"{OUT}/n_cover.png")
        await pg.locator(".bars").scroll_into_view_if_needed(); await pg.wait_for_timeout(1800)
        await pg.locator(".bars").screenshot(path=f"{OUT}/n_bars.png")
        await pg.locator(".explorer").scroll_into_view_if_needed(); await pg.wait_for_timeout(600)
        await pg.locator(".mapbox").screenshot(path=f"{OUT}/n_map.png")
        await pg.locator("#card").screenshot(path=f"{OUT}/n_card_ceyhan.png")
        dot = pg.locator('circle.dot.beyond').first
        await dot.click(); await pg.wait_for_timeout(1200)
        await pg.locator("#card").screenshot(path=f"{OUT}/n_card_beyond.png")
        await pg.locator(".look").scroll_into_view_if_needed(); await pg.wait_for_timeout(400)
        await pg.locator(".look").screenshot(path=f"{OUT}/n_look.png")
        await pg.locator("#board").scroll_into_view_if_needed(); await pg.wait_for_timeout(400)
        await pg.locator("#board").screenshot(path=f"{OUT}/n_board.png")
        await pg.goto(BASE + "lab.html"); await pg.wait_for_timeout(5000)
        await pg.screenshot(path=f"{OUT}/n_lab.png")
        await pg.goto(BASE + "tr.html"); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}/n_tr.png")
        await b.close()
asyncio.run(main())
