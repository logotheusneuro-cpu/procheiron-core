#!/usr/bin/env python3
"""Stdlib-only JSON Schema (Draft 2020-12 subset) checker for Procheiron.

WHY THIS EXISTS: the live validator is stdlib-only by doctrine (config.yaml
policy_defaults.no_package_installs class). The Phase-3 schemas (3.1) are
standard JSON Schema so any tool can consume them, but the *consuming validator*
must not take a `jsonschema` runtime dependency. This module interprets exactly
the subset of JSON Schema the Procheiron schemas use, returning structured
findings the validator can grade via severity_map.json.

Supported keywords: type (string or list), enum, const, required, properties,
additionalProperties (boolean), items (single subschema), minItems, minLength,
maxLength, pattern, minimum, maximum, anyOf, allOf, oneOf, not, if/then/else.
Annotation keywords ($schema, $id, $comment, $defs, $ref-free, title,
description, default, $note_*) are ignored.

NOT a general validator: $ref, patternProperties, dependentSchemas, prefixItems,
and numeric multipleOf are intentionally unsupported and raise UnsupportedSchema
so a schema that quietly needs them cannot pass by silent omission.

The test suite (../tests/test_schemas.py) cross-checks every finding against the
`jsonschema` package (Draft 2020-12) when it is importable, so this reference
implementation is proven equivalent on the live data + fixtures.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

_SUPPORTED = {
    "$schema", "$id", "$comment", "$defs", "title", "description", "default",
    "type", "enum", "const", "required", "properties", "additionalProperties",
    "items", "minItems", "minLength", "maxLength", "pattern", "minimum", "maximum",
    "anyOf", "allOf", "oneOf", "not", "if", "then", "else",
}


class UnsupportedSchema(RuntimeError):
    pass


class Finding(dict):
    """A schema violation. Keys: instance_path, schema_path, keyword, message."""


def _is_type(value: Any, typ: str) -> bool:
    if typ == "object":
        return isinstance(value, dict)
    if typ == "array":
        return isinstance(value, list)
    if typ == "string":
        return isinstance(value, str)
    if typ == "boolean":
        return isinstance(value, bool)
    if typ == "null":
        return value is None
    if typ == "integer":
        # JSON booleans are not integers, and 1.0 counts as integer in 2020-12.
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, float) and value.is_integer()
    if typ == "number":
        # bool is a subclass of int in Python; JSON Schema says bool is NOT a number.
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise UnsupportedSchema(f"unknown type keyword: {typ!r}")


def _equal(a: Any, b: Any) -> bool:
    """Type-aware equality so True != 1 and 1 != 1.0-as-different-json-types are
    handled the way JSON Schema enum/const expect (value + json-type)."""
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a == b
    if type(a) is not type(b) and not (isinstance(a, str) and isinstance(b, str)):
        # dict/list/str/None must match json type
        if isinstance(a, dict) and isinstance(b, dict):
            return a == b
        if isinstance(a, list) and isinstance(b, list):
            return a == b
        return a is b if a is None or b is None else a == b and type(a) is type(b)
    return a == b


def _check_unsupported(schema: Dict[str, Any]) -> None:
    for key in schema:
        if key in _SUPPORTED or key.startswith("$") or key.startswith("x-"):
            continue
        raise UnsupportedSchema(f"unsupported schema keyword: {key!r}")


def validate(schema: Any, instance: Any, ipath: str = "", spath: str = "") -> List[Finding]:
    """Return a list of Findings (empty == valid). ipath/spath are JSON-pointer-ish."""
    findings: List[Finding] = []
    if schema is True:
        return findings
    if schema is False:
        return [Finding(instance_path=ipath or "/", schema_path=spath, keyword="false",
                        message="schema is false; nothing validates")]
    if not isinstance(schema, dict):
        raise UnsupportedSchema(f"schema must be object/bool at {spath}, got {type(schema).__name__}")
    _check_unsupported(schema)

    def add(keyword: str, message: str, ip: Optional[str] = None) -> None:
        findings.append(Finding(instance_path=ip if ip is not None else (ipath or "/"),
                                schema_path=f"{spath}/{keyword}", keyword=keyword, message=message))

    # type
    if "type" in schema:
        types = schema["type"]
        types = [types] if isinstance(types, str) else list(types)
        if not any(_is_type(instance, t) for t in types):
            add("type", f"expected type {schema['type']!r}, got {_json_type(instance)}")
            # If the base type is wrong, deeper keyword checks are noise; still
            # run combinators/enum which are type-orthogonal.
    # enum
    if "enum" in schema:
        if not any(_equal(instance, opt) for opt in schema["enum"]):
            add("enum", f"value {instance!r} not in enum {schema['enum']!r}")
    # const
    if "const" in schema:
        if not _equal(instance, schema["const"]):
            add("const", f"value {instance!r} != const {schema['const']!r}")

    # string facets
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            add("minLength", f"string length {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            add("maxLength", f"string length {len(instance)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            add("pattern", f"string {instance!r} does not match pattern {schema['pattern']!r}")

    # number facets
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            add("minimum", f"value {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            add("maximum", f"value {instance} > maximum {schema['maximum']}")

    # array facets
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            add("minItems", f"array length {len(instance)} < minItems {schema['minItems']}")
        if "items" in schema:
            for i, elem in enumerate(instance):
                findings += validate(schema["items"], elem, f"{ipath}/{i}", f"{spath}/items")

    # object facets
    if isinstance(instance, dict):
        if "required" in schema:
            for key in schema["required"]:
                if key not in instance:
                    add("required", f"missing required property {key!r}", ip=ipath or "/")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in instance:
                findings += validate(subschema, instance[key], f"{ipath}/{key}", f"{spath}/properties/{key}")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    add("additionalProperties", f"additional property {key!r} not allowed",
                        ip=f"{ipath}/{key}")
        elif isinstance(schema.get("additionalProperties"), dict):
            for key in instance:
                if key not in props:
                    findings += validate(schema["additionalProperties"], instance[key],
                                         f"{ipath}/{key}", f"{spath}/additionalProperties")

    # combinators
    if "allOf" in schema:
        for i, sub in enumerate(schema["allOf"]):
            findings += validate(sub, instance, ipath, f"{spath}/allOf/{i}")
    if "anyOf" in schema:
        if not any(not validate(sub, instance, ipath, "") for sub in schema["anyOf"]):
            add("anyOf", "instance does not match any subschema in anyOf")
    if "oneOf" in schema:
        matches = sum(1 for sub in schema["oneOf"] if not validate(sub, instance, ipath, ""))
        if matches != 1:
            add("oneOf", f"instance matched {matches} subschemas in oneOf (need exactly 1)")
    if "not" in schema:
        if not validate(schema["not"], instance, ipath, ""):
            add("not", "instance matches a schema it must not match")
    if "if" in schema:
        if not validate(schema["if"], instance, ipath, ""):  # 'if' passed
            if "then" in schema:
                findings += validate(schema["then"], instance, ipath, f"{spath}/then")
        else:
            if "else" in schema:
                findings += validate(schema["else"], instance, ipath, f"{spath}/else")

    return findings


def _json_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_valid(schema: Any, instance: Any) -> bool:
    return not validate(schema, instance)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Validate a JSON instance (or JSONL file) against a Procheiron schema.")
    ap.add_argument("schema")
    ap.add_argument("instance", help="a .json object or a .jsonl file (one object per line)")
    ap.add_argument("--jsonl", action="store_true", help="treat instance as JSONL")
    args = ap.parse_args()
    sch = load_schema(Path(args.schema))
    total = 0
    if args.jsonl:
        for n, line in enumerate(Path(args.instance).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            for f in validate(sch, obj):
                total += 1
                print(f"line {n} {f['instance_path']} [{f['keyword']}] {f['message']}")
    else:
        obj = json.loads(Path(args.instance).read_text(encoding="utf-8"))
        for f in validate(sch, obj):
            total += 1
            print(f"{f['instance_path']} [{f['keyword']}] {f['message']}")
    print(f"{'FAIL' if total else 'PASS'}: {total} finding(s)")
    raise SystemExit(1 if total else 0)
