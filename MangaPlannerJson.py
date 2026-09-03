#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import csv
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import argparse
import sys

APP_VERSION = "3.0.1 by Zoria"
BASE_URL = "https://www.nautiljon.com"
PLANNING_URL = f"{BASE_URL}/planning/manga/"

# ---------------------------  Models ---------------------------

@dataclass
class MangaItem:
    nom_manga: str
    date_sortie: str
    prix: str
    editeur: Optional[str]
    lien_acheter: Optional[str]
    image: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------- Export helpers ---------------------------

def export_json(items: List[MangaItem], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        json.dump([i.to_dict() for i in items], f, ensure_ascii=False, indent=2)


def export_csv(items: List[MangaItem], out_path: Path) -> None:
    fieldnames = ["nom_manga", "date_sortie", "prix", "editeur", "lien_acheter", "image"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for it in items:
            writer.writerow(it.to_dict())


# --------------------------- Scraper core ---------------------------

async def dismiss_gdpr(page) -> None:
    """
    Essaie plusieurs variantes de boutons/roles pour fermer une éventuelle popup RGPD.
    Silencieux en cas d'échec : on continue sans bloquer.
    """
    candidates = [
        # Boutons fréquents FR
        {"role": "button", "name": r"Continuer sans accepter"},
        {"role": "button", "name": r"Tout refuser|Refuser tout"},
        {"role": "button", "name": r"Continuer|Fermer|Accepter et fermer"},
        # Lien possible
        {"role": "link", "name": r"Continuer sans accepter|Tout refuser|Fermer"},
    ]
    for c in candidates:
        try:
            await page.get_by_role(c["role"], name=c["name"], exact=False).click(timeout=1500)
            logging.info("✅ Pop-up RGPD ignorée (%s / %s).", c["role"], c["name"])
            return
        except Exception:
            continue
    logging.info("ℹ️ Aucune pop-up RGPD à fermer (ou non détectée).")


async def extract_planning(page) -> List[MangaItem]:
    """
    Extrait toutes les lignes du tableau via un evaluate JS côté page
    pour minimiser les allers-retours Python <-> navigateur.
    """
    try:
        await page.wait_for_selector("#planning tbody", timeout=15_000)
        logging.info("✅ Tableau de planning détecté.")
    except PlaywrightTimeout:
        raise RuntimeError("Le tableau #planning n'a pas été trouvé (timeout).")

    rows = await page.eval_on_selector_all(
        "#planning tbody tr",
        """
        (trs) => trs.map(tr => {
            if (tr.classList.contains('planning_day')) return null;

            const tds = Array.from(tr.querySelectorAll('td'));
            if (tds.length < 5) return null;

            const text = el => (el?.textContent || '').trim();

            const date_sortie = (tr.getAttribute('data-planning-date') || '').trim();

            const imgEl = tds[0].querySelector('a img');
            let image = imgEl ? (imgEl.getAttribute('src') || '').trim() : null;
            if (image && !/^https?:\\/\\//.test(image)) image = 'https://www.nautiljon.com' + image;

            const heading = tds[1].querySelector('.planning_volume_heading');
            const details = tds[1].querySelector('.planning_volume_details');
            const nom_manga = [text(heading), text(details)].filter(Boolean).join(' - ') || text(tds[1]);

            const prix = text(tds[2]);

            const edLink = tds[3].querySelector('a');
            const editeur = edLink ? text(edLink) : (text(tds[3]) || null);

            const buyLink = tds[4].querySelector('a');
            let lien_acheter = buyLink ? (buyLink.getAttribute('href') || '').trim() : null;
            if (lien_acheter && !/^https?:\\/\\//.test(lien_acheter)) lien_acheter = 'https://www.nautiljon.com' + lien_acheter;

            return { nom_manga, date_sortie, prix, editeur, lien_acheter, image };
        }).filter(Boolean)
        """,
    )

    items: List[MangaItem] = []
    for r in rows:
        
        nom = (r.get("nom_manga") or "").strip()
        if not nom:
            continue
        items.append(
            MangaItem(
                nom_manga=nom,
                date_sortie=(r.get("date_sortie") or "").strip(),
                prix=(r.get("prix") or "").strip(),
                editeur=(r.get("editeur") or None) or None,
                lien_acheter=(r.get("lien_acheter") or None) or None,
                image=(r.get("image") or None) or None,
            )
        )
    return items


async def scrape(headless: bool, timeout: int, debug: bool) -> List[MangaItem]:
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

            items = await extract_planning(page)
            logging.info("✅ %d mangas récupérés.", len(items))
            return items
        finally:
            await browser.close()


# --------------------------- CLI ---------------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper Nautiljon planning manga (modernisé)."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(f"planning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
        help="Chemin du fichier de sortie (par défaut: planning_YYYYmmdd_HHMMSS.json)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Format de sortie (json ou csv).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout de chargement initial de la page (secondes).",
    )
    
    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument("--headless", dest="headless", action="store_true", help="Mode headless (par défaut).")
    headless_group.add_argument("--no-headless", dest="headless", action="store_false", help="Affiche le navigateur.")
    parser.set_defaults(headless=True)

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active des logs plus verbeux et slow-mo navigateur.",
    )

    return parser.parse_args(argv)


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


# --------------------------- Entry point ---------------------------

async def amain(argv: List[str]) -> int:
    args = parse_args(argv)
    setup_logging(args.debug)

    logging.info("Version : %s", APP_VERSION)
    try:
        items = await scrape(headless=args.headless, timeout=args.timeout, debug=args.debug)
    except Exception as e:
        logging.error("❌ Échec du scraping : %s", e, exc_info=args.debug)
        return 1

    if not items:
        logging.warning("⚠️ Aucun manga trouvé. Le site a peut-être changé.")
    else:
        out: Path = args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "json":
            export_json(items, out)
        else:
            export_csv(items, out)
        logging.info("💾 Export %s -> %s", args.format.upper(), out.resolve())

    return 0


def main() -> None:
    try:
        exit_code = asyncio.run(amain(sys.argv[1:]))
    except KeyboardInterrupt:
        logging.warning("Interrompu par l'utilisateur.")
        exit_code = 130
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
