#!/usr/bin/env bash
# Оновлює хаб: серверні сторінки + GitHub-сторінки, комітить і пушить.
set -euo pipefail
cd /root/gh-hub
export GITHUB_TOKEN="$(gh auth token)"
python3 server_scan.py
python3 build.py
git add -A
if git diff --cached --quiet; then
  echo "no changes"
  exit 0
fi
git -c user.email=moskalenko.t.o@gmail.com -c user.name="Fil-m" commit -qm "auto: оновлення хаба сторінок"
git push -q
echo "pushed"
