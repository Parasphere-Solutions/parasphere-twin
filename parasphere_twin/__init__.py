"""The shared structure-twin schema for Parasphere products.

One twin file drives the simulator world, the survey mission, the coverage
denominator, and the processing prior. This package is the single place
that schema is defined.
"""
from parasphere_twin.fixtures import demo_twin
from parasphere_twin.io import (
    TwinVersionError,
    dump_twin,
    dumps_twin,
    load_twin,
    loads_twin,
)
from parasphere_twin.schema import (
    SCHEMA_VERSION,
    PierGeometry,
    PlanarFace,
    SubstructureTwin,
    all_faces,
    faces_for,
)

__all__ = [
    "SCHEMA_VERSION",
    "PierGeometry",
    "PlanarFace",
    "SubstructureTwin",
    "TwinVersionError",
    "all_faces",
    "demo_twin",
    "dump_twin",
    "dumps_twin",
    "faces_for",
    "load_twin",
    "loads_twin",
]

__version__ = "0.1.0"
