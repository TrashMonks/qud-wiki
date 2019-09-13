from qud_object_tree import qindex


def test_render_wiki_templates():
    """Test rendering the wiki template for each object to find any exceptions."""
    for name, obj in qindex.items():
        if obj.is_wiki_eligible():
            obj.wiki_template()
