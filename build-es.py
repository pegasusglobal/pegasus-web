#!/usr/bin/env python3
"""Render the text of both language pages from their data-en / data-es attributes.

index.html is the single source of markup. Every translatable string lives in a
data-en / data-es attribute pair. This script writes the English strings into
index.html and the Spanish ones into es/index.html, so the text is in the HTML
itself and paints without waiting for JavaScript. Run it after any edit to
index.html:

    python3 build-es.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
TRANSLATABLE = re.compile(
    r'(<(\w+)\b[^>]*?\sdata-en="([^"]*)"[^>]*?\sdata-es="([^"]*)"[^>]*>)(.*?)(</\2>)', re.S
)


def render_text(html, lang):
    group = 3 if lang == "en" else 4
    return TRANSLATABLE.sub(lambda m: m.group(1) + m.group(group) + m.group(6), html)


index_path = ROOT / "index.html"
src = render_text(index_path.read_text(encoding="utf-8"), "en")
if src.count("data-en=") != len(TRANSLATABLE.findall(src)):
    sys.exit("build-es.py: some data-en elements were not matched; check attribute order (data-en before data-es)")
index_path.write_text(src, encoding="utf-8")

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
out = render_text(out, "es")

(ROOT / "es").mkdir(exist_ok=True)
(ROOT / "es" / "index.html").write_text(out, encoding="utf-8")
print(f"es/index.html regenerated ({len(out.splitlines())} lines)")
