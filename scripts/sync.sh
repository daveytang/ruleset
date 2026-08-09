#!/usr/bin/env bash
# Mirror Loyalsoldier/v2ray-rules-dat assets into ./release
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/release"
mkdir -p "$OUT"

download() {
  local name="$1"
  shift
  local tmp="$OUT/$name.tmp"
  local ok=0
  for url in "$@"; do
    echo "GET $url"
    if curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 30 --max-time 300 \
      -A "ruleset-mirror/1.0" -o "$tmp" "$url"; then
      if [[ -s "$tmp" ]]; then
        mv -f "$tmp" "$OUT/$name"
        echo "OK  $name ($(wc -c <"$OUT/$name" | tr -d ' ') bytes)"
        ok=1
        break
      fi
    fi
    echo "FAIL $url" >&2
  done
  rm -f "$tmp"
  if [[ "$ok" -ne 1 ]]; then
    echo "ERROR: failed to download $name" >&2
    return 1
  fi
}

download geoip.dat \
  "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geoip.dat"

download geosite.dat \
  "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geosite.dat"

download direct-list.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/direct-list.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/direct-list.txt"

download proxy-list.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/proxy-list.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/proxy-list.txt"

download reject-list.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/reject-list.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/reject-list.txt"

download apple-cn.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/apple-cn.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/apple-cn.txt"

download google-cn.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/google-cn.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/google-cn.txt"

download gfw.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/gfw.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/gfw.txt"

download win-update.txt \
  "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/release/win-update.txt" \
  "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/win-update.txt"

# meta for humans / CI
{
  echo "{"
  echo "  \"updated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"source\": \"https://github.com/Loyalsoldier/v2ray-rules-dat\","
  echo "  \"files\": ["
  first=1
  for f in geoip.dat geosite.dat direct-list.txt proxy-list.txt reject-list.txt apple-cn.txt google-cn.txt gfw.txt win-update.txt; do
    size=$(wc -c <"$OUT/$f" | tr -d ' ')
    sha=$(shasum -a 256 "$OUT/$f" | awk '{print $1}')
    [[ $first -eq 1 ]] || echo ","
    first=0
    printf '    {"name":"%s","bytes":%s,"sha256":"%s"}' "$f" "$size" "$sha"
  done
  echo
  echo "  ]"
  echo "}"
} >"$OUT/meta.json"

echo "Done. Files in $OUT:"
ls -lh "$OUT"
