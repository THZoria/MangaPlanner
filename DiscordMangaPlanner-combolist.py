import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from bs4 import BeautifulSoup
import re
import requests
import schedule
import time
from datetime import datetime

#Combo list of mangas you're interested in
allowed_keywords = ["A Couple of Cuckoos", "A Certain Scientific Railgun", "Ash le Bâtisseur de civilisation", "Black Clover", "Bocchi the Rock!", "By The Grace Of The Gods", "Coco L'île magique", "Frieren", "Fun Territory Defense by the Optimistic Lord", "Horimiya", "Kamisama School", "L'Atelier des Sorciers", "La Nouvelle vie de Lili", "La Petite faiseuse de livres - Partie 2", "Les Caprices de la Lune", "Les Carnets de l'Apothicaire", "Les Carnets de l'Apothicaire - Enquêtes à la cour", "Les fées, le Roi-Dragon et moi (en chat)", "Les fées, le Roi-Dragon et moi (en chat)", "Love Me For Who I Am", "Magic Maker", "Mushoku Tensei", "Oshi no Ko", "Step by Step Sara", "Tearmoon Empire Story", "The Rising of the Shield Hero", "Shy", "Vanupied", "Shirayuki aux cheveux rouges", "Fairy Tail - 100 Years Quest", "La sainte déchue et son fervent protecteur", "	Tadokoro-san", "La Lady solitaire", "Le Palais des assassins", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", "keyword3", ]

async def send_to_discord(embed):
    # Put a link webhook discord
    webhook_url = ""
    requests.post(webhook_url, json={"embeds": [embed]})

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

        if any(keyword.lower() in nom_manga.lower() for keyword in allowed_keywords):
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
