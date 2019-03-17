from telethon import events
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from gsearch.googlesearch import search
from google_images_download import google_images_download
import json
import os
from PIL import Image
import requests
from telegraph import upload_file


def progress(current, total):
    logger.info("Downloaded {} of {}\nCompleted {}".format(current, total, (current / total) * 100))


@borg.on(events.NewMessage(pattern=r"\.google search (.*)", outgoing=True))
@borg.on(events.MessageEdited(pattern=r"\.google search (.*)", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    await event.edit("Processing ...")
    input_str = event.pattern_match.group(1) # + " -inurl:(htm|html|php|pls|txt) intitle:index.of \"last modified\" (mkv|mp4|avi|epub|pdf|mp3)"
    search_results = search(input_str, num_results=Config.TG_GLOBAL_ALBUM_LIMIT)
    output_str = " "
    for text, url in search_results:
        output_str += " 👉🏻  [{}]({}) \n\n".format(text, url)
    end = datetime.now()
    ms = (end - start).seconds
    await event.edit("searched Google for {} in {} seconds. \n{}".format(input_str, ms, output_str), link_preview=False)
    await asyncio.sleep(5)
    await event.edit("Google: {}\n{}".format(input_str, output_str), link_preview=False)


@borg.on(events.NewMessage(pattern=r"\.google image (.*)", outgoing=True))
@borg.on(events.MessageEdited(pattern=r"\.google image (.*)", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    await event.edit("Processing ...")
    input_str = event.pattern_match.group(1)
    response = google_images_download.googleimagesdownload()
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    arguments = {
        "keywords": input_str,
        "limit": Config.TG_GLOBAL_ALBUM_LIMIT,
        "format": "jpg",
        "delay": 1,
        "safe_search": True,
        "output_directory": Config.TMP_DOWNLOAD_DIRECTORY
    }
    paths = response.download(arguments)
    lst = paths[input_str]
    await borg.send_file(
        event.chat_id,
        lst,
        caption=input_str,
        reply_to=event.message.id,
        progress_callback=progress
    )
    for each_file in lst:
        os.remove(each_file)
    end = datetime.now()
    ms = (end - start).seconds
    await event.edit("searched Google for {} in {} seconds.".format(input_str, ms), link_preview=False)
    await asyncio.sleep(5)
    await event.delete()


@borg.on(events.NewMessage(pattern=r"\.google reverse search", outgoing=True))
@borg.on(events.MessageEdited(pattern=r"\.google reverse search", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    SEARCH_URL = "https://www.google.com/searchbyimage?image_url={}"
    OUTPUT_STR = "Reply to an image to do Google Reverse Search"
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        previous_message_text = previous_message.message
        if previous_message.media:
            downloaded_file_name = await borg.download_media(
                previous_message,
                Config.TMP_DOWNLOAD_DIRECTORY
            )
            im = Image.open(downloaded_file_name).convert("RGB")
            # https://stackoverflow.com/a/33298016/4723940
            im.save(downloaded_file_name + ".jpg","jpeg")
            # os.rename(downloaded_file_name, downloaded_file_name + ".jpg")
            downloaded_file_name = downloaded_file_name + ".jpg"
            try:
                media_urls = upload_file(downloaded_file_name)
            except Exception as exc:
                await event.edit("ERROR: " + str(exc))
                os.remove(downloaded_file_name)
                return False
            else:
                os.remove(downloaded_file_name)
                previous_message_text = "https://telegra.ph/{}".format(media_urls[0][1:])
        logger.info(previous_message_text)
        request_url = SEARCH_URL.format(previous_message_text)
        google_rs_response = requests.get(request_url, allow_redirects=False)
        the_location = google_rs_response.headers.get("Location")
        OUTPUT_STR = "Open this [link]({})".format(the_location)
    end = datetime.now()
    ms = (end - start).seconds
    await event.edit(OUTPUT_STR)
