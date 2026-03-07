# trojmiasto-image-downloader

A command-line tool for downloading image galleries from the trojmiasto.pl website.
It allows users to easily fetch and save photos from galleries inside articles to their local machine for offline viewing
or archival purposes.

This project is an independent, open-source utility and is not affiliated with, endorsed by, or associated
with trojmiasto.pl. All trademarks and content belong to their respective owners. Users are responsible for ensuring
their use of the tool complies with the website’s terms of service and applicable laws.

## Installation

### Using `uv`

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already. Then:

```console
uv tool install trojmiasto-image-downloader
```

### Using `pipx`

[Install pipx](https://pipx.pypa.io/stable/installation/) if you haven't already. Then:

```console
pipx install trojmiasto-image-downloader
```

### Using `pip`

```console
# Create a virtual environment
python -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the package
pip install trojmiasto-image-downloader
```

## Updating

### Using `uv`

```console
uv tool upgrade trojmiasto-image-downloader
```

### Using `pipx`

```console
pipx upgrade trojmiasto-image-downloader
```

### Using `pip`

```console
# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

pip install --upgrade trojmiasto-image-downloader
```

## Usage

```console
$ tid [OPTIONS] ARTICLE_URL [DESTINATION_DIRECTORY]
```

**Arguments**:

* `ARTICLE_URL`: URL of an article at trojmiasto.pl containing the image gallery.  [required]
* `[DESTINATION_DIRECTORY]`: Destination directory to save the downloaded images to. Defaults to the current working directory.

**Options**:

* `-s, --start-idx INTEGER`: Index of the first image to download, counting from one. If not set, downloads images from the first one.
* `-e, --end-idx INTEGER`: Index of the last image to download, counting from one. If not set, downloads images up to the last one.
* `--respect-robots-txt / --ignore-robots-txt`: Respect robots.txt rules when making requests (recommended). This will override --delay for the specific hosts if necessary.  [default: respect-robots-txt]
* `-d, --delay INTEGER`: Number of milliseconds to wait before performing the next request to the same host.  [default: 1000]
* `-c, --max-concurrency INTEGER`: Max number of concurrent connections.  [default: 1]
* `-t, --timeout INTEGER`: Timeout in seconds.  [default: 30]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

## License

[MIT](LICENSE)
