# MangaPlanner

[![Discord](https://img.shields.io/discord/454099185416011776?label=Join%20Discord&logo=discord&logoColor=white&style=for-the-badge)](https://discord.sighya.fr)
[![Latest Release](https://img.shields.io/github/v/release/THZoria/MangaPlanner?label=Latest%20Release&color=05c09a&style=for-the-badge)](https://github.com/THZoria/MangaPlanner/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/THZoria/MangaPlanner/total?label=Downloads&color=blue&style=for-the-badge)](https://github.com/THZoria/MangaPlanner)

MangaPlanner is a Python project that retrieves upcoming **Manga and Light Novel releases from Nautiljon**.

It can output the release schedule in three different ways:

- **Discord** - Send upcoming releases to a Discord channel using a webhook.
- **ICS** - Generate calendars compatible with Outlook, Thunderbird, Google Calendar, etc.
- **JSON** - Export release information such as title, date, price, publisher, purchase link and cover.

Discord and ICS scripts also have a **ComboList** version to only track selected titles.

> [!NOTE]
> MangaPlanner is an independent project and is not affiliated with Nautiljon.

## Installation

Requires **Python 3**.

```bash
git clone https://github.com/THZoria/MangaPlanner.git
cd MangaPlanner

pip install -r requirements.txt
playwright install
```

## Usage

### Discord

Configure your Discord webhook in the script before running it.

```bash
# Manga
python DiscordPlanner/DiscordMangaPlanner.py
python DiscordPlanner/DiscordMangaPlanner-combolist.py

# Light Novels
python DiscordPlanner/DiscordLNPlanner.py
python DiscordPlanner/DiscordLNPlanner-combolist.py
```

The `-combolist` versions only send releases matching titles from your personal list.

### ICS

Generate an `.ics` calendar containing upcoming releases:

```bash
# Manga
python MangaPlannerICS/MangaPlannerICS.py
python MangaPlannerICS/MangaPlannerICS-combolist.py

# Light Novels
python LNPlannerICS/LNPlannerICS.py
python LNPlannerICS/LNPlannerICS-combolist.py
```

The generated calendar can be imported into any application supporting the ICS format.

### JSON

Generate structured release data:

```bash
# Manga
python MangaPlannerJson.py

# Light Novels
python LNPlannerJson.py
```

JSON exports include the available release information such as title, release date, price, publisher, purchase link and cover image.

## Automation

The scripts can be run automatically using **Cron** on Linux or **Task Scheduler** on Windows.

Example Cron job to run the Manga Discord planner on the first day of every month:

```cron
0 9 1 * * cd /path/to/MangaPlanner && python DiscordPlanner/DiscordMangaPlanner.py
```

## About

MangaPlanner was originally created as a small personal project to keep track of upcoming Manga and Light Novel releases.

It relies on Nautiljon's website structure, so scraper updates may occasionally be required when the website changes.

Feel free to fork the project, report issues, submit fixes or improve it for your own needs.

Created by **Zoria / THZoria**.

Special thanks to **Pharuxtan** for helping with the original Discord embed implementation.
