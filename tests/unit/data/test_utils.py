from footbot.data.utils import get_safe_web_name


def test_get_safe_web_name():
    assert get_safe_web_name("abć") == "abc"
