from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"


def all_py_text():
    for path in ROOT.rglob("*.py"):
        yield path, path.read_text(encoding="utf-8")


def test_main_menu_labels_match_handlers():
    text = "\n".join(s for _, s in all_py_text())
    for label in ["📚 KITOBLAR", "🧠 TEST", "🏆 TOP", "👤 PROFIL", "ℹ️ YORDAM", "🛠 ADMIN"]:
        assert label in text


def test_back_buttons_have_handlers():
    text = "\n".join(s for _, s in all_py_text())
    for label in [
        "⬅️ ASOSIY MENYU", "⬅️ KITOBLAR", "⬅️ TESTLAR", "⬅️ ADMIN PANEL",
        "⬅️ KONTENT", "⬅️ FOYDALANUVCHILAR", "⬅️ KANALLAR", "⬅️ REYTING",
        "⬅️ TEST BOSHQARUVI", "⬅️ SOZLAMALAR",
    ]:
        assert (f'F.text == "{label}"' in text) or (label in text and "F.text.in_" in text)


def test_no_referral_or_time_based_leaderboards():
    text = "\n".join(s.lower() for _, s in all_py_text())
    for forbidden in ("referral", "weekly top", "monthly top", "season top"):
        assert forbidden not in text


def test_html_parse_mode_enabled():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "ParseMode.HTML" in main


def test_quiz_uses_inline_answer_callbacks():
    inline = (ROOT / "keyboards" / "inline.py").read_text(encoding="utf-8")
    quiz = (ROOT / "handlers" / "user" / "quiz.py").read_text(encoding="utf-8")
    assert "quiz_answer:" in inline
    assert "quiz_answer:" in quiz


def test_health_supports_head_for_external_monitors():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '@app.head("/health")' in main


def test_book_list_back_returns_to_books_home():
    inline = (ROOT / "keyboards" / "inline.py").read_text(encoding="utf-8")
    assert 'back_callback: str = "books:home"' in inline


def test_uptime_liveness_supports_get_and_head():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '@app.get("/live")' in main
    assert '@app.head("/live")' in main


def test_quiz_book_picker_uses_dedicated_callback_prefix():
    quiz = (ROOT / "handlers" / "user" / "quiz.py").read_text(encoding="utf-8")
    inline = (ROOT / "keyboards" / "inline.py").read_text(encoding="utf-8")
    assert 'item_callback_prefix="quizbook"' in quiz
    assert 'callback_data=f"{item_callback_prefix}:{book.id}"' in inline


def test_quiz_answer_has_double_tap_guard_and_db_guard():
    quiz = (ROOT / "handlers" / "user" / "quiz.py").read_text(encoding="utf-8")
    models = (ROOT / "database" / "models.py").read_text(encoding="utf-8")
    assert 'redis.lock(f"quiz-answer:' in quiz
    assert 'UniqueConstraint("attempt_id", "question_id"' in models


def test_bot_profile_is_branded():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'set_my_short_description("📚 Kitoblar • 🧠 Testlar • 🏆 TOP")' in main
    assert 'set_my_description(' in main
