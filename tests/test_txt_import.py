from app.utils.txt_import import parse_txt


def test_minimal_format_without_extra_metadata():
    text = '''1. Savol?
A: A variant
B: B variant
C: C variant
D: D variant
ANSWER: C

2. Ikkinchi?
A: A variant
B: B variant
C: C variant
D: D variant
ANSWER: 1
'''
    parsed, errors, duplicates = parse_txt(text, 100)
    assert len(parsed) == 2
    assert not errors
    assert duplicates == 0
    assert [q.correct_option for q in parsed] == ["C", "A"]
    assert parsed[0].explanation == ""


def test_parentheses_dot_and_legacy_lines_are_tolerated():
    text = '''1) Savol?
A) A variant
B. B variant
C: C variant
D: D variant
ANSWER: D
DIFFICULTY: hard
EXPLANATION: ignored
'''
    parsed, errors, duplicates = parse_txt(text, 100)
    assert len(parsed) == 1
    assert not errors
    assert duplicates == 0
    assert parsed[0].correct_option == "D"


def test_duplicate_and_limit():
    blocks = []
    for i in range(1, 104):
        text = "Takroriy" if i in {2, 3} else f"Savol {i}"
        blocks.append(f"{i}. {text}?\nA: A{i}\nB: B{i}\nC: C{i}\nD: D{i}\nANSWER: A")
    parsed, errors, duplicates = parse_txt("\n\n".join(blocks), 100)
    assert len(parsed) == 99
    assert duplicates == 1
    assert any("maksimal 100 ta" in e for e in errors)
