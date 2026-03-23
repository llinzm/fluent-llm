
# capability_registry

A small Python package for loading and validating a FluentControl-aligned capability registry.

## What is in the package

- `data/registry.yaml` — the current merged capability registry
- `models.py` — typed dataclasses for registry entities
- `loader.py` — YAML loading and schema checks
- `registry.py` — in-memory access helpers
- `validator.py` — compatibility validation engine

## Install dependency

This package uses PyYAML. Use `yaml.safe_load` when loading YAML from files. PyYAML documents `safe_load` as the safer choice for untrusted input. citeturn587932view0

```bash
pip install pyyaml
```

## Quick start

```python
from capability_registry import load_default_registry

registry = load_default_registry()

print(registry.get_device("FCA"))
print(registry.get_tip("FCA_DiTi_200uL"))

result = registry.validate_compatibility(
    device_name="FCA",
    tip_name="FCA_DiTi_200uL",
    liquid_class_name="Water_Contact_Wet",
    volume_uL=50,
    labware_name="Plate_96",
    operation_name="mix",
)

print(result.ok)
print(result.errors)
print(result.warnings)
```

## What the validator checks

- unknown devices, tips, liquid classes, and labware
- tip-to-device compatibility
- max and min tip volume limits
- liquid-class-to-tip compatibility
- low-level device capability checks
- labware-to-operation compatibility warnings

## Notes

- The registry is intentionally conservative.
- Some FluentControl details remain installation-specific, especially liquid classes, exact tip catalogs, and exported method inventory.
- The `methods` section is a planning bridge, not a substitute for exported FluentControl methods.

## Package layout

```text
capability_registry/
  __init__.py
  models.py
  registry.py
  loader.py
  validator.py
  data/
    registry.yaml
  README.md
```
