from qud_object_tree import qindex
from qudobject_wiki import escape_ampersands


def test_escape_ampersands():
    assert escape_ampersands('&yfloating&G &Yglowsphere') == '&amp;yfloating&amp;G &amp;Yglowsphere'


def test_render_wiki_templates():
    """Test rendering the wiki template for each object to find any exceptions."""
    for name, obj in qindex.items():
        if obj.is_wiki_eligible():
            obj.wiki_template()
