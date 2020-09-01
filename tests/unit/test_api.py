from footbot.main import home_route


def test_home():
    assert 'Greetings' in home_route()
