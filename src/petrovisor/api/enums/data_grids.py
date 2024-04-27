from enum import (
    IntEnum,
    auto,
)


# DataGrid types
class DataGridType(IntEnum):
    """
    DataGrid types
    """

    # Unknown (custom)
    Unknown = 0
    # One Polygon (no data)
    Polygon = auto()
    # Several polygons (no data)
    Polygons = auto()
    # Geo data grid (ZMap like)
    GeoDataGrid = auto()
    # Voronoi grid
    VoronoiGrid = auto()
    # Points with values (from shape files)
    Points = auto()
    # Corner Point Grid
    CornerPointGrid = auto()


# PointSet types
class PointSetType(IntEnum):
    """
    PointSet types
    """

    # Unknown (custom)
    Unknown = 0
    # Single point
    Point = auto()
    # Multipoint(set of points)
    MultiPoint = auto()
    # Two connected points
    Line = auto()
    # Polyline / LineString / LineStrip(connected sequence of points)
    PolyLine = auto()
    # Polygon / LinearRing(connected sequence of points that form a closed ring)
    Polygon = auto()
    # Polygon with four vertices
    Quad = auto()
    # Polygon with three vertices
    Triangle = auto()
    # Triangle strip(every group of 3 adjacent vertices forms a triangle)
    TriangleStrip = auto()
    # Triangle fan(every group of 2 adjacent vertices forms a triangle with the very first vertex)
    TriangleFan = auto()
    # Polyhedron (three-dimensional shape with flat polygonal faces)
    Polyhedron = auto()
    # Hexahedron (polyhedron composed of six faces)
    Hexahedron = auto()
    # Tetrahedron (polyhedron composed of four triangular faces)
    Tetrahedron = auto()
    # Pyramid (polyhedron composed of quadrilateral base connected to point (apex), forming four triangular faces)
    Pyramid = auto()
    # Wedge / Triangular prism (polyhedron composed of two triangular and three trapezoid faces)
    Wedge = auto()
