"""The contract every Parasphere product depends on."""
import math

import pytest
from pydantic import ValidationError

from parasphere_twin import (
    SCHEMA_VERSION,
    PierGeometry,
    SubstructureTwin,
    TwinVersionError,
    all_faces,
    demo_twin,
    dump_twin,
    dumps_twin,
    faces_for,
    load_twin,
    loads_twin,
)


def test_demo_twin_is_the_shared_fixture():
    twin = demo_twin()
    assert twin.structure_id == "demo-two-pier"
    assert [p.pier_id for p in twin.piers] == ["pier1", "pier2"]
    assert twin.schema_version == SCHEMA_VERSION


def test_twins_are_frozen():
    twin = demo_twin()
    with pytest.raises(ValidationError):
        twin.name = "edited"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        twin.piers[0].x_ft = 1.0  # type: ignore[misc]


def test_four_faces_span_waterline_to_streambed():
    twin = demo_twin()
    faces = faces_for(twin.piers[0], twin)
    assert {f.face_id for f in faces} == {
        "pier1-x+", "pier1-x-", "pier1-z+", "pier1-z-"
    }
    for face in faces:
        assert face.origin[1] == twin.waterline_y_ft
        assert face.height_ft == twin.waterline_y_ft - twin.streambed_y_ft
        assert face.v_axis == (0.0, -1.0, 0.0)


def test_face_normals_are_unit_and_point_outward():
    twin = demo_twin()
    pier = twin.piers[0]
    for face in faces_for(pier, twin):
        norm = math.sqrt(sum(component**2 for component in face.normal))
        assert math.isclose(norm, 1.0)
        # A step along the normal from the face's center moves away from
        # the pier's center line.
        center = (
            face.origin[0] + face.u_axis[0] * face.width_ft / 2,
            face.origin[2] + face.u_axis[2] * face.width_ft / 2,
        )
        stepped = (center[0] + face.normal[0], center[1] + face.normal[2])
        before = abs(center[0] - pier.x_ft) + abs(center[1] - pier.z_ft)
        after = abs(stepped[0] - pier.x_ft) + abs(stepped[1] - pier.z_ft)
        assert after > before


def test_faces_are_clipped_by_waterline_and_streambed():
    twin = SubstructureTwin(
        structure_id="clip", name="Clipping case",
        waterline_y_ft=-5.0, streambed_y_ft=-40.0,
        piers=(
            PierGeometry(
                pier_id="p", x_ft=0.0, z_ft=0.0, length_ft=4.0, width_ft=8.0,
                top_y_ft=0.0,      # above the waterline: clipped down
                bottom_y_ft=-30.0,  # above the streambed: clipped up
            ),
        ),
    )
    face = faces_for(twin.piers[0], twin)[0]
    assert face.origin[1] == -5.0            # waterline wins over pier top
    assert face.height_ft == 25.0            # -5 down to the pier bottom


def test_all_faces_covers_every_pier_in_order():
    twin = demo_twin()
    faces = all_faces(twin)
    assert len(faces) == 4 * len(twin.piers)
    assert [f.pier_id for f in faces[:4]] == ["pier1"] * 4


def test_json_round_trip_is_lossless(tmp_path):
    twin = demo_twin()
    path = dump_twin(twin, tmp_path / "twin.json")
    assert load_twin(path) == twin
    assert loads_twin(dumps_twin(twin)) == twin


def test_incompatible_major_is_refused():
    payload = dumps_twin(demo_twin()).replace(
        f'"schema_version":"{SCHEMA_VERSION}"', '"schema_version":"2.0"'
    ).replace(  # tolerate pydantic's spacing either way
        f'"schema_version": "{SCHEMA_VERSION}"', '"schema_version": "2.0"'
    )
    with pytest.raises(TwinVersionError, match="not safely readable"):
        loads_twin(payload)


def test_compatible_minor_is_accepted():
    payload = dumps_twin(demo_twin()).replace(
        f'"{SCHEMA_VERSION}"', f'"{SCHEMA_VERSION.split(".")[0]}.99"'
    )
    assert loads_twin(payload).structure_id == "demo-two-pier"


def test_legacy_twin_without_version_still_loads():
    """Files written before versioning are assumed current-major."""
    import json

    payload = json.loads(dumps_twin(demo_twin()))
    payload.pop("schema_version")
    assert loads_twin(json.dumps(payload)).structure_id == "demo-two-pier"
