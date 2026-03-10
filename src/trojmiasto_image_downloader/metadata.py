from importlib.metadata import version, PackageNotFoundError


try:
    PKG_VERSION = version("trojmiasto-image-downloader")
except PackageNotFoundError:
    PKG_VERSION = "unknown"

USERAGENT = f"trojmiasto-image-downloader/{PKG_VERSION} (+https://github.com/MatWojewodzki/trojmiasto-image-downloader; contact: matwojewodzki@gmail.com)"
