"""Test cases for wikitemplate.py"""

from wikitemplate import WikiTemplate


def test_create_from_attribs():
    attribs = {'title': '{{Qud text|&amp;ycommunications panel}}',
               'image': 'communications panel.png'}
    template = WikiTemplate('Item', attribs)


def test_create_from_text():
    text = """{{Item
| title = {{Qud text|&amp;ycommunications panel}}
| image = communications panel.png
}}
"""
    template = WikiTemplate.from_text('Item', text)


def test_compare_attribs_text():
    attribs = {'title': '{{Qud text|&amp;ycommunications panel}}',
               'image': 'communications panel.png'}
    template_a = WikiTemplate('Item', attribs)
    text = """{{Item
| title = {{Qud text|&amp;ycommunications panel}}
| image = communications panel.png
}}
"""
    template_t = WikiTemplate.from_text('Item', text)
    assert template_a == template_t


def test_text_roundtrip_comparison():
    text = """{{Item
| title = {{Qud text|&amp;ycommunications panel}}
| image = communications panel.png
}}
"""
    template = WikiTemplate.from_text('Item', text)
    assert template == WikiTemplate.from_text('Item', template.to_text())
