from typing import Annotated, Callable
import asyncio
import os
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

import aiohttp
from aiohttp import ClientSession, ClientConnectorError, ClientError
import typer
from rich.progress import Progress
from bs4 import BeautifulSoup

from .host_policies import HostPolicy, get_host_policies
from .parsing import get_hosts, get_host


try:
    PKG_VERSION = version("trojmiasto-image-downloader")
except PackageNotFoundError:
    PKG_VERSION = "unknown"

USERAGENT = f"trojmiasto-image-downloader/{PKG_VERSION} (+https://github.com/MatWojewodzki/trojmiasto-image-downloader; contact: matwojewodzki@gmail.com)"


class DownloadResult:
    def __init__(self):
        self.successes = 0
        self.failures = 0

    def register_download_result(self, success: bool):
        if success:
            self.successes += 1
        else:
            self.failures += 1


async def get_img_urls(
    session: ClientSession, article_url: str, start_idx: int | None, end_idx: int | None
) -> tuple[str]:
    try:
        async with session.get(article_url) as response:
            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            tags = soup.find_all("a", class_="photoMarker__link")
            img_urls = tuple(map(lambda tag: tag["href"], tags))

            start_idx = 0 if start_idx is None else start_idx - 1
            end_idx = len(img_urls) if end_idx is None else end_idx - 1

            return img_urls[start_idx:end_idx]

    except TimeoutError:
        print("Failed to fetch the article (timed out).")
        exit(1)
    except (ClientConnectorError, ClientError) as e:
        print(f"Failed to fetch the article ({e}).")
        exit(1)


def prepare_destination_directory(destination_directory: Path):
    destination_directory.mkdir(parents=True, exist_ok=True)


async def download_img(
    session: ClientSession,
    download_result_callback: Callable[[bool], None],
    destination_directory: Path,
    img_url: str,
):
    filename = img_url.split("/")[-1]
    destination_file_path = destination_directory / filename
    try:
        async with session.get(img_url) as response:
            response.raise_for_status()
            with open(destination_file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
            download_result_callback(True)
            print(f"Downloaded {img_url}.")

    except TimeoutError:
        print(f"Failed to download {img_url} (timed out).")
        download_result_callback(False)
    except (ClientConnectorError, ClientError) as e:
        print(f"Failed to download {img_url} ({e}).")
        download_result_callback(False)


async def handle_img_download(
    session: ClientSession,
    download_result_callback: Callable[[bool], None],
    destination_directory: Path,
    img_url: str,
    host_policies: dict[str, HostPolicy],
):
    host_policy = host_policies[get_host(img_url)]

    if not host_policy.can_fetch(img_url):
        print(f"Failed to download {img_url} (forbidden by robots.txt).")
        return

    if host_policy.get_rate_limiter() is not None:  # delay is set for this host
        async with host_policy.get_rate_limiter():
            await download_img(
                session, download_result_callback, destination_directory, img_url
            )
    else:  # delay is not set for this host
        await download_img(
            session, download_result_callback, destination_directory, img_url
        )


async def main_async(
    url: str,
    destination_directory: Path,
    start_idx: int | None,
    end_idx: int | None,
    respect_robots_txt: bool,
    delay: int,
    max_concurrency: int,
    timeout: int,
):
    connector = aiohttp.TCPConnector(
        limit=max_concurrency,
        force_close=True,
    )
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        img_urls = await get_img_urls(session, url, start_idx, end_idx)

        if len(img_urls) == 0:
            print("No images found for this article.")
            exit(0)

        hosts = get_hosts(img_urls)
        print(
            f"Found {len(img_urls)} images from {len(hosts)} host(s) ({', '.join(hosts)})."
        )

        host_policies = await get_host_policies(
            session, USERAGENT, respect_robots_txt, delay, hosts
        )

        prepare_destination_directory(destination_directory)

        download_result = DownloadResult()
        with Progress() as progress:
            task_id = progress.add_task("Downloading images", total=len(img_urls))

            def download_result_callback(success: bool):
                progress.update(task_id, advance=1)
                download_result.register_download_result(success)

            tasks = [
                handle_img_download(
                    session,
                    download_result_callback,
                    destination_directory,
                    url,
                    host_policies,
                )
                for url in img_urls
            ]
            await asyncio.gather(*tasks)

        print(
            f"Successfully downloaded {download_result.successes} image(s), {download_result.failures} failed."
        )


def main(
    article_url: Annotated[
        str,
        typer.Argument(
            help="URL of an article at trojmiasto.pl containing the image gallery."
        ),
    ],
    destination_directory: Annotated[
        Path,
        typer.Argument(
            help="Destination directory to save the downloaded images to. Defaults to the current working directory.",
            default_factory=lambda: os.getcwd(),
            show_default=False,
        ),
    ],
    start_idx: Annotated[
        int | None,
        typer.Option(
            "--start-idx",
            "-s",
            help="Index of the first image to download, counting from one. If not set, downloads images from the first one.",
        ),
    ] = None,
    end_idx: Annotated[
        int | None,
        typer.Option(
            "--end-idx",
            "-e",
            help="Index of the last image to download, counting from one. If not set, downloads images up to the last one.",
        ),
    ] = None,
    respect_robots_txt: Annotated[
        bool,
        typer.Option(
            "--respect-robots-txt/--ignore-robots-txt",
            help="Respect robots.txt rules when making requests (recommended). This will override --delay for the specific hosts if necessary.",
        ),
    ] = True,
    delay: Annotated[
        int,
        typer.Option(
            "--delay",
            "-d",
            help="Number of milliseconds to wait before performing the next request to the same host.",
        ),
    ] = 1000,
    max_concurrency: Annotated[
        int,
        typer.Option(
            "--max-concurrency",
            "-c",
            help="Max number of concurrent connections.",
        ),
    ] = 1,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            "-t",
            help="Timeout in seconds.",
        ),
    ] = 30,
):
    asyncio.run(
        main_async(
            article_url,
            destination_directory,
            start_idx,
            end_idx,
            respect_robots_txt,
            delay,
            max_concurrency,
            timeout,
        )
    )


def app():
    typer.run(main)
