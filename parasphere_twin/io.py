"""Reading and writing twins, with the version check that keeps them honest."""
import json
from pathlib import Path

from parasphere_twin.schema import SCHEMA_VERSION, SubstructureTwin


class TwinVersionError(ValueError):
    """A twin file was written against an incompatible schema major."""


def _major(version: str) -> int:
    try:
        return int(str(version).split(".", 1)[0])
    except (ValueError, AttributeError) as error:
        raise TwinVersionError(f"unreadable schema_version: {version!r}") from error


def loads_twin(text: str) -> SubstructureTwin:
    """Parse twin JSON, refusing schema majors this package cannot honor."""
    payload = json.loads(text)
    declared = payload.get("schema_version", SCHEMA_VERSION)
    if _major(declared) != _major(SCHEMA_VERSION):
        raise TwinVersionError(
            f"twin declares schema {declared}; this package implements "
            f"{SCHEMA_VERSION} — a major difference changes field meanings, "
            "so the file is not safely readable here"
        )
    return SubstructureTwin.model_validate(payload)


def load_twin(path: str | Path) -> SubstructureTwin:
    """Load a twin from a JSON file."""
    return loads_twin(Path(path).read_text())


def dumps_twin(twin: SubstructureTwin, *, indent: int = 2) -> str:
    """Serialize a twin to JSON text."""
    return twin.model_dump_json(indent=indent)


def dump_twin(twin: SubstructureTwin, path: str | Path) -> Path:
    """Write a twin to a JSON file and return the path."""
    target = Path(path)
    target.write_text(dumps_twin(twin) + "\n")
    return target
