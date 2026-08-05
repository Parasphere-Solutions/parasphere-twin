# parasphere-twin

The shared structure-twin schema. One twin file drives every Parasphere
product:

| Consumer | What the twin does there |
|---|---|
| HoloOcean fork | spawns the simulated world — piers, streambed, waterline |
| `parasphere-sub` | compiles the survey mission and scores coverage per face |
| `plumbline` | the cleaning prior: protects structure returns, flags multipath |
| Drafthorse | anchors findings in structure coordinates |

That is the architecture: the simulator rehearses against it, the vehicle
inspects against it, and the processing engine interprets against it —
because they are all reading the same file.

## Frame convention

Feet, right-handed:

- `x` along the structure from the reference end (Abutment A / south / start = 0)
- `y` vertical, 0 at the deck reference, negative below it
- `z` across the width from the centerline

## Use

```python
from parasphere_twin import demo_twin, all_faces, load_twin, dump_twin

twin = load_twin("nottoway.json")      # or demo_twin() for the shared fixture
for face in all_faces(twin):           # four underwater faces per pier
    print(face.face_id, face.width_ft, face.height_ft, face.normal)
```

Models are frozen: a twin is a fact about a structure, not a scratchpad.
Consumers derive; they never edit in place.

## Versioning

`SCHEMA_VERSION` is semantic. Additive fields bump the minor and stay
readable everywhere; anything that changes or removes a field's meaning
bumps the major, and `load_twin` refuses majors it does not implement —
so a breaking change turns every consumer's CI red instead of silently
mis-shaping geometry. Pin a minor in each consumer.

## Scope

Deliberately minimal: models, face derivation, JSON I/O with the version
check, and the shared demo fixture. No geometry solving, no rendering, no
storage. Cleverness belongs in the consumer that needs it.

## Development

```sh
uv sync --extra dev
uv run pytest
```

## License

Apache-2.0. Maintained by [Parasphere Solutions](https://paraspheresolutions.com) —
automated infrastructure inspection software. The schema is published openly
so partners, agencies, and hardware vendors can read and write the same
structure description we do.
