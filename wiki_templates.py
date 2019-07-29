"""Templates class for Caves of Qud wiki work.

The point of this is to be able to create one template from XML attribs, and another from the
text of an existing wiki page, then compare them directly with ==."""

class Template:
    def __init__(self, attribs):
        self.attribs = attribs

    @classmethod
    def from_text(cls, text):
        """Construct a Template"""
    def __eq__(self, other):
        return self.attribs == other.attribs