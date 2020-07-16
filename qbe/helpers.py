def displayname_to_wiki(phrase: str):
    """Convert display names from the new color templating format to usage of
    the wiki's {{Qud shader}} template.
    {{Qud shader}} syntax: https://cavesofqud.gamepedia.com/Template:Qud_shader/doc
    Example: {{Qud shader|text=Stopsvalinn|colors=R-r-K-y-Y|type=sequence|unbolded=true}}

    Examples of display names in game format:
    Game displayname: {{c-C-Y-W alternation|maghammer}}
    Game displayname: {{R-r-K-y-Y sequence|Stopsvalinn}}
    Game displayname: {{y|raw beetle meat}}
    Game displayname: {{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}
    Game displayname: {{K|{{crysteel|crysteel}} mace}}  # oh no
    """
    # Parser states:
    READING_TEXT = 1
    ONE_LEFT_BRACE = 2
    READING_SHADER = 3
    ONE_RIGHT_BRACE = 4
    state = READING_TEXT
    shader_stack = [None]  # default white
    new_shader_name = ''
    parsed = []  # tuples of character, current shader
    for char in phrase:
        if state == READING_TEXT:
            if char == '{':
                state = ONE_LEFT_BRACE
            elif char == '}':
                state = ONE_RIGHT_BRACE
            else:
                parsed.append((char, shader_stack[-1]))
        elif state == ONE_LEFT_BRACE:
            if char == '{':
                state = READING_SHADER
            else:
                state = READING_TEXT
                parsed.append(('{', shader_stack[-1]))  # include the { that we didn't write
                parsed.append((char, shader_stack[-1]))
        elif state == READING_SHADER:
            if char == '|':
                state = READING_TEXT
                shader_stack.append(new_shader_name)
                new_shader_name = ''
            else:
                new_shader_name += char
        elif state == ONE_RIGHT_BRACE:
            state = READING_TEXT
            if char == '}':
                if len(shader_stack) == 1:
                    error = f"Unexpected }} occurred while parsing {phrase}"
                    raise ValueError(error)
                else:
                    shader_stack.pop()
            else:
                parsed.append((char, shader_stack[-1]))
    # we've parsed all printable chars:
    # now, conflate sequential chars with the same shader
    output = []
    current_shader = None
    current_fragment = ''
    for character, shader in parsed:
        if shader == current_shader:
            current_fragment += character
        else:
            if len(current_fragment) > 0:
                output.append((current_fragment, current_shader))
            current_fragment = character
            current_shader = shader
    if len(current_fragment) > 0:
        output.append((current_fragment, current_shader))
    # finally, convert to our custom wiki templates
    displays = []
    for text, specifier in output:
        if specifier is None:
            displays.append(text)
        elif ' ' in specifier:
            colors, _type = specifier.split(' ')
            display = f'{{{{Qud shader|text={text}|colors={colors}|type={_type}}}}}'
            displays.append(display)
        else:  # simple specifier
            display = f'{{{{Qud shader|{specifier}|{text}}}}}'
            displays.append(display)
    return ''.join(displays)
