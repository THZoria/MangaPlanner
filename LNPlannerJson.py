from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

APP_VERSION = "3.0.1 by Zoria"
BASE_URL = "https://www.nautiljon.com"
PLANNING_URL = f"{BASE_URL}/planning/ln/"


async def dismiss_gdpr(page) -> None:
    candidates = [
        {"role": "button", "name": r"Continuer sans accepter"},
        {"role": "button", "name": r"Tout refuser|Refuser tout"},
        {"role": "button", "name": r"Continuer|Fermer|Accepter et fermer"},
        {"role": "link", "name": r"Continuer sans accepter|Tout refuser|Fermer"},
    ]
    for candidate in candidates:
        try:
            await page.get_by_role(candidate["role"], name=candidate["name"], exact=False).click(timeout=1200)
            return
        except Exception:
            continue


async def extract_items(page):
    try:
        await page.wait_for_selector("#planning tbody", timeout=15_000)
    except PlaywrightTimeout:
        raise RuntimeError("Le tableau #planning n'a pas ete trouve (timeout).")

    return await page.eval_on_selector_all(
        "#planning tbody tr",
        r"""
        (trs) => trs.map(tr => {
            if (tr.classList.contains('planning_day')) return null;

            const tds = Array.from(tr.querySelectorAll('td'));
            if (tds.length < 5) return null;

            const txt = el => (el?.textContent || '').trim();
            const imgEl = tds[0].querySelector('a img');
            let image = imgEl ? (imgEl.getAttribute('src') || '').trim() : null;
            if (image && !/^https?:\/\//.test(image)) image = 'https://www.nautiljon.com' + image;

            const heading = tds[1].querySelector('.planning_volume_heading');
            const details = tds[1].querySelector('.planning_volume_details');
            const nom_manga = [txt(heading), txt(details)].filter(Boolean).join(' - ') || txt(tds[1]);
            const date_sortie = (tr.getAttribute('data-planning-date') || '').trim();
            const prix = txt(tds[2]);
            const edLink = tds[3].querySelector('a');
            const editeur = edLink ? txt(edLink) : txt(tds[3]);
            const buyLink = tds[4].querySelector('a');
            let lien_acheter = buyLink ? (buyLink.getAttribute('href') || '').trim() : null;
            if (lien_acheter && !/^https?:\/\//.test(lien_acheter)) lien_acheter = 'https://www.nautiljon.com' + lien_acheter;

            return { nom_manga, date_sortie, prix, editeur: editeur || null, lien_acheter: lien_acheter || null, image };
        }).filter(Boolean)
        """,
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Version : %s", APP_VERSION)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                viewport={"width": 1400, "height": 900},
            )
            page = await context.new_page()
            await page.goto(PLANNING_URL, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(800)
            await dismiss_gdpr(page)
            items = await extract_items(page)
        finally:
            await browser.close()

    Path("planning.json").write_text(json.dumps(items, ensure_ascii=False, indent=4), encoding="utf-8")
    logging.info("%d light novels exportes vers planning.json", len(items))


if __name__ == "__main__":
    asyncio.run(main())
