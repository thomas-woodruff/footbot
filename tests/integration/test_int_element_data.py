from footbot.data.element_data import get_bootstrap


def test_get_bootstrap():
    data = get_bootstrap()
    assert "elements" in data
    assert "events" in data
    assert isinstance(data["elements"], list)
    assert isinstance(data["events"], list)
