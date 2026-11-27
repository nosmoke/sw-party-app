#!/bin/bash
# Builds both versions of the party app from src/app.html:
#   index.html            the hosted site (GitHub Pages + Firebase), with tools/ext-head.html
#   dist-claude/index.html the version published as a Claude artifact (Claude's own storage)
# Both use the same asset files that sit beside index.html (adventures/, items/, spells/ ...).
set -e
cd "$(dirname "$0")/.."
H='<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>'
{ printf '%s<title>אפליקציית החבורה</title><link rel="icon" href="data:,">\n' "$H"; cat tools/ext-head.html; printf '</head><body>\n'; cat src/app.html; printf '\n</body></html>\n'; } > index.html
mkdir -p dist-claude
{ printf '%s</head><body>\n' "$H"; cat src/app.html; printf '\n</body></html>\n'; } > dist-claude/index.html
echo "built index.html and dist-claude/index.html"
