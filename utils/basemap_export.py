"""
Export simplified coastlines and state borders as JSON rows for the dashboard route map.
Run from the project root: python -m utils.basemap_export
"""

import json

from cartopy.io import shapereader
from shapely.geometry import box

# North America frame the route map covers
FRAME = box(-128, 17, -64, 52)
SIMPLIFY_DEGREES = 0.04


def lines_of(geometry):
    """Yield the coordinate lists of a (multi)line or the rings of a (multi)polygon, inside the frame."""
    clipped = geometry.intersection(FRAME).simplify(SIMPLIFY_DEGREES)
    if clipped.is_empty:
        return
    for part in getattr(clipped, 'geoms', [clipped]):
        if part.geom_type == 'Polygon':
            yield list(part.exterior.coords)
        elif part.geom_type == 'LineString':
            yield list(part.coords)
        elif part.geom_type == 'MultiLineString':
            for line in part.geoms:
                yield list(line.coords)


def points_text(coords):
    return ' '.join(f'{lon:.2f},{lat:.2f}' for lon, lat in coords)


def export(path='docs/data/basemap.json'):
    sources = [
        ('land', shapereader.natural_earth('50m', 'physical', 'land')),
        ('border', shapereader.natural_earth('50m', 'cultural', 'admin_1_states_provinces_lines')),
    ]
    rows = []
    for kind, shapefile in sources:
        for record in shapereader.Reader(shapefile).geometries():
            for coords in lines_of(record):
                if len(coords) >= 2:
                    rows.append({'id': f'{kind}{len(rows)}', 'kind': kind, 'pts': points_text(coords)})

    with open(path, 'w') as f:
        json.dump(rows, f)

    return rows


if __name__ == '__main__':
    print(len(export()), 'paths')
