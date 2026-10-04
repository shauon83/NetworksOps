#!/usr/bin/env python3
"""Read-only ipTIME EasyMesh topology checker.

This calls the same endpoint used by the Easy Mesh management page:
  /easymesh/api.cgi?key=topology

It deliberately prints only connection diagnostics; it does not print Wi-Fi
passwords, cookies, MAC addresses, or the complete router response.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

DEFAULT_URL = os.environ.get("IPTIME_URL", "http://YOUR_ROUTER_IP").rstrip("/")
DEFAULT_TARGETS = tuple(
    name.strip()
    for name in os.environ.get("IPTIME_TARGETS", "agent-living,agent-room").split(",")
    if name.strip()
)


def fetch_topology(base_url: str, timeout: int, cookie: str | None) -> dict[str, Any]:
    endpoint = f"{base_url}/easymesh/api.cgi?{urlencode({'key': 'topology'})}"
    # Do not inherit a corporate/system HTTP proxy for a private LAN address.
    # Some ipTIME firmware is also more reliable with the same basic headers
    # used by its web management page.
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Referer": f"{base_url}/",
        "Origin": base_url,
        "Connection": "close",
    }
    if cookie:
        headers["Cookie"] = cookie
    request = Request(endpoint, headers=headers, method="GET")
    direct_opener = build_opener(ProxyHandler({}))
    with direct_opener.open(request, timeout=timeout) as response:
        status = getattr(response, "status", "unknown")
        content_type = response.headers.get("Content-Type", "not supplied")
        body = response.read()

    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        kind = "empty" if not body.strip() else "non-JSON"
        raise ValueError(
            f"Topology endpoint returned {kind} data "
            f"(HTTP {status}, Content-Type: {content_type}, {len(body)} bytes). "
            "This usually means the router requires the browser login session."
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("Topology response is not a JSON object")
    return payload


def text(value: Any, empty: str = "-") -> str:
    if value is None or value == "":
        return empty
    return str(value)


def is_connected(agent: dict[str, Any]) -> bool:
    return (
        bool(agent.get("ip"))
        and agent.get("connection") in {"WIRED", "WIRELESS"}
        and agent.get("status") not in {"MISSING", ""}
    )


def show_snapshot(payload: dict[str, Any], targets: tuple[str, ...]) -> bool:
    header = payload.get("header", {})
    controllers = payload.get("controller", [])
    agents = payload.get("agent", [])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[{now}] EasyMesh topology")
    print(f"  header.msg: {text(header.get('msg'))}")

    if controllers:
        controller = controllers[0]
        print(
            "  controller: "
            f"{text(controller.get('nickname'))} | "
            f"status={text(controller.get('status'))} | "
            f"connection={text(controller.get('connection'))}"
        )
    else:
        print("  controller: NOT FOUND")

    by_name = {
        agent.get("nickname"): agent
        for agent in agents
        if isinstance(agent, dict) and agent.get("nickname")
    }

    all_ready = True
    for target in targets:
        agent = by_name.get(target)
        if agent is None:
            print(f"  agent: {target} | NOT_REGISTERED_IN_CONTROLLER")
            all_ready = False
            continue

        state = "CONNECTED" if is_connected(agent) else "NOT_READY"
        print(
            f"  agent: {target} | {state} | "
            f"ip={text(agent.get('ip'))} | "
            f"connection={text(agent.get('connection'))} | "
            f"status={text(agent.get('status'))} | "
            f"backhaul={text(agent.get('current-bh'))}"
        )
        all_ready = all_ready and is_connected(agent)

    extra_agents = sorted(set(by_name) - set(targets))
    if extra_agents:
        print("  other registered agents: " + ", ".join(extra_agents))

    return all_ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Read ipTIME EasyMesh topology safely")
    parser.add_argument("--url", default=DEFAULT_URL, help="Controller URL (default: %(default)s)")
    parser.add_argument("--timeout", type=int, default=5, help="HTTP timeout in seconds")
    parser.add_argument("--watch", action="store_true", help="Poll until every target is connected")
    parser.add_argument("--interval", type=int, default=20, help="Polling interval for --watch")
    parser.add_argument(
        "--cookie",
        default=os.environ.get("IPTIME_COOKIE"),
        help="Optional browser Cookie header when the controller requires login",
    )
    parser.add_argument(
        "--targets",
        default=",".join(DEFAULT_TARGETS),
        help="Comma-separated agent nicknames to check",
    )
    args = parser.parse_args()
    targets = tuple(name.strip() for name in args.targets.split(",") if name.strip())

    while True:
        try:
            payload = fetch_topology(args.url.rstrip("/"), args.timeout, args.cookie)
            all_ready = show_snapshot(payload, targets)
            if all_ready:
                print("\nAll requested agents are connected.")
                return 0
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"\nRequest failed: {exc}", file=sys.stderr)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"\nUnexpected response: {exc}", file=sys.stderr)

        if not args.watch:
            return 1
        print(f"Retrying in {args.interval} seconds ...")
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
