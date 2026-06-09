"""
Descarga los límites municipales de la provincia de Alicante desde OpenStreetMap
(Overpass API) y los guarda en static/alicante_municipios.geojson.

Uso: python scripts/descargar_geojson.py
"""
import json
import os
import sys
import urllib.parse
import urllib.request

SERVIDORES = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# out geom incluye coordenadas directamente en cada member way
QUERY = """
[out:json][timeout:180];
area["ISO3166-2"="ES-A"]->.prov;
relation["admin_level"="8"]["boundary"="administrative"](area.prov);
out geom;
"""


def coords_iguales(a, b, tol=1e-7):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def encadenar_ways(ways):
    if not ways:
        return []
    result = list(ways[0])
    remaining = [list(w) for w in ways[1:]]
    while remaining:
        ultimo = result[-1]
        encontrado = False
        for i, way in enumerate(remaining):
            if coords_iguales(way[0], ultimo):
                result.extend(way[1:])
                remaining.pop(i)
                encontrado = True
                break
            if coords_iguales(way[-1], ultimo):
                result.extend(list(reversed(way))[1:])
                remaining.pop(i)
                encontrado = True
                break
        if not encontrado:
            for w in remaining:
                result.extend(w)
            break
    return result


def relation_a_poligono(members):
    outer_ways = []
    for m in members:
        if m.get("role") == "outer" and m.get("type") == "way" and "geometry" in m:
            coords = [[n["lon"], n["lat"]] for n in m["geometry"]]
            outer_ways.append(coords)
    if not outer_ways:
        return None
    ring = encadenar_ways(outer_ways)
    if ring and not coords_iguales(ring[0], ring[-1]):
        ring.append(ring[0])
    return ring if len(ring) >= 4 else None


def consultar(servidor):
    params = urllib.parse.urlencode({"data": QUERY})
    url = f"{servidor}?{params}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "TFG-AlicanteDig/1.0")
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def descargar():
    output = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "static", "alicante_municipios.geojson")
    )

    raw = None
    for servidor in SERVIDORES:
        print(f"Probando {servidor} ...")
        try:
            raw = consultar(servidor)
            print("Conexión OK.")
            break
        except Exception as e:
            print(f"  Fallo: {e}")

    if raw is None:
        print("No se pudo contactar ningún servidor Overpass.", file=sys.stderr)
        sys.exit(1)

    elements = raw.get("elements", [])
    print(f"Recibidos {len(elements)} elementos de OSM.")

    features = []
    sin_geom = []

    for elem in elements:
        if elem.get("type") != "relation":
            continue

        tags = elem.get("tags", {})
        nombre = tags.get("name", "")
        nombre_es = tags.get("name:es", "")
        ref_ine = tags.get("ref:ine", "")

        ring = relation_a_poligono(elem.get("members", []))
        if not ring:
            sin_geom.append(nombre_es or nombre or ref_ine)
            continue

        features.append({
            "type": "Feature",
            "properties": {
                "nombre": nombre,
                "nombre_es": nombre_es,
                "ref_ine": ref_ine
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [ring]
            }
        })
        print(f"  ✓ {nombre_es or nombre}")

    geojson = {"type": "FeatureCollection", "features": features}

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    print(f"\n✅ Guardado en: {output}")
    print(f"   Municipios con geometría: {len(features)}")
    if sin_geom:
        print(f"   Sin geometría ({len(sin_geom)}): {', '.join(sin_geom)}")


if __name__ == "__main__":
    descargar()
