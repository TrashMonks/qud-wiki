"""Templates classes for Caves of Qud wiki work.

The point of this is to be able to create one template from XML attribs, and another from the
text of an existing wiki page, then compare them directly with ==.

The template will also do any HTMLification that is required on the QudObject attributes."""

from config import config


class WikiTemplate:
    """Generic class to represent a Caves of Qud wiki template.

    Methods:
        __eq__: allow comparing template to another
    """
    def __init__(self, template_type: str, attribs: dict):
        self.template_type = template_type  # Item, Character, etc.
        # HTMLification of attributes must be done at creation time to allow equality testing
        # with templates created from existing wiki text
        for attrib, value in attribs.items():
            if attrib == 'renderstring':
                # careful not to edit the }} off the end of a final line!
                if value.count('}') == 1:
                    attribs[attrib] = value.replace('}', '&#125;')
                elif value.count('}') == 3:
                    attribs[attrib] = value.replace('}', '&#125;', count=1)
        self.attribs = attribs

    @classmethod
    def from_qud_object(cls, template_type: str, qud_object):
        """Construct a Template by getting the required dictionary from a QudObject."""
        attribs = {}
        fields = config['Templates']['Fields']
        for field in fields:
            attrib = getattr(qud_object, field)
            if attrib is not None:
                attribs[field] = attrib
        return cls(template_type, attribs)

    @classmethod
    def from_text(cls, template_type: str, text: str):
        """Construct a Template from a wiki text, rather than directly from attribs.

        Attribute:value pairs must be given one per line, starting with |

        If this is given a wiki page with more than one template in it, will only operate on
        the first one."""

        text = text.strip()
        if not text.startswith('{{'):
            raise ValueError('Given text template does not start with \'{{\'')
        attribs = {}
        attrib_lines = [line for line in text.split('\n') if line.startswith('|')]
        if len(attrib_lines) == 0:
            raise ValueError('Given text template does not have lines starting with \'|\'')
        for line in attrib_lines:
            attrib, value = line.split('=', maxsplit=1)
            if attrib.startswith('|'):
                attrib = attrib[1:]
            attrib = attrib.strip()
            value = value.strip()
            attribs[attrib] = value
        return cls(template_type, attribs)

    def __eq__(self, other) -> bool:
        """Compare this Template to another Template by checking their attribute dictionaries."""
        return self.template_type == other.template_type and self.attribs == other.attribs

    def __str__(self) -> str:
        """Return a string representation of self in the Caves of Qud wiki item template format."""
        if self.template_type == 'Corpse':
            intro_string = '{{!}}-\n'
            before_title = ''
            after_title = ''
        else: 
            intro_string = ''
            before_title = "{{Qud text|"
            after_title = "}}"
        output = intro_string + '{{' + f'{self.template_type}\n'
        output += "| title = " + before_title + self.attribs['title'] + after_title + "\n"
        for stat in self.attribs:
            if self.attribs[stat] != self.attribs['title']:
                if self.template_type == 'Corpse':
                    if stat not in ['hunger','colorstr','renderstr','image']:
                        output += f"| {stat} = {self.attribs[stat]}\n"
                else:
                    output += f"| {stat} = {self.attribs[stat]}\n"
        output += "}}\n"
        return output