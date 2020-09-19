import footbot.data.element_data as ed


def test_get_bootstrap():
    data = ed.get_bootstrap()
    assert "elements" in data
    assert "events" in data
    assert isinstance(data["elements"], list)
    assert isinstance(data["events"], list)
