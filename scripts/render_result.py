#!/usr/bin/env python3
"""Render the `sorcar` CLI result (raw YAML) into a short plain-text message.

`sorcar` prints exactly the raw YAML result when stdout is not a TTY. The exact
schema is version-dependent, so this is deliberately defensive: it tries the
known keys and falls back to a trimmed dump of the YAML rather than failing.

Usage: render_result.py <raw-file>   -> plain text on stdout
"""
import sys

try:
    import yaml
except ImportError:  # PyYAML ships with the framework, but do not depend on it
    yaml = None

TEXT_KEYS = ("summary", "final_answer", "result", "answer", "output", "text", "message")
MAX_CHARS = 3500


def render(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return "(agent produced no output)"

    if yaml is None:
        return raw[:MAX_CHARS]

    try:
        data = yaml.safe_load(raw)
    except Exception:  # noqa: BLE001 - unparsable output is still worth reporting
        return raw[:MAX_CHARS]

    if not isinstance(data, dict):
        return str(data)[:MAX_CHARS]

    lines = []

    if "success" in data:
        lines.append(f"success: {data['success']}")

    for key in TEXT_KEYS:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            lines.append("")
            lines.append(val.strip()[:MAX_CHARS])
            break

    # Surface anything else that looks like a short scalar worth seeing.
    for key in ("error", "model", "num_turns", "cost_usd", "duration_ms"):
        val = data.get(key)
        if isinstance(val, (str, int, float, bool)) and str(val).strip():
            lines.append(f"{key}: {val}")

    out = "\n".join(lines).strip()
    return out if out else raw[:MAX_CHARS]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: render_result.py <raw-file>", file=sys.stderr)
        return 2
    try:
        raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        print("(no output file — the agent produced nothing)", file=sys.stderr)
        return 0
    sys.stdout.write(render(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
