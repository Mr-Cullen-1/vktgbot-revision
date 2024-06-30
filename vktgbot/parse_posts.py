import re
from typing import Union

import requests
from loguru import logger

from api_requests import get_video_url
from config import REQ_VERSION, VK_TOKEN, REMOVE_WATERMARKS, DOWNLOAD_VIDEOS, DOWNLOAD_VK_CLIPS, BLACKLIST
from tools import add_urls_to_text, prepare_text_for_html, prepare_text_for_reposts, reformat_vk_links

def parse_post(item: dict, repost_exists: bool, item_type: str, group_name: str) -> Union[dict, None]:
    text = prepare_text_for_html(item["text"])
    if repost_exists:
        text = prepare_text_for_reposts(text, item, item_type, group_name)

    text = reformat_vk_links(text)

    if any(word in text for word in BLACKLIST):
        logger.info("Post contains blacklisted words and will not be published.")
        return None

    urls: list = []
    videos: list = []
    photos: list = []
    docs: list = []

    if "attachments" in item:
        parse_attachments(item["attachments"], text, urls, videos, photos, docs)

    text = add_urls_to_text(text, urls, videos)
    logger.info(f"{item_type.capitalize()} parsing is complete.")
    return {"text": text, "photos": photos, "docs": docs, "videos": videos}

def parse_attachments(attachments, text, urls, videos, photos, docs):
    for attachment in attachments:
        if attachment["type"] == "link":
            url = get_url(attachment, text)
            if url:
                urls.append(url)
        elif attachment["type"] == "video":
            video = get_video(attachment)
            if video:
                videos.append(video)
        elif attachment["type"] == "photo":
            photo = get_photo(attachment)
            if photo:
                photos.append(photo)
        elif attachment["type"] == "doc":
            doc = get_doc(attachment["doc"])
            if doc:
                docs.append(doc)

def get_url(attachment: dict, text: str) -> Union[str, None]:
    url = attachment["link"]["url"]
    return url if url not in text else None

def get_video(attachment: dict) -> str:
    owner_id = attachment["video"]["owner_id"]
    video_id = attachment["video"]["id"]
    access_key = attachment["video"].get("access_key", "")

    video_url = get_video_url(VK_TOKEN, REQ_VERSION, owner_id, video_id, access_key)
    if DOWNLOAD_VIDEOS and video_url:
        return download_video(video_url)
    elif DOWNLOAD_VK_CLIPS and attachment["video"]["type"] == "short_video":
        return f"https://vk.com/clip{owner_id}_{video_id}"
    else:
        return f"https://vk.com/video{owner_id}_{video_id}"

def download_video(url: str) -> str:
    import yt_dlp
    ydl_opts = {'outtmpl': './temp/%(title)s.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info_dict)

def get_photo(attachment: dict) -> Union[str, None]:
    sizes = attachment["photo"]["sizes"]
    types = ["w", "z", "y", "x", "r", "q", "p", "o", "m", "s"]

    for type_ in types:
        if next(
            (item for item in sizes if item["type"] == type_),
            False,
        ):
            return re.sub(
                "&([a-zA-Z]+(_[a-zA-Z]+)+)=([a-zA-Z0-9-_]+)",
                "",
                next(
                    (item for item in sizes if item["type"] == type_),
                    False,
                )["url"],
            )
    else:
        return None

def get_doc(doc: dict) -> Union[dict, None]:
    if doc["size"] > 50000000:
        logger.info(f"The document was skipped due to its size exceeding the 50MB limit: {doc['size']=}.")
        return None
    else:
        response = requests.get(doc["url"])

        with open(f'./temp/{doc["title"]}', "wb") as file:
            file.write(response.content)

    return {"title": doc["title"], "url": doc["url"]}
