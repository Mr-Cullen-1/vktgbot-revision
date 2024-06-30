import re

def add_urls_to_text(text: str, urls: list, videos: list) -> str:
    if urls:
        text += "\n\n" + "\n".join(urls)
    if videos:
        text += "\n\n" + "\n".join(videos)
    return text

def prepare_text_for_html(text: str) -> str:
    # Преобразование текста в HTML формат
    text = re.sub(r'\n', '<br>', text)
    text = re.sub(r'\[', '&#91;', text)
    text = re.sub(r'\]', '&#93;', text)
    return text

def prepare_text_for_reposts(text: str, item: dict, item_type: str, group_name: str) -> str:
    # Добавление информации о репосте
    repost_text = f"\n\nRepost from {group_name}"
    return text + repost_text

def reformat_vk_links(text: str) -> str:
    # Преобразование ссылок VK
    text = re.sub(r'https?://vk\.com', '', text)
    return text

def split_text(text: str, max_length: int) -> list:
    # Разделение текста на части
    words = text.split()
    chunks = []
    chunk = ""
    for word in words:
        if len(chunk) + len(word) + 1 > max_length:
            chunks.append(chunk)
            chunk = word
        else:
            chunk += " " + word
    if chunk:
        chunks.append(chunk)
    return chunks
