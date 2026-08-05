"""The structure twin: one description that drives every Parasphere product.

The same twin JSON spawns the simulator world, compiles the survey mission,
supplies the coverage denominator, and serves as the cleaning prior that
tells processing where the structure actually is.

Frame convention (feet, right-handed, and identical in every consumer):

- ``x`` runs along the structure from the reference end (Abutment A /
  south / start = 0)
- ``y`` is vertical, 0 at the deck reference, negative below it
- ``z`` runs across the width from the centerline

Everything here is frozen: a twin is a fact about a structure, not a
mutable scratchpad. Consumers derive; they never edit in place.
"""
from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"
"""Semantic version of the twin schema itself.

Bump the minor for additive, backward-compatible fields; bump the major
for anything that changes the meaning of an existing field or removes
one. `load_twin` refuses majors it does not implement.
"""


class PierGeometry(BaseModel):
    """One rectangular pier/column wall: a top-down box plus vertical extent."""

    model_config = ConfigDict(frozen=True)

    pier_id: str
    x_ft: float
    """Center along the structure."""
    z_ft: float
    """Center across the structure from the centerline."""
    length_ft: float
    """Extent along x."""
    width_ft: float
    """Extent along z."""
    top_y_ft: float
    """Top of the inspectable span (cap / beam seat)."""
    bottom_y_ft: float
    """Bottom (streambed or footing top)."""


class SubstructureTwin(BaseModel):
    """A bridge's below-deck geometry, as known before anyone gets wet."""

    model_config = ConfigDict(frozen=True)

    structure_id: str
    name: str
    waterline_y_ft: float
    streambed_y_ft: float
    piers: tuple[PierGeometry, ...]
    schema_version: str = Field(default=SCHEMA_VERSION)


class PlanarFace(BaseModel):
    """One vertical pier face: the unit of survey planning and coverage.

    Points on the face are ``origin + u_axis*s + v_axis*t`` for
    ``s`` in [0, width_ft] and ``t`` in [0, height_ft]. ``v_axis`` always
    points down; ``normal`` points away from the pier into open water.
    """

    model_config = ConfigDict(frozen=True)

    face_id: str
    pier_id: str
    origin: tuple[float, float, float]
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    normal: tuple[float, float, float]
    width_ft: float
    height_ft: float


def faces_for(pier: PierGeometry, twin: SubstructureTwin) -> tuple[PlanarFace, ...]:
    """The four underwater faces of a pier, waterline down to the bottom."""
    top = min(twin.waterline_y_ft, pier.top_y_ft)
    bottom = max(twin.streambed_y_ft, pier.bottom_y_ft)
    height = top - bottom
    half_l, half_w = pier.length_ft / 2.0, pier.width_ft / 2.0
    down = (0.0, -1.0, 0.0)

    def face(suffix, origin, u_axis, normal, width):
        return PlanarFace(
            face_id=f"{pier.pier_id}-{suffix}",
            pier_id=pier.pier_id,
            origin=origin,
            u_axis=u_axis,
            v_axis=down,
            normal=normal,
            width_ft=width,
            height_ft=height,
        )

    x0, x1 = pier.x_ft - half_l, pier.x_ft + half_l
    z0, z1 = pier.z_ft - half_w, pier.z_ft + half_w
    return (
        face("x+", (x1, top, z0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), pier.width_ft),
        face("x-", (x0, top, z1), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0), pier.width_ft),
        face("z+", (x0, top, z1), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), pier.length_ft),
        face("z-", (x1, top, z0), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), pier.length_ft),
    )


def all_faces(twin: SubstructureTwin) -> tuple[PlanarFace, ...]:
    """Every underwater face on the structure, pier order preserved."""
    faces: list[PlanarFace] = []
    for pier in twin.piers:
        faces.extend(faces_for(pier, twin))
    return tuple(faces)
