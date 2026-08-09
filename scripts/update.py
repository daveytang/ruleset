#!/usr/bin/env python3
"""Fetch, merge, and export CN IP / CN domain / GFW domain rulesets."""

from __future__ import annotations

import ipaddress
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CUSTOM = ROOT / "custom"

SOURCES = {
    "cn_ip_v4": [
        # BGP-based Mainland China IPv4 prefixes
        "https://raw.githubusercontent.com/misakaio/chnroutes2/master/chnroutes.txt",
        # APNIC delegated fallback / supplement
        "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
    ],
    "cn_ip_v6": [
        "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china6.txt",
    ],
    "cn_domain": [
        # China direct domains (dnsmasq-china-list accelerated domains)
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf",
        # Apple / Google CN domains from same project
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf",
        "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf",
    ],
    "gfw_domain": [
        # GFWList converted domains
        "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/gfw.txt",
        # Extra blocked domains
        "https://raw.githubusercontent.com/Loyalsoldier/cn-blocked-domain/release/domains.txt",
    ],
}

USER_AGENT = "cn-ruleset-updater/1.0 (+https://github.com/daveytang/ruleset)"
TIMEOUT = 120


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_optional(url: str) -> str:
    try:
        text = fetch(url)
        print(f"  OK  {url} ({len(text.splitlines())} lines)")
        return text
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  FAIL {url}: {exc}", file=sys.stderr)
        return ""


def parse_cidrs(text: str) -> set[str]:
    result: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        # Strip common prefixes: IP-CIDR, IP-CIDR6, GEOIP, etc.
        line = re.sub(r"^(?:IP-CIDR6?|ip-cidr6?)\s*,?\s*", "", line, flags=re.I)
        line = line.split(",")[0].split()[0].strip()
        if "/" not in line:
            # bare IP → /32 or /128
            try:
                ip = ipaddress.ip_address(line)
                line = f"{ip}/32" if ip.version == 4 else f"{ip}/128"
            except ValueError:
                continue
        try:
            net = ipaddress.ip_network(line, strict=False)
            result.add(str(net))
        except ValueError:
            continue
    return result


def aggregate_cidrs(cidrs: set[str], version: int) -> list[str]:
    nets = []
    for c in cidrs:
        try:
            n = ipaddress.ip_network(c, strict=False)
            if n.version == version:
                nets.append(n)
        except ValueError:
            continue
    collapsed = list(ipaddress.collapse_addresses(nets))
    collapsed.sort(key=lambda n: (int(n.network_address), n.prefixlen))
    return [str(n) for n in collapsed]


DOMAIN_RE = re.compile(
    r"^(?:DOMAIN(?:-SUFFIX|-KEYWORD)?|HOST(?:-SUFFIX)?|server=/.*/|"
    r"\|\||@@\|\||\*\.)?"
    r"([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+)"
    r"(?:[/\^\$\|,\s].*)?$",
    re.I,
)


def parse_domains(text: str) -> set[str]:
    result: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!") or line.startswith("["):
            continue
        # dnsmasq: server=/example.com/114.114.114.114
        m = re.match(r"^server=/([^/]+)/", line, re.I)
        if m:
            host = m.group(1).lower().lstrip(".")
            if "." in host and not host.startswith("*"):
                result.add(host)
            continue
        # Clash payload style: - '+.example.com' or - example.com
        line = re.sub(r"^-\s*", "", line)
        line = line.strip("'\"")
        line = line.lstrip("+.")
        # DOMAIN-SUFFIX,example.com
        line = re.sub(r"^(?:DOMAIN(?:-SUFFIX|-KEYWORD)?|HOST(?:-SUFFIX)?)\s*,\s*", "", line, flags=re.I)
        line = line.split(",")[0].strip().lower()
        line = line.lstrip(".")
        if not line or "*" in line or "/" in line or " " in line:
            continue
        if line.startswith("http:") or line.startswith("https:"):
            continue
        # Reject pure IPs
        try:
            ipaddress.ip_address(line)
            continue
        except ValueError:
            pass
        if "." not in line:
            continue
        if re.fullmatch(r"[a-z0-9.-]+", line):
            result.add(line)
    return result


def load_custom(name: str) -> set[str]:
    path = CUSTOM / name
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    if "ip" in name:
        return parse_cidrs(text)
    return parse_domains(text)


def write_lines(path: Path, lines: list[str], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    body = "\n".join(
        [
            f"# {header}",
            f"# Updated: {stamp}",
            f"# Count: {len(lines)}",
            "#",
            *lines,
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(lines)})")


def write_clash_domain(path: Path, domains: list[str], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# {header}",
        f"# Updated: {stamp}",
        f"# Count: {len(domains)}",
        "payload:",
        *[f"  - '+.{d}'" for d in domains],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(domains)})")


def write_clash_ip(path: Path, cidrs: list[str], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# {header}",
        f"# Updated: {stamp}",
        f"# Count: {len(cidrs)}",
        "payload:",
        *[f"  - '{c}'" for c in cidrs],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(cidrs)})")


def write_surge_domain(path: Path, domains: list[str], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# {header}",
        f"# Updated: {stamp}",
        f"# Count: {len(domains)}",
        *[f"DOMAIN-SUFFIX,{d}" for d in domains],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(domains)})")


def write_surge_ip(path: Path, cidrs: list[str], header: str, v6: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    kind = "IP-CIDR6" if v6 else "IP-CIDR"
    lines = [
        f"# {header}",
        f"# Updated: {stamp}",
        f"# Count: {len(cidrs)}",
        *[f"{kind},{c},no-resolve" for c in cidrs],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(cidrs)})")


def write_singbox_domain(path: Path, domains: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "rules": [{"domain_suffix": domains}],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(domains)})")


def write_singbox_ip(path: Path, cidrs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "rules": [{"ip_cidr": cidrs}],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(cidrs)})")


def collect(kind: str, parser) -> set[str]:
    print(f"\n== Fetching {kind} ==")
    items: set[str] = set()
    for url in SOURCES[kind]:
        text = fetch_optional(url)
        if text:
            items |= parser(text)
    return items


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)

    cn_v4 = collect("cn_ip_v4", parse_cidrs) | load_custom("cn_ip_extra.txt")
    cn_v4 -= load_custom("cn_ip_exclude.txt")
    cn_v4_list = aggregate_cidrs(cn_v4, 4)

    cn_v6 = collect("cn_ip_v6", parse_cidrs) | load_custom("cn_ip6_extra.txt")
    cn_v6 -= load_custom("cn_ip6_exclude.txt")
    cn_v6_list = aggregate_cidrs(cn_v6, 6)

    cn_dom = collect("cn_domain", parse_domains) | load_custom("cn_domain_extra.txt")
    cn_dom -= load_custom("cn_domain_exclude.txt")
    cn_dom_list = sorted(cn_dom)

    gfw_dom = collect("gfw_domain", parse_domains) | load_custom("gfw_domain_extra.txt")
    gfw_dom -= load_custom("gfw_domain_exclude.txt")
    # Prefer CN direct over GFW when conflict
    gfw_dom -= cn_dom
    gfw_dom_list = sorted(gfw_dom)

    if not cn_v4_list:
        print("ERROR: empty CN IPv4 list", file=sys.stderr)
        return 1
    if not cn_dom_list:
        print("ERROR: empty CN domain list", file=sys.stderr)
        return 1
    if not gfw_dom_list:
        print("ERROR: empty GFW domain list", file=sys.stderr)
        return 1

    # Plain text
    write_lines(DIST / "cn_ip.txt", cn_v4_list, "Mainland China IPv4 CIDR")
    write_lines(DIST / "cn_ip6.txt", cn_v6_list, "Mainland China IPv6 CIDR")
    write_lines(DIST / "cn_domain.txt", cn_dom_list, "China direct domains")
    write_lines(DIST / "gfw_domain.txt", gfw_dom_list, "GFW / blocked domains")

    # Clash / Mihomo
    write_clash_ip(DIST / "clash" / "cn_ip.yaml", cn_v4_list, "CN IPv4 for Clash")
    write_clash_ip(DIST / "clash" / "cn_ip6.yaml", cn_v6_list, "CN IPv6 for Clash")
    write_clash_domain(DIST / "clash" / "cn_domain.yaml", cn_dom_list, "CN domains for Clash")
    write_clash_domain(DIST / "clash" / "gfw_domain.yaml", gfw_dom_list, "GFW domains for Clash")

    # Surge
    write_surge_ip(DIST / "surge" / "cn_ip.list", cn_v4_list, "CN IPv4 for Surge")
    write_surge_ip(DIST / "surge" / "cn_ip6.list", cn_v6_list, "CN IPv6 for Surge", v6=True)
    write_surge_domain(DIST / "surge" / "cn_domain.list", cn_dom_list, "CN domains for Surge")
    write_surge_domain(DIST / "surge" / "gfw_domain.list", gfw_dom_list, "GFW domains for Surge")

    # sing-box rule-set (source JSON)
    write_singbox_ip(DIST / "sing-box" / "cn_ip.json", cn_v4_list)
    write_singbox_ip(DIST / "sing-box" / "cn_ip6.json", cn_v6_list)
    write_singbox_domain(DIST / "sing-box" / "cn_domain.json", cn_dom_list)
    write_singbox_domain(DIST / "sing-box" / "gfw_domain.json", gfw_dom_list)

    meta = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "cn_ip": len(cn_v4_list),
            "cn_ip6": len(cn_v6_list),
            "cn_domain": len(cn_dom_list),
            "gfw_domain": len(gfw_dom_list),
        },
        "sources": SOURCES,
    }
    (DIST / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nDone. meta={meta['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
