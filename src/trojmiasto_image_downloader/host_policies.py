from typing import Iterable, Self
from urllib.parse import unquote, urlparse
import asyncio
import time
import re

import typer
from aiohttp import ClientSession, ClientConnectorError, ClientError


class RateLimiter:
    def __init__(self, delay: int):
        self._delay = delay  # ms
        self._lock = asyncio.Lock()
        self._last_finish = 0.0

    async def __aenter__(self):
        await self._lock.acquire()

        now = time.monotonic()
        wait_time = self._delay - (now - self._last_finish)
        if wait_time > 0:
            await asyncio.sleep(wait_time / 1000)  # convert ms to s

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._last_finish = time.monotonic()
        self._lock.release()

    def get_delay(self) -> int:
        return self._delay


class HostPolicy:
    def __init__(self):
        self._rate_limiter: RateLimiter | None = None
        self.rules: list[tuple[re.Pattern[str], bool, int]] = []
        self._robots_txt_delay: int = 0  # ms

    def _add_rule(self, pattern: str, allow: bool):
        if pattern == "":
            return

        # convert robots pattern -> regex
        regex = re.escape(pattern)
        regex = regex.replace(r"\*", ".*")

        if pattern.endswith("$"):
            regex = regex[:-2] + "$"
        else:
            regex = "^" + regex

        compiled = re.compile(regex)

        self.rules.append((compiled, allow, len(pattern)))

    def _parse_robots_txt(
        self, useragent: str, default_delay: int, robots_txt: str
    ) -> int:
        active = False
        for line in robots_txt.splitlines():
            # remove comment
            i = line.find("#")
            if i >= 0:
                line = line[:i]
            line = line.strip()

            if not line:
                active = False
                continue

            line = line.split(":", maxsplit=1)
            if len(line) != 2:
                continue

            key = line[0].strip().lower()
            value = unquote(line[1].strip()).strip()

            if key == "user-agent" and (value == "*" or useragent.startswith(value)):
                active = True
                continue

            if not active:
                continue

            if key == "disallow":
                self._add_rule(value, False)
            elif key == "allow":
                self._add_rule(value, True)
            elif key == "crawl-delay" and value.isdigit():
                self._robots_txt_delay = max(
                    self._robots_txt_delay, int(value) * 1000
                )  # convert s to ms

        final_delay = max(self._robots_txt_delay, default_delay)  # ms
        return final_delay

    def _create_rate_limiter(self, delay: int):
        if delay > 0:
            self._rate_limiter = RateLimiter(delay)

    def get_rate_limiter(self) -> RateLimiter | None:
        return self._rate_limiter

    def can_fetch(self, url: str) -> bool:
        path = urlparse(url).path

        matched_rule = None

        for regex, allow, length in self.rules:
            if regex.match(path):
                if matched_rule is None or length > matched_rule[2]:
                    matched_rule = (regex, allow, length)

        if matched_rule is None:
            return True

        return matched_rule[1]

    def get_robots_txt_delay(self) -> int:
        return self._robots_txt_delay

    @classmethod
    def from_robots_txt(
        cls, useragent: str, default_delay: int, robots_txt: str
    ) -> Self:
        obj = cls()
        final_delay = obj._parse_robots_txt(useragent, default_delay, robots_txt)
        obj._create_rate_limiter(final_delay)
        return obj

    @classmethod
    def from_delay(cls, default_delay: int) -> Self:
        obj = cls()
        obj._create_rate_limiter(default_delay)
        return obj


async def get_host_policies(
    session: ClientSession,
    useragent: str,
    respect_robots_txt: bool,
    default_delay: int,
    hosts: Iterable[str],
):
    if not respect_robots_txt:
        print("Ignoring robots.txt files (user intent).")
        return {host: HostPolicy.from_delay(default_delay) for host in hosts}

    host_policies = dict()
    for host in hosts:
        print(f"Fetching robots.txt for {host}...")
        robots_txt_url = f"https://{host}/robots.txt"

        try:
            async with session.get(robots_txt_url) as response:
                if response.status == 404:
                    host_policies[host] = HostPolicy.from_delay(default_delay)
                    print(
                        f"Robots.txt for host {host} not found. Leaving the default delay of {default_delay}ms."
                    )
                    continue

                response.raise_for_status()

                robots_file = await response.text()
                host_policy = HostPolicy.from_robots_txt(
                    useragent, default_delay, robots_file
                )
                host_policies[host] = host_policy

                robots_txt_delay = host_policy.get_robots_txt_delay()

                if robots_txt_delay > 0 and robots_txt_delay > default_delay:
                    print(
                        f"Fetched robots.txt for {host}. Crawl-delay specified: {robots_txt_delay}ms. Delay overwritten for this host."
                    )
                elif robots_txt_delay > 0:
                    print(
                        f"Fetched robots.txt for {host}. Crawl-delay specified: {robots_txt_delay}ms. Leaving the default delay of {default_delay}ms."
                    )
                else:
                    print(
                        f"Fetched robots.txt for {host}. Crawl-delay not specified. Leaving the default delay of {default_delay}ms."
                    )

        except TimeoutError:
            print(f"Failed to fetch robots.txt for {host} (timed out).")
            raise typer.Exit(1)
        except (ClientConnectorError, ClientError) as e:
            print(f"Failed to fetch robots.txt for {host} ({e}).")
            raise typer.Exit(1)

    return host_policies
