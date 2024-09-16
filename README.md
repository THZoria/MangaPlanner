# MangaPlanner

MangaPlanner is a Python script designed to provide manga calendars on Discord.
It uses an API or web scraping from the nautiljon site to retrieve information on upcoming manga releases, then formats them in a clear and readable way for display on a Discord server or in ICS format. This script can be configured to run periodically, providing regular updates on new manga releases, offering a rewarding experience for manga fans on Discord or in ICS for Mail tools like Outlook or Thuderbird.

# There are 2 versions of this script, 
- The first displays the entire schedule for the upcoming manga month.
- The second displays only the mangas you've added to the combo list.

# How it works
This requires the use of Python, as well as a certain module asyncio, pyppeteer, beautifulsoup4, schedule and requests
Install the requirements:

```sh
git clone https://github.com/THZoria/MangaPlanner.git
pip install -r requirements.txt
```

To run the for discord script

Full version :

```sh
python DiscordMangaPlanner.py
```

Version with list of mangas to be added to the script

```sh
python DiscordMangaPlanner-combolist.py
```

To run this script in ICS version

Full version :

```sh
python MangaPlannerICS.py
```

Version with list of mangas to be added to the script

```sh
python MangaPlannerICS-ComboList.py
```

Version that generates a json file containing id, manga name, release date, price, publisher, purchase link and image.

```sh
python MangaPlannerJson.py
```

You'll also need to modify the webhook link in the script, as well as the combo list if you're using the 2nd script
All that's left to do is to use the Windows task scheduler or Cron on Linux to automate the monthly script launch.

Basically, it's a simple script I made in my spare time just to keep up to date with the latest releases. Feel free to fork the script and improve it to your liking, this script being far from perfect.
Many thanks to Pharuxtan who helped me create the script embed,
