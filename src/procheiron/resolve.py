#!/usr/bin/env python3
"""Procheiron path resolver — Tier-1 draft.

Resolution order is most-explicit-wins per the corrected 2026-06-11 Tier-1 plan:
1. explicit --root argument
2. PROCHEIRON_ROOT environment variable
3. nearest ancestor containing .procheiron/config.yaml
4. clear error

If an ambient ancestor tree differs from an explicit/env-selected root, the
resolver emits a loud stderr warning instead of silently hiding the mismatch.

Stdlib-only: config.yaml support is deliberately a small subset sufficient for the
current Procheiron config shape (nested mappings, scalar strings/numbers/bools).
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_REL = Path('.procheiron') / 'config.yaml'


class ResolveError(RuntimeError):
    pass


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ''
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    stack: list[tuple[int, Dict[str, Any]]] = [(-1, data)]
    for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        if '\t' in raw[:len(raw) - len(raw.lstrip())]:
            raise ResolveError(f'{path}:{lineno}: tabs are not supported in config indentation')
        indent = len(raw) - len(raw.lstrip(' '))
        line = raw.strip()
        if ':' not in line:
            raise ResolveError(f'{path}:{lineno}: expected key: value')
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ResolveError(f'{path}:{lineno}: invalid indentation')
        parent = stack[-1][1]
        if value == '':
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return data


def find_ancestor_root(start: Optional[Path] = None) -> Optional[Path]:
    here = (start or Path.cwd()).resolve()
    if here.is_file():
        here = here.parent
    for candidate in [here, *here.parents]:
        if (candidate / CONFIG_REL).is_file():
            return candidate
    return None


def _warn_if_ancestor_mismatch(chosen: Path, ancestor: Optional[Path], source: str) -> None:
    if ancestor and ancestor.resolve() != chosen.resolve():
        print(
            'procheiron_resolve: WARNING: '
            f'{source} selected {chosen}, but ambient ancestor discovery found {ancestor}; '
            'using the more explicit root',
            file=sys.stderr,
        )


def resolve_root(explicit_root: Optional[str] = None, start: Optional[Path] = None) -> Path:
    ancestor = find_ancestor_root(start)
    if explicit_root:
        chosen = Path(explicit_root).expanduser().resolve()
        _warn_if_ancestor_mismatch(chosen, ancestor, '--root')
        return chosen
    env_root = os.environ.get('PROCHEIRON_ROOT')
    if env_root:
        chosen = Path(env_root).expanduser().resolve()
        _warn_if_ancestor_mismatch(chosen, ancestor, 'PROCHEIRON_ROOT')
        return chosen
    if ancestor:
        return ancestor
    raise ResolveError('No Procheiron root found: pass --root, set PROCHEIRON_ROOT, run under a tree with .procheiron/config.yaml')


@dataclass(frozen=True)
class ProcheironConfig:
    root: Path
    config_path: Path
    version: str
    profile: str
    paths: Dict[str, Path]
    raw: Dict[str, Any]

    def path(self, key: str) -> Path:
        if key not in self.paths:
            raise ResolveError(f'paths.{key} missing from config {self.config_path}')
        return self.paths[key]


def load_config(explicit_root: Optional[str] = None, start: Optional[Path] = None) -> ProcheironConfig:
    root = resolve_root(explicit_root=explicit_root, start=start)
    config_path = root / CONFIG_REL
    if not config_path.is_file():
        raise ResolveError(f'Procheiron config missing at {config_path}; refusing silent deployment fallback')
    raw = parse_simple_yaml(config_path)
    profile = str(raw.get('profile') or '').strip()
    if not profile:
        raise ResolveError(f'{config_path}: required key profile is missing')
    version = str(raw.get('version') or '').strip()
    # ponytail: config 'root' is intentionally not consulted — the resolved root (env/ancestor/--root)
    # remains the authority for this run; a config/runtime mismatch is exposed to validators, not acted on.
    paths_raw = raw.get('paths')
    if not isinstance(paths_raw, dict):
        raise ResolveError(f'{config_path}: required mapping paths is missing')
    paths: Dict[str, Path] = {}
    for key, val in paths_raw.items():
        p = Path(str(val)).expanduser()
        paths[str(key)] = p if p.is_absolute() else root / p
    return ProcheironConfig(root=root, config_path=config_path, version=version, profile=profile, paths=paths, raw=raw)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Resolve Procheiron root/config paths')
    parser.add_argument('--root', help='explicit root (wins over env and ancestor discovery)')
    parser.add_argument('--print-root', action='store_true')
    parser.add_argument('--print-config', action='store_true')
    parser.add_argument('--get-path', help='print resolved paths.<key>')
    args = parser.parse_args(argv)
    try:
        if args.print_root and not (args.print_config or args.get_path):
            print(resolve_root(args.root))
            return 0
        cfg = load_config(args.root)
        if args.print_root:
            print(cfg.root)
        if args.print_config:
            print(cfg.config_path)
        if args.get_path:
            print(cfg.path(args.get_path))
        if not (args.print_root or args.print_config or args.get_path):
            print(f'root={cfg.root}')
            print(f'profile={cfg.profile}')
            print(f'version={cfg.version}')
            for key in sorted(cfg.paths):
                print(f'paths.{key}={cfg.paths[key]}')
        return 0
    except ResolveError as exc:
        print(f'procheiron_resolve: ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
