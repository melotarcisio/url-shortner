import requests
from core.settings import settings


ALPHABET = [c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]


def bijective_encode(idx: int):
    if idx == 0:
        return ALPHABET[0]

    s = ""
    base = len(ALPHABET)

    while idx > 0:
        s += ALPHABET[idx % base]
        idx //= base

    return s[::-1]


def bijective_decode(encoded_str: str):
    num = 0
    base = len(ALPHABET)

    for char in encoded_str:
        num = num * base + ALPHABET.index(char)
    return num


def get_url_title(url: str):
    response = requests.get(url)
    title = response.text.split("</title>")[0].split("<title>")[1]
    return title


def get_short_url(encoded_id: str):
    return f"{settings.DOMAIN}/short/{encoded_id}"
