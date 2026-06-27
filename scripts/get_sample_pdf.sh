#!/usr/bin/env bash
# Fetch a real, PUBLIC crime-law PDF to test with: the Swedish Criminal Code
# (brottsbalken), English translation, from the Government of Sweden. Public document —
# safe to fetch. Put your own (incl. sensitive) PDFs in data/ too; it's gitignored.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
url="https://www.government.se/contentassets/7a2dcae0787e465e9a2431554b5eab03/the-swedish-criminal-code.pdf"

mkdir -p "$root/data"
echo "Downloading Swedish Criminal Code → data/swedish_criminal_code.pdf"
curl -fSL -A "Mozilla/5.0" -o "$root/data/swedish_criminal_code.pdf" "$url"
echo "Done. Now:  uv run python -m legendary_potato \"unlawful threat\""
