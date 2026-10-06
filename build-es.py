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
        '<link rel="canonical" href="https://www.pegasusglobaltrade.co/" />',
        '<link rel="canonical" href="https://www.pegasusglobaltrade.co/es" />',
    ),
    ('<meta property="og:locale" content="en_US" />', '<meta property="og:locale" content="es_CO" />'),
    (
        '<meta property="og:url" content="https://www.pegasusglobaltrade.co/" />',
        '<meta property="og:url" content="https://www.pegasusglobaltrade.co/es" />',
    ),
    (
        '<meta property="og:title" content="Colombian Specialty Coffee, Exported Direct" />',
        '<meta property="og:title" content="Café Especial Colombiano, Exportado Directo" />',
    ),
    (
        '<meta property="og:description" content="Single-origin micro-lots from Colombia\'s finest '
        'regions — sourced at the farm and exported with care to specialty buyers across the United States." />',
        '<meta property="og:description" content="Micro-lotes de origen único de las mejores regiones '
        'de Colombia — obtenidos en finca y exportados con cuidado a compradores especializados en Estados Unidos." />',
    ),
    (
        '<meta property="og:image:alt" content="Colombian coffee farmer holding freshly picked coffee cherries" />',
        '<meta property="og:image:alt" content="Caficultor colombiano sosteniendo cerezas de café recién recolectadas" />',
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
