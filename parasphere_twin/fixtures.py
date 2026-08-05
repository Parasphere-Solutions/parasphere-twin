"""Shared fixture twins.

Every consumer tests against these, so "the same twin" is literally true
across the simulator, the mission compiler, and the processing engine.
"""
from parasphere_twin.schema import PierGeometry, SubstructureTwin


def demo_twin() -> SubstructureTwin:
    """Two-pier crossing — the regression fixture used by every product."""
    return SubstructureTwin(
        structure_id="demo-two-pier",
        name="Demo two-pier crossing",
        waterline_y_ft=-10.0,
        streambed_y_ft=-30.0,
        piers=(
            PierGeometry(
                pier_id="pier1", x_ft=40.0, z_ft=0.0, length_ft=4.0,
                width_ft=12.0, top_y_ft=-6.0, bottom_y_ft=-30.0,
            ),
            PierGeometry(
                pier_id="pier2", x_ft=80.0, z_ft=0.0, length_ft=4.0,
                width_ft=12.0, top_y_ft=-6.0, bottom_y_ft=-30.0,
            ),
        ),
    )
