from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1] / "app"


def source():
    return "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.py"))


def test_no_old_admin_book_callback_collision():
    content = (ROOT / "handlers" / "admin" / "content.py").read_text(encoding="utf-8")
    assert 'startswith("book:")' not in content
    assert 'startswith("admqbook:")' in content
    assert 'startswith("admimportbook:")' in content


def test_webhook_explicitly_subscribes_to_channel_posts():
    constants = (ROOT / "constants.py").read_text(encoding="utf-8")
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '"channel_post"' in constants
    assert 'allowed_updates=WEBHOOK_UPDATE_TYPES' in main
    assert 'await bot.set_webhook(' in main


def test_webhook_errors_return_non_2xx_for_retry():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'raise HTTPException(status_code=500' in main


def test_health_and_live_support_get_and_head():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    for path in ("/live", "/health"):
        assert f'@app.get("{path}")' in main
        assert f'@app.head("{path}")' in main


def test_html_and_escape_helpers_exist():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    ui = (ROOT / "utils" / "ui.py").read_text(encoding="utf-8")
    assert "ParseMode.HTML" in main
    assert "def h(" in ui
    assert "escape(" in ui


def test_reaction_pipeline_is_present():
    reaction = (ROOT / "handlers" / "channel_reactions.py").read_text(encoding="utf-8")
    assert '@router.channel_post()' in reaction
    assert 'set_message_reaction' in reaction
    assert 'last_channel_post_id' in reaction


def test_quiz_answers_bind_attempt_and_index():
    inline = (ROOT / "keyboards" / "inline.py").read_text(encoding="utf-8")
    quiz = (ROOT / "handlers" / "user" / "quiz.py").read_text(encoding="utf-8")
    assert 'quiz_answer:{attempt_id}:{index}' in inline
    assert 'startswith("quiz_answer:")' in quiz
    assert 'redis.lock(f"quiz-answer:' in quiz


def test_navigation_registered_before_feature_handlers():
    text = (ROOT / "handlers" / "user" / "__init__.py").read_text(encoding="utf-8")
    assert 'for module in (navigation, start, books, quiz' in text


def test_no_referral_or_time_based_top():
    text = source().lower()
    for forbidden in ("referral", "haftalik top", "weekly top", "monthly top", "season top", "mavsum top"):
        assert forbidden not in text
