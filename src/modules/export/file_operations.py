import os
import aiofiles.os
from rich.markup import escape

async def create_save_directory(config):
    """Asynchronously creates the main directory for saving results."""
    folderName = generateName(config)
    strPath = os.path.join(os.getcwd(), "results", folderName)
    config.saveDirectory = strPath

    if not await aiofiles.os.path.exists(strPath):
        await aiofiles.os.makedirs(strPath, exist_ok=True)
        if config.verbose:
            config.console.print(
                escape(f"🆕 Created directory to save search data [{folderName}]")
            )

    if config.dump:
        if config.currentUser:
            await create_dump_directory(config.currentUser, config)
        if config.currentEmail:
            await create_dump_directory(config.currentEmail, config)

    # ! TODO: Re-enable when PDF generation is fixed
    # if config.pdf:
    #     if config.currentUser:
    #         await create_images_directory(config.currentUser, config)
    #     if config.currentEmail:
    #         await create_images_directory(config.currentEmail, config)

    return True

async def create_dump_directory(identifier, config):
    """Asynchronously creates a directory for dumped response content."""
    folderName = f"dump_{identifier}"
    strPath = os.path.join(config.saveDirectory, folderName)
    if not await aiofiles.os.path.exists(strPath):
        if config.verbose:
            config.console.print(
                escape(f"🆕 Created directory to save dump data [{folderName}]")
            )
        await aiofiles.os.makedirs(strPath, exist_ok=True)

async def create_images_directory(identifier, config):
    """Asynchronously creates a directory for downloaded images (for PDFs)."""
    folderName = f"images_{identifier}"
    strPath = os.path.join(config.saveDirectory, folderName)
    if not await aiofiles.os.path.exists(strPath):
        if config.verbose:
            config.console.print(
                escape(f"🆕 Created directory to save images [{folderName}]")
            )
        await aiofiles.os.makedirs(strPath, exist_ok=True)

def generateName(config, extension=None):
    """Generates a filename based on the current search target and date."""
    if config.currentUser:
        folderName = f"{config.currentUser}_{config.dateRaw}_blackbird"
    elif config.currentEmail:
        folderName = f"{config.currentEmail}_{config.dateRaw}_blackbird"
    else:
        folderName = f"blackbird_results_{config.dateRaw}"

    if extension:
        return f"{folderName}.{extension}"

    return folderName
