from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class ParsedQuestion:
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: str = ""


def _normalize_answer(raw: str) -> str:
    value = raw.strip().upper()
    return {"1": "A", "2": "B", "3": "C", "4": "D"}.get(value, value)


def _split_blocks(content: str) -> list[list[str]]:
    normalized = content.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    blocks: list[list[str]] = []
    current: list[str] = []
    question_re = re.compile(r"^\s*\d+\s*(?:[.)]|[-:]\s+).+$")
    for raw in lines:
        line = raw.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        if current and question_re.match(line):
            blocks.append(current)
            current = []
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _field(lines: list[str], letter: str) -> str:
    pattern = re.compile(rf"^\s*{letter}\s*[.):]\s*(.*?)\s*$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return ""


def _answer(lines: list[str]) -> str:
    pattern = re.compile(r"^\s*(?:ANSWER|JAVOB)\s*[:=\-]\s*([A-D1-4])\s*$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            return _normalize_answer(match.group(1))
    return ""


def _question_text(lines: list[str]) -> str:
    result: list[str] = []
    for line in lines:
        if re.match(r"^\s*[A-D]\s*[.):]", line, re.IGNORECASE):
            continue
        if re.match(r"^\s*(?:ANSWER|JAVOB)\s*[:=\-]", line, re.IGNORECASE):
            continue
        # Optional legacy metadata is ignored; it is not required.
        if re.match(r"^\s*(?:DIFFICULTY|EXPLANATION)\s*[:=]", line, re.IGNORECASE):
            continue
        result.append(line)
    if result:
        result[0] = re.sub(r"^\s*\d+\s*(?:[.)]|[-:]\s+)\s*", "", result[0])
    return " ".join(x.strip() for x in result if x.strip()).strip()


def _normalize_for_duplicate(text: str) -> str:
    return " ".join(text.casefold().split())


def parse_txt(content: str, limit: int = 100) -> tuple[list[ParsedQuestion], list[str], int]:
    blocks = _split_blocks(content)
    errors: list[str] = []
    parsed: list[ParsedQuestion] = []
    seen: set[str] = set()
    duplicate_count = 0

    if not content.strip():
        return [], ["Fayl bo‘sh."], 0
    if len(blocks) > limit:
        errors.append(f"Faylda {len(blocks)} ta savol bor; maksimal {limit} ta qabul qilinadi.")
        blocks = blocks[:limit]

    for idx, lines in enumerate(blocks, start=1):
        text = _question_text(lines)
        a, b, c, d = (_field(lines, x) for x in "ABCD")
        ans = _answer(lines)
        issues: list[str] = []
        options = (a, b, c, d)
        if len(text) < 3:
            issues.append("savol matni yo‘q yoki juda qisqa")
        if any(not value for value in options):
            issues.append("A/B/C/D variantlari to‘liq emas")
        elif len(set(_normalize_for_duplicate(value) for value in options)) < 4:
            issues.append("variantlar bir-biridan farq qilishi kerak")
        if ans not in {"A", "B", "C", "D"}:
            issues.append("ANSWER: A/B/C/D yoki 1/2/3/4 bo‘lishi kerak")
        normalized = _normalize_for_duplicate(text)
        if normalized and normalized in seen:
            duplicate_count += 1
            issues.append("fayl ichida duplicate")
        if issues:
            errors.append(f"{idx}-savol: " + ", ".join(issues))
            continue
        seen.add(normalized)
        parsed.append(
            ParsedQuestion(
                text=text,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d,
                correct_option=ans,
            )
        )
    return parsed, errors, duplicate_count
