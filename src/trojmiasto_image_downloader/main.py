import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer

from .main_async import main_async
from .parsing import get_host
from .metadata import PKG_VERSION


def article_url_callback(url: str) -> str:
    host = get_host(url)
    if not host.endswith("trojmiasto.pl"):
        raise typer.BadParameter("url must point to trojmiasto.pl")
    return url


def version_callback(value: bool):
    if value:
        print(PKG_VERSION)
        raise typer.Exit(0)


def main(
    article_url: Annotated[
        str,
        typer.Argument(
            help="URL of an article at trojmiasto.pl containing the image gallery.",
            callback=article_url_callback,
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
    _: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Display the current version and exit.",
            is_eager=True,
            show_default=False,
            callback=version_callback,
        ),
    ] = False,
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
