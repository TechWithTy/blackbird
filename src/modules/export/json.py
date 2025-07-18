import aiofiles
import os
import json

from .file_operations import generateName
from ..utils.log import logError


async def save_to_json(results, config):
    """Asynchronously saves results to a JSON file."""
    try:
        fileName = generateName(config, "json")
        path = os.path.join(config.saveDirectory, fileName)
        
        # Serialize JSON to string in memory (this is synchronous but fast)
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json_data)
            
        config.console.print(f"💾  Saved results to '[cyan1]{fileName}[/cyan1]'")
        return True
    except Exception as e:
        logError(e, "Couldn't save results to JSON file!", config)
        return False
