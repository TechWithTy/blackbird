import os
import time
import asyncio
from rich.text import Text
from rich.live import Live

from ..utils.filter import filterFoundAccounts, applyFilters
from ..utils.parse import extractMetadata
from ..utils.http_client import do_async_request
from ..whatsmyname.list_operations import read_list
from ..utils.input import processInput
from ..utils.log import logError
from ..export.dump import dump_content
from ..utils.precheck import perform_pre_check


# Verify account existence based on list args
async def checkSite(
    site,
    method,
    url,
    session,
    semaphore,
    config,
    data=None,
    headers=None,
):
    returnData = {
        "name": site["name"],
        "url": url,
        "category": site["cat"],
        "status": "NONE",
        "metadata": None,
    }
    async with semaphore:
        if site["pre_check"]:
            authenticated_headers = perform_pre_check(
                site["pre_check"], headers, config
            )
            headers = authenticated_headers
            if not headers:
                returnData["status"] = "ERROR"
                return returnData

        response, content, _ = await do_async_request(
            session, method, url, headers=headers, proxy=config.proxy, timeout=config.timeout
        )
        if response is None:
            returnData["status"] = "ERROR"
            return returnData
        try:
            if response:
                if (site["e_string"] in response["content"]) and (
                    site["e_code"] == response["status_code"]
                ):
                    if (site["m_string"] not in response["content"]) and (
                        site["m_code"] != response["status_code"]
                    ):
                        returnData["status"] = "FOUND"
                        config.console.print(
                            rf"  ✔️  \[[cyan1]{site['name']}[/cyan1]] [bright_white]{response['url']}[/bright_white]"
                        )
                        if site["metadata"]:
                            extractedMetadata = extractMetadata(
                                site["metadata"], response, site["name"], config
                            )
                            extractedMetadata.sort(key=lambda x: x["name"])
                            returnData["metadata"] = extractedMetadata
                        # Save response content to a .HTML file
                        if config.dump:
                            path = os.path.join(
                                config.saveDirectory, f"dump_{config.currentEmail}"
                            )

                            result = await dump_content(path, site, response, config)
                            if result and config.verbose:
                                config.console.print(
                                    "      💾  Saved HTML data from found account"
                                )
                else:
                    returnData["status"] = "NOT-FOUND"
                    if config.verbose:
                        config.console.print(
                            f"  ❌ [[blue]{site['name']}[/blue]] [bright_white]{response['url']}[/bright_white]"
                        )
                return returnData
        except Exception as e:
            logError(e, f"Coudn't check {site['name']} {url}", config)
            return returnData


# Control survey on list sites
async def fetchResults(email, config, session):
    originalEmail = email
    tasks = []
    semaphore = asyncio.Semaphore(config.max_concurrent_requests)
    total_sites = len(config.email_sites)
    completed = 0
    results = []

    def render():
        percent = int((completed / total_sites) * 100)
        return Text.from_markup(
            f"🛰️  Enumerating accounts with email [cyan1]\"{originalEmail}\"[/cyan1] — [green1]{percent}%[/green1] ({completed}/{total_sites})"
        )

    async def wrappedCheck(site):
        nonlocal completed
        if site["input_operation"] is not None:
            email_processed = processInput(originalEmail, site["input_operation"], config)
        else:
            email_processed = originalEmail

        url = site["uri_check"].replace("{account}", email_processed)
        data = site["data"].replace("{account}", email_processed) if site["data"] else None
        headers = site["headers"] if site["headers"] else None

        result = await checkSite(
            site=site,
            method=site["method"],
            url=url,
            session=session,
            semaphore=semaphore,
            config=config,
            data=data,
            headers=headers,
        )
        completed += 1
        return result

    tasks = [wrappedCheck(site) for site in config.email_sites]

    with Live(render(), refresh_per_second=10, console=config.console) as live:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            live.update(render())

    return {"results": results, "email": originalEmail}


# Start email check and presents results to user
async def verify_email(email, config, session):
    data = await read_list("email", config)
    sitesToSearch = data["sites"]
    config.email_sites = applyFilters(sitesToSearch, config)

    start_time = time.time()
    results = await fetchResults(email, config, session)
    end_time = time.time()

    config.console.print(
        f":chequered_flag: Check completed in {round(end_time - start_time, 1)} seconds ({len(results['results'])} sites)"
    )

    if config.dump:
        config.console.print(
            f"💾  Dump content saved to '[cyan1]{config.currentEmail}_{config.dateRaw}_blackbird/dump_{config.currentEmail}[/cyan1]'"
        )

    # Filter results to only found accounts
    foundAccounts = list(filter(filterFoundAccounts, results["results"]))
    config.emailFoundAccounts = foundAccounts

    if len(foundAccounts) <= 0:
        config.console.print("⭕ No accounts were found for the given email")

    return foundAccounts
