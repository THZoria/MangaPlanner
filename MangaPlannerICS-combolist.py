from __future__ import annotations

import asyncio
import argparse
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Iterable

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

APP_VERSION = "1.3.0"
BASE_URL = "https://www.nautiljon.com"
PLANNING_URL = f"{BASE_URL}/planning/manga/"

#Combo list of mangas you're interested in
ALLOWED_KEYWORDS = ["KeyWord1", "KeyWord2", "KeyWord4", "KeyWord5", "KeyWord6"]

# --------------------------- Model ---------------------------

@dataclass
class MangaEvent:
    nom_manga: str
    date_sortie: str      
    prix: str
    editeur: Optional[str]
    lien_acheter: Optional[str]

    def date_as_ics(self) -> str:
        try:
            dt = datetime.strptime(self.date_sortie, "%d/%m/%Y")
            return dt.strftime("%Y%m%d")
        except ValueError:
            return ""

    def date_end_as_ics(self) -> str:
        try:
            dt = datetime.strptime(self.date_sortie, "%d/%m/%Y") + timedelta(days=1)
            return dt.strftime("%Y%m%d")
        except ValueError:
            return ""

    def human_date(self) -> str:
        try:
            dt = datetime.strptime(self.date_sortie, "%d/%m/%Y")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return self.date_sortie

# --------------------------- Utilities ---------------------------

def any_keyword_in(text: str, keywords: Iterable[str]) -> bool:
    return any(k in text for k in keywords)

async def dismiss_gdpr(page) -> None:
    candidates = [
        {"role": "button", "name": r"Continuer sans accepter"},
        {"role": "button", "name": r"Tout refuser|Refuser tout"},
        {"role": "button", "name": r"Continuer|Fermer|Accepter et fermer"},
        {"role": "link",   "name": r"Continuer sans accepter|Tout refuser|Fermer"},
    ]
    for c in candidates:
        try:
            await page.get_by_role(c["role"], name=c["name"], exact=False).click(timeout=1200)
            logging.info("✅ Pop-up RGPD ignorée (%s / %s).", c["role"], c["name"])
            return
        except Exception:
            continue
    logging.info("ℹ️ Aucune pop-up RGPD détectée (ou déjà fermée).")

# --------------------------- Scraper ---------------------------

async def extract_items(page) -> List[MangaEvent]:
    try:
        await page.wait_for_selector("#planning tbody", timeout=15_000)
        logging.info("✅ Tableau détecté.")
    except PlaywrightTimeout:
        raise RuntimeError("Le tableau #planning n'a pas été trouvé (timeout).")

    rows = await page.eval_on_selector_all(
        "#planning tbody tr",
        """
        (trs) => trs.map(tr => {
            const tds = Array.from(tr.querySelectorAll('td'));
            if (tds.length < 6) return null;

            const txt = el => (el?.textContent || '').trim();

            const date = txt(tds[0]);
            const linksTitle = tds[2].querySelectorAll('a');
            const nom = linksTitle.length ? txt(linksTitle[linksTitle.length - 1]) : txt(tds[2]);
            const prix = txt(tds[3]);
            const edLink = tds[4].querySelector('a');
            const editeur = edLink ? txt(edLink) : txt(tds[4]);
            const buyLink = tds[5].querySelector('a');
            let lien = buyLink ? (buyLink.getAttribute('href') || '').trim() : null;
            if (lien && !/^https?:\\/\\//.test(lien)) lien = 'https://www.nautiljon.com' + lien;

            return { date, nom, prix, editeur: editeur || null, lien_acheter: lien || null };
        }).filter(Boolean)
        """
    )

    items: List[MangaEvent] = []
    for r in rows:
        nom = (r.get("nom") or "").strip()
        if not nom:
            continue
        if not any_keyword_in(nom, ALLOWED_KEYWORDS):
            continue
        items.append(
            MangaEvent(
                nom_manga=nom,
                date_sortie=(r.get("date") or "").strip(),
                prix=(r.get("prix") or "").strip(),
                editeur=(r.get("editeur") or None) or None,
                lien_acheter=(r.get("lien_acheter") or None) or None,
            )
        )
    return items

async def scrape(headless: bool, timeout: int, debug: bool) -> List[MangaEvent]:
    launch_kwargs = dict(headless=headless, args=["--no-sandbox"])
    if debug:
        launch_kwargs["slow_mo"] = 50

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_kwargs)
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
            logging.info("🌐 Accès à la page… %s", PLANNING_URL)
            await page.goto(PLANNING_URL, wait_until="domcontentloaded", timeout=timeout * 1000)

            await page.wait_for_timeout(800)
            await dismiss_gdpr(page)

            items = await extract_items(page)
            logging.info("✅ %d éléments retenus après filtre.", len(items))
            return items
        finally:
            await browser.close()

# --------------------------- ICS ---------------------------

def make_ics_event_legacy(ev: MangaEvent) -> str:
    ds = ev.date_as_ics()
    de = ev.date_end_as_ics()
    if not ds or not de:
        return ""
    
    desc = (
        f"Editeur: {ev.editeur or ''}\\n"
        f"Date de sortie: {ev.human_date()}\\n"
        f"Prix: {ev.prix or ''}\\n"
        f"Lien: {ev.lien_acheter or ''}\\n"
    )
    return (
        "BEGIN:VEVENT\n"
        f"SUMMARY:{ev.nom_manga}\n"
        f"DESCRIPTION:{desc}\n"
        f"DTSTART;VALUE=DATE:{ds}\n"
        f"DTEND;VALUE=DATE:{de}\n"
        "END:VEVENT\n"
    )

def export_ics_legacy(events: List[MangaEvent], out_path: Path) -> None:
    content = "BEGIN:VCALENDAR\nVERSION:2.0\n"
    for ev in events:
        block = make_ics_event_legacy(ev)
        if block:
            content += block
    content += "END:VCALENDAR\n"
    out_path.write_text(content, encoding="utf-8")

# --------------------------- CLI ---------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Exporter le planning Nautiljon → ICS (filtré).")
    p.add_argument("--out", type=Path, default=Path("manga_schedule.ics"), help="Fichier .ics de sortie")
    p.add_argument("--timeout", type=int, default=30, help="Timeout (s) pour le chargement initial")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--headless", dest="headless", action="store_true", help="Mode headless (par défaut)")
    g.add_argument("--no-headless", dest="headless", action="store_false", help="Affiche le navigateur")
    p.set_defaults(headless=True)
    p.add_argument("--debug", action="store_true", help="Logs verbeux")
    return p.parse_args(argv)

def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

# --------------------------- Input ---------------------------

async def amain(argv: list[str]) -> int:
    args = parse_args(argv)
    setup_logging(args.debug)
    logging.info("Version : %s", APP_VERSION)

    try:
        items = await scrape(headless=args.headless, timeout=args.timeout, debug=args.debug)
    except Exception as e:
        logging.error("❌ Échec du scraping : %s", e, exc_info=args.debug)
        return 1

    if not items:
        logging.warning("⚠️ Aucun résultat après filtre. Le fichier sera tout de même écrit (sans événements).")

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    export_ics_legacy(items, out)
    logging.info("💾 Export ICS (legacy) -> %s", out.resolve())
    return 0

def main() -> None:
    import sys
    try:
        code = asyncio.run(amain(sys.argv[1:]))
    except KeyboardInterrupt:
        logging.warning("Interrompu par l'utilisateur.")
        code = 130
    raise SystemExit(code)

if __name__ == "__main__":
    main()


