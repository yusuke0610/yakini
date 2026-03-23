from app.messages import get_error, get_success, load_messages


def test_get_error_returns_message_by_key() -> None:
    load_messages()

    assert get_error("auth.invalid_credentials") == "メールアドレスまたはパスワードが正しくありません。"


def test_get_error_formats_placeholders() -> None:
    load_messages()

    assert get_error("validation.required_field", field="メールアドレス") == "メールアドレスは必須です。"


def test_get_success_formats_placeholders() -> None:
    load_messages()

    assert get_success("document.saved", document="職務経歴書") == "職務経歴書を保存しました。"


def test_missing_message_key_falls_back_to_key() -> None:
    load_messages()

    assert get_error("unknown.category.key") == "unknown.category.key"
