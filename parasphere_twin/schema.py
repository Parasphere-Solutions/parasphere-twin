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

Unknown keys are rejected, never ignored: a misspelled field in a
hand-authored twin would otherwise validate cleanly and read downstream
as "not stated" — and for a field like ``foundation_y_ft``, whose
absence means "no foundation on record", that silence is itself a
safety statement no typo may be allowed to make.
"""
import math

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.1"
"""Semantic version of the twin schema itself.

Bump the minor for additive, backward-compatible fields; bump the major
for anything that changes the meaning of an existing field or removes
one. `load_twin` refuses majors it does not implement.
"""


class PierGeometry(BaseModel):
    """One rectangular pier/column wall: a top-down box plus vertical extent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

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
    """Bottom of the MODELED vertical extent.

    Where the modeled pier stops for geometry and occlusion — usually
    the streambed, because that is as far as any survey can see. It is
    explicitly NOT a foundation claim: a twin modeled down to the
    mudline says nothing about what is buried beneath it. The bottom of
    the foundation itself, when known, is `foundation_y_ft`.
    """
    foundation_y_ft: float | None = None
    """Elevation of the BOTTOM of the foundation, when known.

    The level below which there is no more structure to undermine — the
    reference that remaining scour cover is measured against. `None`
    means unknown, which is the common case (most DOTs do not release
    as-built foundation plans); unknown must stay `None` rather than
    degrade to a guess.

    Frame trap: this is a twin-frame `y` elevation, the same frame as
    `top_y_ft` and `bottom_y_ft` — NOT a raw plan-sheet elevation. Plan
    sheets state foundation levels in the project's vertical datum;
    whoever populates this field owns the conversion into the twin's
    frame, because a silent datum mismatch here produces a confidently
    wrong cover number.

    A foundation above the current streambed, or above `bottom_y_ft`,
    is valid input: it is the undermined case this field exists to
    expose, not a data error. The only bound enforced is that the
    foundation sits below the pier's own top.
    """

    @model_validator(mode="after")
    def _foundation_sits_below_the_top(self) -> "PierGeometry":
        if self.foundation_y_ft is None:
            return self
        # isfinite is load-bearing: a bare comparison rejects NaN and
        # +inf but ACCEPTS -inf, which would then serialize to null and
        # round-trip as "no foundation on record".
        if not (math.isfinite(self.foundation_y_ft)
                and self.foundation_y_ft < self.top_y_ft):
            raise ValueError(
                "foundation_y_ft must sit below top_y_ft (an unknown or "
                "non-finite level is stated as None, never as a number). No "
                "other bound applies: a foundation above bottom_y_ft or the "
                "streambed is the undermining this field exists to expose."
            )
        return self


class SubstructureTwin(BaseModel):
    """A bridge's below-deck geometry, as known before anyone gets wet."""

    model_config = ConfigDict(frozen=True, extra="forbid")

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

    model_config = ConfigDict(frozen=True, extra="forbid")

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
