from typing import Iterable
from urllib.parse import urlsplit


def get_host(url) -> str:
    return urlsplit(url).netloc


def get_hosts(urls: Iterable[str]) -> set[str]:
    hosts = set()
    for url in urls:
        hosts.add(get_host(url))
    return hosts
