import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer

from .main_async import main_async


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
