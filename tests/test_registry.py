import json
from pathlib import Path

from audit_tools_bundle import BUNDLE_VERSION
from audit_tools_bundle.registry import COMPONENTS


def test_bundle_version():
    assert BUNDLE_VERSION == "0.3.0"


def test_component_ids_match_lock_file():
    lock = json.loads((Path(__file__).parents[1] / "component-lock.json").read_text(encoding="utf-8"))
    assert {item.component_id for item in COMPONENTS} == set(lock)


def test_component_order_and_product_version():
    assert [item.component_id for item in COMPONENTS] == [
        "file_renamer", "medical_record", "fund_calculator",
    ]
    lock = json.loads((Path(__file__).parents[1] / "component-lock.json").read_text(encoding="utf-8"))
    assert lock["file_renamer"]["version"] == "1.0.0"


def test_factories_can_be_loaded():
    for component in COMPONENTS:
        assert callable(component.load_factory())
