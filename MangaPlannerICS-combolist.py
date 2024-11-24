import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Version du script
print("Version : 1.2.0 by Zoria")

#Combo list of mangas you're interested in
allowed_keywords = ["KeyWord1", "KeyWord2", "KeyWord4", "KeyWord5", "KeyWord6"]

async def generate_ics_event(manga_info):
    """
    Generate an ICS event string for a manga.
    """
    event = f"BEGIN:VEVENT\n"
    event += f"SUMMARY:{manga_info['nom_manga']}\n"
    event += f"DESCRIPTION:Editeur: {manga_info['editeur']}\\nDate de sortie: {manga_info['date_sortie']}\\nPrix: {manga_info['prix']}\\nLien: {manga_info['lien_acheter']}\\n\n"
    event += f"DTSTART;VALUE=DATE:{manga_info['date_sortie']}\n"
    event += f"DTEND;VALUE=DATE:{manga_info['date_sortie']}\n"
    event += f"END:VEVENT\n"
    return event

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

    manga_events = {}  # Dictionnaire pour stocker les événements triés

    for element in elements:
        properties = element.find_all('td')

        if len(properties) >= 6:
            nom_manga = properties[2].find_all('a')[-1].get_text()
            for keyword in allowed_keywords:
                if keyword in nom_manga:
                    date_sortie = datetime.strptime(properties[0].get_text(), "%d/%m/%Y").strftime("%Y%m%d")
                    image = 'https://www.nautiljon.com' + properties[1].a.img.attrs['src']
                    prix = properties[3].get_text()
                    editeur = properties[4].a.get_text() if properties[4].a else None
                    lien_acheter = 'https://www.nautiljon.com' + properties[5].a.attrs['href'] if properties[5].a else None

                    manga_info = {
                        "nom_manga": nom_manga,
                        "date_sortie": date_sortie,
                        "prix": prix,
                        "editeur": editeur,
                        "lien_acheter": lien_acheter,
                        "image" : image
                    }

                    event = await generate_ics_event(manga_info)

                    # Ajouter l'événement trié au dictionnaire
                    manga_events[nom_manga] = event
                    break  # Sortir de la boucle des mots-clés une fois qu'une correspondance est trouvée

    # Parcourir le dictionnaire trié et ajouter les événements à ics_content
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\n"
    for manga_event in sorted(manga_events.values()):
        ics_content += manga_event

    ics_content += "END:VCALENDAR\n"

    with open("manga_schedule.ics", "w", encoding="utf-8") as ics_file:
        ics_file.write(ics_content)

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
