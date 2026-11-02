#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сканує серверні сайти (Caddy) і пише server_pages.json для хаба."""
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

CADDY = "/etc/caddy/Caddyfile"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_pages.json")
SKIP = re.compile(r"(^|/)(node_modules|\.git|build|dist|vendor)(/|$)")


def blocks(text):
    out, cur, depth = [], None, 0
    for line in text.splitlines():
        s = line.strip()
        if depth == 0 and s.endswith("{") and " " not in s[:-1].strip():
            cur = {"domain": s[:-1].strip(), "root": None, "proxy": None}
            depth = 1
            continue
        if cur is not None:
            depth += s.count("{") - s.count("}")
            m = re.match(r"root\s+\*\s+(\S+)", s)
            if m:
                cur["root"] = m.group(1)
            m = re.match(r"reverse_proxy\s+(\S+)", s)
            if m:
                cur["proxy"] = m.group(1)
            if depth <= 0:
                out.append(cur)
                cur, depth = None, 0
    return out


def get_title(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read(120000).decode("utf-8", "ignore")
            code = r.status
        m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
        return (re.sub(r"\s+", " ", m.group(1)).strip() if m else ""), code
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception:
        return "", 0


def scan(root):
    pages = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "build", "dist", "vendor")]
        for f in filenames:
            if not f.lower().endswith(".html"):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            if SKIP.search(rel):
                continue
            try:
                mt = datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).strftime("%Y-%m-%d")
            except OSError:
                mt = ""
            pages.append({"path": rel, "date": mt, "size": os.path.getsize(p)})
    pages.sort(key=lambda x: (x["date"], x["path"]), reverse=True)
    return pages


def url_for(domain, path):
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    return f"https://{domain}/" + urllib.parse.quote(path.replace(os.sep, "/"))


def main():
    sites = []
    for b in blocks(open(CADDY, encoding="utf-8", errors="ignore").read()):
        d = b["domain"]
        if "sslip.io" not in d and "116-203-217-173" not in d:
            continue
        site = {"domain": d, "proxy": b["proxy"], "pages": []}
        if b["root"] and os.path.isdir(b["root"]):
            site["pages"] = [
                {"path": p["path"], "date": p["date"], "url": url_for(d, p["path"])}
                for p in scan(b["root"])
            ]
            site["root"] = b["root"]
        site["title"], site["status"] = get_title(f"https://{d}/")
        sites.append(site)
    sites.sort(key=lambda s: s["domain"])
    json.dump({"sites": sites, "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(len(s["pages"]) for s in sites)
    print(f"{len(sites)} сайтів · {total} сторінок → {OUT}")


if __name__ == "__main__":
    main()
