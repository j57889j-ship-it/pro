from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_question_and_import_callbacks_are_namespaced():
    content = text("handlers/admin/content.py")
    user_books = text("handlers/user/books.py")
    assert 'admqbook:' in content
    assert 'admimportbook:' in content
    assert 'startswith("book:")' in user_books
    assert 'startswith("book:")' not in content


def test_admin_settings_callback_is_handled():
    settings = text("handlers/admin/settings.py")
    navigation = text("handlers/admin/navigation.py")
    assert 'callback_data="adm:settings"' in settings
    assert 'F.data == "adm:settings"' in navigation


def test_reaction_updates_webhook_channel_posts():
    main = text("main.py")
    constants = text("constants.py")
    assert '"channel_post"' in constants
    assert 'allowed_updates=WEBHOOK_UPDATE_TYPES' in main
    assert 'set_webhook(' in main


def test_reaction_settings_persist():
    service = text("services/settings.py")
    assert 'await session.commit()' in service
