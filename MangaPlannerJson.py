import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from bs4 import BeautifulSoup
from datetime import datetime
import json

# Version du script
print("Version : 1.2.0 by Zoria")

async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto("https://www.nautiljon.com/planning/manga/")

    try:
        await page.waitForSelector("#planning tbody", timeout=60000)
    except TimeoutError:
        print("Le délai d'attente pour le sélecteur '#planning tbody' a été dépassé.")

    table_content = await page.evaluate('document.querySelector("#planning tbody").outerHTML')
    soup = BeautifulSoup(table_content, 'html.parser')

    elements = soup.find_all('tr')

    manga_list = []

    for element in elements:
        properties = element.find_all('td')
        id = properties[2].find_all('a')[-1]['href'].split(",")[-1].split(".")[0]
        date_sortie = properties[0].get_text()
        image = 'https://www.nautiljon.com' + properties[1].a.img.attrs['src']
        nom_manga = properties[2].find_all('a')[-1].get_text()
        prix = properties[3].get_text()
        editeur = properties[4].a.get_text() if properties[4].a else None
        lien_acheter = 'https://www.nautiljon.com' + properties[5].a.attrs['href'] if properties[5].a else None

        manga_info = {
            "id": id,
            "nom_manga": nom_manga,
            "date_sortie": date_sortie,
            "prix": prix,
            "editeur": editeur,
            "lien_acheter": lien_acheter,
            "image": image
        }

        manga_list.append(manga_info)

    with open("planning.json", "w", encoding="utf-8") as json_file:
        json.dump(manga_list, json_file, ensure_ascii=False, indent=4)

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
