import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from bs4 import BeautifulSoup
import requests

async def send_to_discord(embed):
    # Mettez le lien du webhook Discord ici
    webhook_url = ""
    requests.post(webhook_url, json={"embeds": [embed]})

async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto("https://www.nautiljon.com/planning/ln/")

    try:
        await page.waitForSelector("#planning tbody", timeout=60000)
    except TimeoutError:
        print("Le délai d'attente pour le sélecteur '#planning tbody' a été dépassé.")

    table_content = await page.evaluate('document.querySelector("#planning tbody").outerHTML')
    soup = BeautifulSoup(table_content, 'html.parser')

    elements = soup.find_all('tr')

    for element in elements:
        properties = element.find_all('td')

        date_sortie = properties[0].get_text()
        image = 'https://www.nautiljon.com' + properties[1].a.img.attrs['src']
        nom_manga = properties[2].find_all('a')[-1].get_text()
        prix = properties[3].get_text()
        editeur = None
        if properties[4].a:
            editeur = properties[4].a.get_text()
        lien_acheter = None
        if properties[5].a:
            lien_acheter = 'https://www.nautiljon.com' + properties[5].a.attrs['href']

        embed = {
            "title": f"Nouveau manga: {nom_manga}",
            "fields": [
                {"name": "Date de sortie", "value": date_sortie, "inline": True},
                {"name": "Prix", "value": prix, "inline": True},
                {"name": "Éditeur", "value": editeur, "inline": True},
            ],
            "image": {"url": image},
            "url": lien_acheter
        }

        await send_to_discord(embed)

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
