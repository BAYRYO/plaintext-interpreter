import pytest
from src.html_converter import HTMLConverter

@pytest.fixture
def converter():
    return HTMLConverter(config_path="configs/config.yml")


def test_process_titles_basic(converter):
    html = "<h1>Title 1</h1><h2>Title 2</h2><h3>Title 3</h3>"
    processed, titles = converter.process_titles(html)

    assert [t.level for t in titles] == [1, 2, 3]
    assert [t.text for t in titles] == ["Title 1", "Title 2", "Title 3"]
    assert [t.id for t in titles] == ["section1", "section2", "section3"]
