from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "app"


def test_inline_callbacks_have_handlers():
    inline = (ROOT / "keyboards" / "inline.py").read_text(encoding="utf-8")
    source = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.py"))

    callbacks = set(re.findall(r'callback_data="([^"$]+)"', inline))
    exact = set(re.findall(r'(?:F|c)\.data\s*==\s*"([^"]+)"', source))
    prefixes = set(re.findall(r'(?:F|c)\.data\.startswith\("([^"]+)"\)', source))
    prefixes |= set(re.findall(r'c\.data.*?startswith\("([^"]+)"\)', source))
    missing = [cb for cb in callbacks if cb not in exact and not any(cb.startswith(prefix) for prefix in prefixes)]
    assert not missing, f"Unhandled callbacks: {missing}"
