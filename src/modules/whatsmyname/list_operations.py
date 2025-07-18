import os
import sys
import json
import aiofiles
import aiohttp

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.http_client import do_async_request
from utils.hash import hashJSON
from utils.log import logError


# Read list file and return content
async def read_list(option, config):
    path = None
    if option == "username":
        path = config.USERNAME_LIST_PATH
    elif option == "email":
        path = config.EMAIL_LIST_PATH
    elif option == "metadata":
        path = config.USERNAME_METADATA_LIST_PATH
    else:
        return False

    async with aiofiles.open(path, "r", encoding="UTF-8") as f:
        content = await f.read()
        data = json.loads(content)
    return data


# Download .JSON file list from defined URL
async def download_list(session, config):
    response = await do_async_request("GET", config.USERNAME_LIST_URL, session, config)
    if response and response.get("json"):
        async with aiofiles.open(config.USERNAME_LIST_PATH, "w", encoding="UTF-8") as f:
            await f.write(json.dumps(response["json"], indent=4, ensure_ascii=False))


# Check for changes in remote list
async def check_updates(config):
    if os.path.isfile(config.USERNAME_LIST_PATH):
        config.console.print(":counterclockwise_arrows_button: Checking for updates...")
        try:
            async with aiohttp.ClientSession() as session:
                data = await read_list("username", config)
                currentListHash = hashJSON(data)

                response = await do_async_request(
                    "GET", config.USERNAME_LIST_URL, session, config
                )
                if not response or not response.get("json"):
                    config.console.print(
                        ":police_car_light: Could not fetch remote list."
                    )
                    return

                remoteListHash = hashJSON(response["json"])

                if currentListHash != remoteListHash:
                    config.console.print(":counterclockwise_arrows_button: Updating...")
                    await download_list(session, config)
                else:
                    config.console.print("✔️  Sites List is up to date")
        except Exception as e:
            config.console.print(":police_car_light: Couldn't read local list")
            config.console.print(":down_arrow: Downloading site list")
            logError(e, "Couldn't read local list", config)
            async with aiohttp.ClientSession() as session:
                await download_list(session, config)
    else:
        config.console.print(":globe_with_meridians: Downloading site list")
        async with aiohttp.ClientSession() as session:
            await download_list(session, config)
