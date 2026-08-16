"""Evaluates the object-path formulas in a character StatSheet.json file.

Usable standalone (CLI) or imported by the Flask app (load_and_compute / StatSheetEngine).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any


class FormulaError(Exception):
    """Raised for malformed formulas or paths that cannot be resolved."""

class CouldNotReach(Exception):
    """Raised for not found paths in formulas."""


class CircularReferenceError(FormulaError):
    """Raised when a formula (directly or indirectly) depends on itself."""


class AggregateList(list):
    """Marks a list produced by a 'rows[]' path so SUM() can be told apart from a plain path."""


_TOKEN_RE = re.compile(
    r"""
      (?P<NUMBER>\d+(?:\.\d+)?)
    | (?P<PATH>[A-Za-zÀ-ÖØ-öø-ÿ_][A-Za-zÀ-ÖØ-öø-ÿ0-9_.\[\]/]*)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<COMMA>,)
    | (?P<PLUS>\+)
    | (?P<MINUS>-)
    | (?P<STAR>\*)
    | (?P<SLASH>/)
    | (?P<SKIP>\s+)
    """,
    re.VERBOSE,
)

_FUNCTIONS = {"MIN", "MAX", "ABS", "MEDIAN", "SUM"}


def _tokenize(expr: str) -> list[tuple[str, str]]:
    tokens = []
    pos = 0
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m:
            raise FormulaError(f"Unerwartetes Zeichen in Formel {expr!r} an Position {pos}")
        kind = m.lastgroup
        if kind != "SKIP":
            tokens.append((kind, m.group()))
        pos = m.end()
    return tokens


class _Parser:
    """Recursive-descent parser/evaluator for the small formula language."""

    def __init__(self, tokens: list[tuple[str, str]], engine: "StatSheetEngine"):
        self.tokens = tokens
        self.pos = 0
        self.engine = engine

    def _peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> tuple[str, str]:
        tok = self._peek()
        if tok is None:
            raise FormulaError("Unerwartetes Ende der Formel")
        self.pos += 1
        return tok

    def parse(self) -> float:
        value = self._expr()
        if self._peek() is not None:
            raise FormulaError(f"Ueberschuessige Token ab Position {self.pos}")
        return value

    def _expr(self):
        value = self._term()
        while self._peek() and self._peek()[0] in ("PLUS", "MINUS"):
            kind, _ = self._advance()
            rhs = self._term()
            value = value + rhs if kind == "PLUS" else value - rhs
        return value

    def _term(self):
        value = self._factor()
        while self._peek() and self._peek()[0] in ("STAR", "SLASH"):
            kind, _ = self._advance()
            rhs = self._factor()
            value = value * rhs if kind == "STAR" else value / rhs
        return value

    def _factor(self):
        tok = self._peek()
        if tok is None:
            raise FormulaError("Unerwartetes Ende der Formel")
        if tok[0] == "MINUS":
            self._advance()
            return -self._factor()
        if tok[0] == "NUMBER":
            self._advance()
            text = tok[1]
            return float(text) if "." in text else int(text)
        if tok[0] == "LPAREN":
            self._advance()
            value = self._expr()
            self._expect("RPAREN")
            return value
        if tok[0] == "PATH":
            self._advance()
            nxt = self._peek()
            if nxt and nxt[0] == "LPAREN" and tok[1].upper() in _FUNCTIONS:
                return self._call(tok[1].upper())
            return self.engine._get_by_path(tok[1])
        raise FormulaError(f"Unerwartetes Token {tok}")

    def _expect(self, kind: str) -> None:
        tok = self._peek()
        if not tok or tok[0] != kind:
            raise FormulaError(f"Erwartet {kind}, gefunden {tok}")
        self._advance()

    def _call(self, name: str):
        self._expect("LPAREN")
        args = [self._expr()]
        while self._peek() and self._peek()[0] == "COMMA":
            self._advance()
            args.append(self._expr())
        self._expect("RPAREN")
        return _apply_function(name, args)


def _flatten(values: list[Any]) -> list[float]:
    flat: list[float] = []
    for v in values:
        if isinstance(v, list):
            flat.extend(v)
        else:
            flat.append(v)
    return flat


def _apply_function(name: str, args: list[Any]):
    if name == "SUM":
        return sum(_flatten(args))
    flat = _flatten(args)
    if name == "MIN":
        return min(flat)
    if name == "MAX":
        return max(flat)
    if name == "MEDIAN":
        return statistics.median(flat)
    if name == "ABS":
        if len(flat) != 1:
            raise FormulaError("ABS() erwartet genau ein Argument")
        return abs(flat[0])
    raise FormulaError(f"Unbekannte Funktion {name}")


class StatSheetEngine:
    """Lazily evaluates every formula field in a StatSheet document, caching results and
    writing computed values back into the same in-memory document (doc["...']["value"])."""

    def __init__(self, doc: dict):
        self.doc = doc
        self._cache: dict[str, Any] = {}
        self._computing: set[str] = set()

    def get(self, path: str):
        """Public entry point: resolve a dotted object path (e.g. 'stats.Mut.wert')."""
        return self._get_by_path(path)

    def compute_all(self) -> dict:
        """Force-evaluate every formula field in stats/talents/skills/meta. Returns the doc."""
        for section in ("meta", "stats", "talents", "skills"):
            node = self.doc.get(section)
            if isinstance(node, dict):
                self._walk(node, [section])
        return self.doc

    def _walk(self, node: dict, path_parts: list[str]) -> None:
        if "formula" in node and "value" in node and len(node) == 2:
            self._get_by_path(".".join(path_parts))
            return
        for key, value in node.items():
            if isinstance(value, dict):
                self._walk(value, path_parts + [key])

    def _get_by_path(self, path: str):
        parts = path.split(".")
        return self._resolve(self.doc, parts, [])

    def _resolve(self, node: Any, parts: list[str], path_so_far: list[str]):
        part = parts[0]
        rest = parts[1:]
        if part.endswith("[]"):
            key = part[:-2]
            rows = node[key]
            return AggregateList(self._resolve_row(item, rest) for item in rows)

        child = node[part]
        if isinstance(child, dict) and "formula" in child and "value" in child and len(child) == 2:
            if rest not in ([], ["value"]):
                raise FormulaError(f"Ungueltiger Pfad hinter Formel-Feld: {'.'.join(path_so_far + [part] + rest)}")
            return self._compute_field(child, path_so_far + [part])

        if not rest:
            return child
        return self._resolve(child, rest, path_so_far + [part])

    def _resolve_row(self, row: dict, parts: list[str]):
        node: Any = row
        if "ID" in row:
            id = row.get("ID")
            if id.startswith("Item_"):
                items_file = Path(__file__).parent / "data/Global/Items.json"
                items_data = json.loads(items_file.read_text(encoding="utf-8"))
                if id not in items_data:
                    raise CouldNotReach(f"Item {id} nicht in items.json gefunden")
                node = items_data.get(id, {})
            if id.startswith("Skill_"):
                skills_file = Path(__file__).parent / "data/Global/Skills.json"
                skills_data = json.loads(skills_file.read_text(encoding="utf-8"))
                if id not in skills_data:
                    raise CouldNotReach(f"Skill {id} nicht in Skills.json gefunden")
                node = skills_data.get(id, {})
            if id.startswith("SpellEffect_"):
                spell_effects_file = Path(__file__).parent / "data/Global/SpellEffects.json"
                spell_effects_data = json.loads(spell_effects_file.read_text(encoding="utf-8"))
                if id not in spell_effects_data:
                    raise CouldNotReach(f"SpellEffect {id} nicht in SpellEffects.json gefunden")
                node = spell_effects_data.get(id, {})
            if id.startswith("StatusEffekt_"):
                status_effects_file = Path(__file__).parent / "data/Global/StatusEffekts.json"
                status_effects_data = json.loads(status_effects_file.read_text(encoding="utf-8"))
                if id not in status_effects_data:
                    raise CouldNotReach(f"StatusEffekt {id} nicht in StatusEffekt.json gefunden")
                node = status_effects_data.get(id, {})

        for i, part in enumerate(parts):
            if not isinstance(node, dict):
                raise CouldNotReach(f"Pfad {'.'.join(parts)} konnte nicht erreicht werden (Teil {part} ist kein Objekt)")
            if part not in node:
                raise CouldNotReach(f"Pfad {'.'.join(parts)} konnte nicht erreicht werden (Schlüssel {part!r} fehlt)")
            node = node[part]

        if node is None:
            raise CouldNotReach(f"Pfad {'.'.join(parts)} konnte nicht erreicht werden (Endwert ist None)")
        if node == {}:
            raise CouldNotReach(f"Pfad {'.'.join(parts)} konnte nicht erreicht werden (Endwert ist leeres Objekt)")
        if not isinstance(node, (int, float)):
            raise CouldNotReach(f"Pfad {'.'.join(parts)} konnte nicht erreicht werden (Endwert ist kein Zahl)")
        return node

    def _compute_field(self, field: dict, path_parts: list[str]):
        path_str = ".".join(path_parts)
        if path_str in self._cache:
            return self._cache[path_str]
        if path_str in self._computing:
            raise CircularReferenceError(f"Zirkulaerer Bezug bei {path_str}")

        formula = field.get("formula")
        if formula is None:
            value = field["value"]
        else:
            self._computing.add(path_str)
            try:
                tokens = _tokenize(formula)
                value = _Parser(tokens, self).parse()
            finally:
                self._computing.discard(path_str)
            # jeder berechnete Feldwert ist ein "finaler Wert" und wird hier abgerundet (z.B. Monate im Alter)
            #value = math.floor(value)
            field["value"] = value

        self._cache[path_str] = value
        return value


def load_and_compute(path: str | Path) -> dict:
    """Load a StatSheet.json file, compute all formulas, and return the updated document."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    StatSheetEngine(doc).compute_all()
    return doc


def _print_summary(doc: dict) -> None:
    meta = doc["meta"]
    print("=== Meta ===")
    for key, field in meta.items():
        print(f"  {key}: {field['value']}")

    print("\n=== Stats ===")
    for stat_name, fields in doc["stats"].items():
        print(f"  {stat_name}: wert={fields['wert']['value']} "
              f"(min={fields['min']['value']}, max_konst={fields['max_konst']['value']}, "
              f"malus_under={fields['malus_for_under']['value']}, malus_over={fields['malus_for_over']['value']})")

    print("\n=== Talente ===")
    for talent_name, fields in doc["talents"].items():
        print(f"  {talent_name}: wert={fields['wert']['value']} "
              f"(ausgeglichenheit={fields['ausgeglichenheit_bonus']['value']}, bonus={fields['bonus']['value']})")

    print("\n=== Fertigkeiten (FW) ===")
    for talent_name, skills in doc["skills"].items():
        if talent_name.startswith("_"):
            continue
        for skill_name, fields in skills.items():
            print(f"  [{talent_name}] {skill_name}: fw={fields['fw']['value']}")


def main() -> None:
    #get python exekutable path
    #walk for every user in the data/User folder
    #walk in user Folder every folder and akt if there is a StatSheet.json file, load and compute it, print its summary and write it back to the same file
   
    executable_path = Path(__file__).parent
   
    for user_folder in (executable_path / "data/User").iterdir():
        if not user_folder.is_dir():
            continue
        for stat_sheet_file in user_folder.rglob("StatSheet.json"):
            print(f"Processing {stat_sheet_file}")
            doc = load_and_compute(stat_sheet_file)
            _print_summary(doc)
            stat_sheet_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
