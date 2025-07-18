import os
import argparse
import asyncio
import logging
import random
import sys
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console

import src.config as config
from src.modules.core.email import verify_email
from src.modules.core.username import verify_username
from src.modules.export.csv import save_to_csv
from src.modules.export.file_operations import create_save_directory
from src.modules.export.json import save_to_json
from src.modules.export.pdf import save_to_pdf
from src.modules.utils.file_operations import getLinesFromFile, isFile
from src.modules.utils.permute import Permute
from src.modules.ai.client import send_prompt
from src.modules.utils.userAgent import getRandomUserAgent
from src.modules.whatsmyname.list_operations import check_updates
import aiohttp

load_dotenv()


def initiate():
    """Parse arguments and initialize configuration."""
    if not os.path.exists("logs/"):
        os.makedirs("logs/")
    logging.basicConfig(
        filename=config.LOG_PATH,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="blackbird",
        description="An OSINT tool to search for accounts by username in social networks.",
    )
    parser.add_argument(
        "-u", "--username", nargs="*", type=str, help="One or more usernames to search."
    )
    parser.add_argument(
        "-uf", "--username-file", help="The list of usernames to be searched."
    )
    parser.add_argument(
        "--permute", action="store_true", help="Permute usernames, ignoring single elements."
    )
    parser.add_argument(
        "--permuteall", action="store_true", help="Permute usernames, all elements."
    )
    parser.add_argument(
        "-e", "--email", nargs="*", type=str, help="One or more email to search."
    )
    parser.add_argument(
        "-ef", "--email-file", help="The list of emails to be searched."
    )
    parser.add_argument(
        "--csv", action="store_true", help="Generate a CSV with the results."
    )
    parser.add_argument(
        "--pdf", action="store_true", help="Generate a PDF with the results."
    )
    parser.add_argument(
        "--json", action="store_true", help="Generate a JSON with the results."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output.")
    parser.add_argument("-ai", "--ai", action="store_true", help="Use AI features.")
    parser.add_argument(
        "--setup-ai",
        action="store_true",
        help="Configure the API key required for AI features.",
    )
    parser.add_argument(
        "--filter",
        help='Filter sites to be searched by list property value.E.g --filter "cat=social"',
    )
    parser.add_argument(
        "--no-nsfw", action="store_true", help="Removes NSFW sites from the search."
    )
    parser.add_argument(
        "--dump", action="store_true", help="Dump HTML content for found accounts."
    )
    parser.add_argument("--proxy", help="Proxy to send HTTP requests though.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each HTTP request (Default is 30).",
    )
    parser.add_argument(
        "--max-concurrent-requests",
        type=int,
        default=30,
        help="Specify the maximum number of concurrent requests allowed. Default is 30.",
    )
    parser.add_argument(
        "--no-update", action="store_true", help="Don't update sites lists."
    )
    parser.add_argument(
        "--about", action="store_true", help="Show about information and exit."
    )
    args = parser.parse_args()

    # Store the necessary arguments to config Object
    config.username = args.username
    config.username_file = args.username_file
    config.permute = args.permute
    config.permuteall = args.permuteall
    config.csv = args.csv
    config.pdf = args.pdf
    config.json = args.json
    config.filter = args.filter
    config.no_nsfw = args.no_nsfw
    config.dump = args.dump
    config.proxy = args.proxy
    config.verbose = args.verbose
    config.ai = args.ai
    config.setup_ai = args.setup_ai
    config.timeout = args.timeout
    config.max_concurrent_requests = args.max_concurrent_requests
    config.email = args.email
    config.email_file = args.email_file
    config.no_update = args.no_update
    config.about = args.about
    config.instagram_session_id = os.getenv("INSTAGRAM_SESSION_ID")
    config.api_url = os.getenv("API_URL")
    config.console = Console()
    config.dateRaw = datetime.now().strftime("%m_%d_%Y")
    config.datePretty = datetime.now().strftime("%B %d, %Y")
    config.userAgent = getRandomUserAgent(config)
    config.usernameFoundAccounts = None
    config.emailFoundAccounts = None
    config.currentUser = None
    config.currentEmail = None

    lines = getLinesFromFile("assets/text/splash.txt")
    config.splash_line = random.choice(lines) if lines else ""


async def main():
    """Main async function to run the OSINT search."""
    initiate()
    config.console.print(
        """[red]
    ▄▄▄▄    ██▓    ▄▄▄       ▄████▄   ██ ▄█▀ ▄▄▄▄    ██▓ ██▀███  ▓█████▄ 
    ▓█████▄ ▓██▒   ▒████▄    ▒██▀ ▀█   ██▄█▒ ▓█████▄ ▓██▒▓██ ▒ ██▒▒██▀ ██▌
    ▒██▒ ▄██▒██░   ▒██  ▀█▄  ▒▓█    ▄ ▓███▄░ ▒██▒ ▄██▒██▒▓██ ░▄█ ▒░██   █▌
    ▒██░█▀  ▒██░   ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██ █▄ ▒██░█▀  ░██░▒██▀▀█▄  ░▓█▄   ▌
    ░▓█  ▀█▓░██████▒▓█   ▓██▒▒ ▓███▀ ░▒██▒ █▄░▓█  ▀█▓░██░░██▓ ▒██▒░▒████▓ 
    ░▒▓███▀▒░ ▒░▓  ░▒▒   ▓▒█░░ ░▒ ▒  ░▒ ▒▒ ▓▒░▒▓███▀▒░▓  ░ ▒▓ ░▒▓░ ▒▒▓  ▒ 
    ▒░▒   ░ ░ ░ ▒  ░ ▒   ▒▒ ░  ░  ▒   ░ ░▒ ▒░▒░▒   ░  ▒ ░  ░▒ ░ ▒░ ░ ▒  ▒ 
    ░    ░   ░ ░    ░   ▒   ░        ░ ░░ ░  ░    ░  ▒ ░  ░░   ░  ░ ░  ░ 
    ░          ░  ░     ░  ░░ ░      ░  ░    ░       ░     ░        ░    
        ░                  ░                     ░               ░      

    [/red]"""
    )
    config.console.print(
        f"             [white]{config.splash_line}[/white] | by [red]Lucas Antoniaci[/red]"
    )

    if config.about:
        config.console.print(
            """
        Author: Lucas Antoniaci (p1ngul1n0)
        Description: Blackbird is an OSINT tool that perform reverse search in username and emails.
        About WhatsMyName Project: This tool search for accounts using data from the WhatsMyName project, which is an open-source tool developed by WebBreacher. WhatsMyName License: The WhatsMyName project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0). More details (https://github.com/WebBreacher/WhatsMyName)
        """
        )
        sys.exit()

    if (
        not config.username
        and not config.email
        and not config.username_file
        and not config.email_file
        and not config.setup_ai
    ):
        config.console.print("Either --username or --email is required")
        sys.exit()
    if not config.username and (config.permute or config.permuteall):
        config.console.print("Permutations requires --username")
        sys.exit()

    async with aiohttp.ClientSession() as session:
        if config.no_update:
            config.console.print(":next_track_button:  Skipping update...")
        else:
            await check_updates(config)

        if config.ai:
            config.console.print(
                "[yellow1]:exclamation: By proceeding, you consent to share the found site names with Blackbird AI for analysis.[/yellow1] [Y/n]",
                end="",
            )
            confirm = input(" > ").strip().lower()

            if confirm not in ["", "y"]:
                config.console.print(":stop_sign:  Cancelled by user.")
                sys.exit()

            from src.modules.ai.key_manager import load_api_key_from_file

            apikey = load_api_key_from_file(config)
            if not apikey:
                config.console.print(
                    ":x: No API Key found. Please run with --setup-ai to configure the API Key."
                )
                sys.exit()

        if config.setup_ai:
            config.console.print(
                "[yellow1]:exclamation: By continuing, you acknowledge that your IP is registered for API key management and abuse prevention.[/yellow1] [Y/n]",
                end="",
            )
            confirm = input(" > ").strip().lower()

            if confirm not in ["", "y"]:
                config.console.print(":stop_sign:  Cancelled by user.")
                sys.exit()

            from src.modules.ai.key_manager import fetch_api_key_from_server

            result = await fetch_api_key_from_server(config)
            if not result:
                config.console.print(
                    ":x: Failed to fetch API Key. Please check your internet connection or try again later."
                )
            sys.exit()

        if config.username_file:
            if isFile(config.username_file):
                config.username = getLinesFromFile(config.username_file)
                config.console.print(
                    f':glasses: Successfully loaded {len(config.username)} usernames from "{config.username_file}"'
                )
            else:
                config.console.print(f'❌ Could not read file "{config.username_file}"')
                sys.exit()

        if config.username:
            if (config.permute or config.permuteall) and len(config.username) > 1:
                elements = " ".join(config.username)
                way = "all" if config.permuteall else "strict"
                permute = Permute(config.username)
                config.username = permute.gather(way)
                config.console.print(
                    f":glasses: Successfully loaded {len(config.username)} usernames from permuting {elements}"
                )
            for user in config.username:
                config.currentUser = user
                if config.dump or config.csv or config.pdf or config.json:
                    await create_save_directory(config)
                await verify_username(config.currentUser, config, session)
                if config.ai:
                    if config.usernameFoundAccounts and len(config.usernameFoundAccounts) > 2:
                        site_names = [
                            account.get("name", "") for account in config.usernameFoundAccounts
                        ]
                        if site_names:
                            prompt = ", ".join(site_names)
                            data = await send_prompt(prompt, session, config)
                            if data:
                                config.ai_analysis = data
                    else:
                        config.console.print(
                            ":warning: Not enough accounts found for AI analysis. Skipping AI features."
                        )

                if config.csv and config.usernameFoundAccounts:
                    await save_to_csv(config.usernameFoundAccounts, config)
                if config.pdf and config.usernameFoundAccounts:
                    await save_to_pdf(config.usernameFoundAccounts, "username", config)
                if config.json and config.usernameFoundAccounts:
                    await save_to_json(config.usernameFoundAccounts, config)

                config.currentUser = None
                config.usernameFoundAccounts = None

        if config.email_file:
            if isFile(config.email_file):
                config.email = getLinesFromFile(config.email_file)
                config.console.print(
                    f':glasses: Successfully loaded {len(config.email)} emails from "{config.email_file}"'
                )
            else:
                config.console.print(f'❌ Could not read file "{config.email_file}"')
                sys.exit()

        if config.email:
            for email in config.email:
                config.currentEmail = email
                if config.dump or config.csv or config.pdf or config.json:
                    await create_save_directory(config)
                await verify_email(email, config, session)
                if config.ai:
                    if config.emailFoundAccounts and len(config.emailFoundAccounts) > 2:
                        site_names = [
                            account.get("name", "") for account in config.emailFoundAccounts
                        ]
                        if site_names:
                            prompt = ", ".join(site_names)
                            data = await send_prompt(prompt, session, config)
                            if data:
                                config.ai_analysis = data
                    else:
                        config.console.print(
                            ":warning: Not enough accounts found for AI analysis. Skipping AI features."
                        )

                if config.csv and config.emailFoundAccounts:
                    await save_to_csv(config.emailFoundAccounts, config)
                if config.pdf and config.emailFoundAccounts:
                    await save_to_pdf(config.emailFoundAccounts, "email", config)
                if config.json and config.emailFoundAccounts:
                    await save_to_json(config.emailFoundAccounts, config)
                config.currentEmail = None
                config.emailFoundAccounts = None


if __name__ == "__main__":
    asyncio.run(main())
