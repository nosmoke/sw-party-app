#!/bin/bash
# builds both versions from equipment-shop.html: publish/ (inside Claude) and site/ (hosted outside Claude)
set -e
cd /home/claude
H='<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>'
mkdir -p publish site
{ printf '%s</head><body>\n' "$H"; cat equipment-shop.html; printf '\n</body></html>\n'; } > publish/index.html
for f in shop/*; do [ "$(basename "$f")" = adventures ] && continue; cp -r "$f" site/; done   # books live in the Firebase library (sources: nosmoke/sw-party-books)
{ printf '%s<title>אפליקציית החבורה</title><link rel="icon" href="data:,">\n' "$H"; cat ext/head.html; printf '</head><body>\n'; cat equipment-shop.html; printf '\n</body></html>\n'; } > site/index.html
cp ext/ext.js site/ext.js
[ -f site/config.js ] || cp ext/config.js site/config.js
touch site/.nojekyll
# keep the repository's source and build pieces in step with the working copy
cp equipment-shop.html sw-party-app/src/app.html
cp ext/head.html sw-party-app/tools/ext-head.html
