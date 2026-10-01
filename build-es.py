#!/usr/bin/env python3
"""Regenerate es/index.html from index.html.

index.html is the single source of markup. Every translatable string lives in a
data-en / data-es attribute pair, so the Spanish page is the same file with the
language flipped. Run this after any edit to index.html:

    python3 build-es.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
src = (ROOT / "index.html").read_text(encoding="utf-8")

REPLACEMENTS = [
    ('<html lang="en">', '<html lang="es">'),
    (
        "<title>Pegasus Global Trade — Colombian Specialty Coffee Export</title>",
        "<title>Pegasus Global Trade — Exportación de Café Especial de Colombia</title>",
    ),
    (
        "Direct-trade specialty coffee from Colombia's finest micro-regions. "
        "Sourced with integrity, exported with care to the United States.",
        "Café especial de comercio directo desde las mejores micro-regiones de Colombia. "
        "Abastecido con integridad, exportado con cuidado hacia los Estados Unidos.",
    ),
    (
        '<link rel="canonical" href="https://pegasusglobaltrade.co/" />',
        '<link rel="canonical" href="https://pegasusglobaltrade.co/es" />',
    ),
    ("const PAGE_LANG = 'en';", "const PAGE_LANG = 'es';"),
    ('class="lang-btn active" data-lang="en"', 'class="lang-btn" data-lang="en"'),
    ('class="lang-btn" data-lang="es"', 'class="lang-btn active" data-lang="es"'),
]

out = src
for old, new in REPLACEMENTS:
    if old not in out:
        sys.exit(f"build-es.py: expected string not found in index.html:\n  {old[:90]}")
    out = out.replace(old, new)

(ROOT / "es").mkdir(exist_ok=True)
(ROOT / "es" / "index.html").write_text(out, encoding="utf-8")
print(f"es/index.html regenerated ({len(out.splitlines())} lines)")
