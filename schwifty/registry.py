import json
import pathlib
from collections import defaultdict
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union


try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files  # type: ignore


_registry: Dict[str, Union[Dict, List[Dict]]] = {}


def has(name: str) -> bool:
    return name in _registry


def get(name: str) -> Union[Dict, List[Dict]]:
    if not has(name):
        data = None
        directory = files(__package__) / f"{name}_registry"
        assert isinstance(directory, pathlib.Path)
        for entry in sorted(directory.glob("*.json")):
            with entry.open() as fp:
                chunk = json.load(fp)
                if data is None:
                    data = chunk
                elif isinstance(data, list):
                    data.extend(chunk)
                elif isinstance(data, dict):
                    data.update(chunk)
        if data is None:
            raise ValueError(f"Failed to load registry {name}")
        save(name, data)
    return _registry[name]


def save(name: str, data: Union[Dict, List[Dict]]) -> None:
    _registry[name] = data


def build_index(
    base_name: str,
    index_name: str,
    key: Union[str, Tuple],
    accumulate: bool = False,
    **predicate: Any,
) -> None:
    def make_key(entry: Dict) -> Union[Tuple, str]:
        return tuple(entry[k] for k in key) if isinstance(key, tuple) else entry[key]

    def match(entry: dict) -> bool:
        return all(entry[key] == value for key, value in predicate.items())

    base = get(base_name)
    assert isinstance(base, list)
    if accumulate:
        data = defaultdict(list)
        for entry in base:
            if not match(entry):
                continue
            data[make_key(entry)].append(entry)
        save(index_name, dict(data))
    else:
        save(index_name, {make_key(entry): entry for entry in base if match(entry)})


def manipulate(name: str, func: Callable) -> None:
    registry = get(name)
    if isinstance(registry, dict):
        for key, value in registry.items():
            registry[key] = func(key, value)
    elif isinstance(registry, list):
        registry = [func(item) for item in registry]
    save(name, registry)
