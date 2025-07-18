import aiofiles
import os
import json

from ..utils.log import logError


async def dump_content(path, site, response, config):
    """Asynchronously dumps response content to a file."""
    siteName = site["name"].replace(" ", "_")
    content = response.get("content")
    extension = "txt"
    is_json = False

    content_type = response.get("headers", {}).get("Content-Type", "")
    if "application/json" in content_type:
        extension = "json"
        content = response.get("json")
        is_json = True
    elif "text/html" in content_type:
        extension = "html"

    if content is None:
        logError(None, f"No content to dump for site {siteName}", config)
        return False

    fileName = f"{siteName}.{extension}"
    full_path = os.path.join(path, fileName)

    try:
        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            if is_json:
                await f.write(json.dumps(content, indent=4, ensure_ascii=False))
            else:
                await f.write(content)
        return True
    except Exception as e:
        logError(e, f"Couldn't dump data for {siteName}!", config)
        return False
