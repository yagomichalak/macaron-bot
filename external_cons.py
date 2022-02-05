import aiomysql
import asyncio
import os
from typing import List, Any

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

async def the_drive() -> Any:
    """ Gets the GoogleDrive connection. """

    gauth = GoogleAuth()
    # gauth.LocalWebserverAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # This is what solved the issues:
        gauth.GetFlow()
        gauth.flow.params.update({'access_type': 'offline'})
        gauth.flow.params.update({'approval_prompt': 'force'})

        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:

        # Refresh them if expired
        gauth.Refresh()
    else:

        # Initialize the saved creds
        gauth.Authorize()

    # Save the current credentials to a file
    gauth.SaveCredentialsFile("mycreds.txt")

    drive = GoogleDrive(gauth)
    return drive


loop = asyncio.get_event_loop()

async def the_database() -> List[Any]:
    """ Gives the databse connection. """

    pool = await aiomysql.create_pool(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        loop=loop
    )
    db = await pool.acquire()
    mycursor = await db.cursor()
    return mycursor, db