from hagadias.helpers import parse_qud_colors


def displayname_to_wiki(phrase: str):
    """Convert display names from the new color templating format to usage of
    the wiki's {{Qud shader}} template.

    See hagadias.helpers.parse_qud_colors for details of the new in-game
    coloring templates.

    {{Qud shader}} syntax: https://cavesofqud.gamepedia.com/Template:Qud_shader/doc
    Example: {{Qud shader|text=Stopsvalinn|colors=R-r-K-y-Y|type=sequence|unbolded=true}}"""
    parsed = parse_qud_colors(phrase)
    output = []
    for text, shader in parsed:
        if shader is None:
            output.append(text)
        elif ' ' in shader:
            # shader has arguments
            colors, _type = shader.split(' ')
            template = '{{Qud shader|text={{(}}' + text + '{{)}}|colors=' + colors + '|type='
            + _type + '}}'  # text surrounded in {} to preserve whitespace
            output.append(template)
        else:
            # plain shader
            template = '{{Qud shader|' + shader + '|{{(}}' + text + '{{)}}}}'
            output.append(template)
    return ''.join(output)
