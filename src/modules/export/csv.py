import aiofiles
import os

from .file_operations import generateName
from ..utils.log import logError

async def save_to_csv(results, config):
    """Asynchronously saves results to a CSV file."""
    try:
        filename = generateName(config, "csv")
        path = os.path.join(config.saveDirectory, filename)
        
        # The csv module is synchronous, so we format strings and write them asynchronously.
        header = '"name","url"\n'
        rows = [header]
        for result in results:
            name = str(result.get("name", "")).replace('"', '""')
            url = str(result.get("url", "")).replace('"', '""')
            rows.append(f'"{name}","{url}"\n')

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.writelines(rows)
            
        config.console.print(f"💾  Saved results to '[cyan1]{filename}[/cyan1]'")
        return True
    except Exception as e:
        logError(e, "Couldn't save results to CSV file!", config)
        return False
