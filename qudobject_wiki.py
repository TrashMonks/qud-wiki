import re

from config import config
from qudobject_props import QudObjectProps


def escape_ampersands(text: str):
    """Convert & to &amp; for use in wiki template."""
    return re.sub('&', '&amp;', text)


class QudObjectWiki(QudObjectProps):
    """Represents a Caves of Qud game object to the wiki interface.

    Inherits from QudObjectProps which provides all the derived information about the object.

    Passes requests to its QudObjectProps superclass and translates the results for templates,
    with HTML escaped characters, etc."""

    def wiki_template(self):
        """Return the fully wikified template representing this object and add a category."""
        fields = config['Templates']['Fields']
        template = self.wiki_template_type()
        intro_string = ''
        before_title = "{{Qud text|"
        after_title = "}}"
        text = intro_string + '{{' + f'{template}\n'
        text += "| title = " + before_title + self.title + after_title + "\n"
        for field in fields:
            if field == 'title':
                continue
            if template == 'Corpse' and field in ['hunger', 'image']:
                continue
            else:
                attrib = getattr(self, field)
                if attrib is not None:
                    if field == 'renderstr':
                        attrib = attrib.replace('}', '&#125;')
                    text += f"| {field} = {attrib}\n"
        category = self.wiki_category()
        if category:
            text += f"| categories = {category}\n"
        text += "}}\n"
        return text

    def wiki_template_type(self) -> str:
        """Determine which template to use for the wiki."""
        val = "Item"
        not_corpses = ('Albino Ape Pelt',
                       'Crystal of Eve',
                       'Black Puma Haunch',
                       'Arsplice Seed',
                       'Albino Ape Heart',
                       'Ogre Ape Heart')
        characters = ['Creature', 'BasePlant', 'BaseFungus', 'Baetyl', 'Wall']
        if any(self.inherits_from(character) for character in characters):
            val = "Character"
        elif self.inherits_from('Food'):
            val = "Food"
        elif (self.inherits_from('RobotLimb') or self.inherits_from('Corpse')) and\
                (self.name not in not_corpses):
            val = "Corpse"
        return val

    def wiki_category(self):
        """Determine what configured wiki category this object belongs in."""
        cat = None
        for config_cat, names in config['Wiki']['Categories'].items():
            for name in names:
                if self.inherits_from(name):
                    cat = config_cat
        return cat

    def is_wiki_eligible(self) -> bool:
        if self.name == 'Argyve\'s Data Disk Encoded':
            return True  # special case because of '['
        if self.is_specified('tag_BaseObject'):
            return False
        if self.displayname == '' or '[' in self.displayname:
            return False
        eligible = True  # equal to initial +Object in config.yml
        for entry in config['Wiki']['Article black+whitelist categories']:
            if entry.startswith('*') and self.inherits_from(entry[1:]):
                eligible = True
            elif entry.startswith('/') and self.inherits_from(entry[1:]):
                eligible = False
            elif entry.startswith('+') and self.name == entry[1:]:
                eligible = True
            elif entry.startswith('-') and self.name == entry[1:]:
                eligible = False
        return eligible

    # PROPERTIES
    # The following properties are implemented to make wiki formatting far simpler.
    # Sorted alphabetically. All return types should be strings or None.

    @property
    def ammodamagetypes(self):
        """Damage attributes associated with the projectile (</br> delimited)."""
        types = super().ammodamagetypes
        if types is not None:
            return '</br>'.join(types)

    @property
    def colorstr(self):
        """The Qud color code associated with the RenderString."""
        colorstr = super().colorstr
        if colorstr is not None:
            return escape_ampersands(colorstr)

    @property
    def cookeffect(self):
        """The possible cooking effects of an item."""
        effect = super().cookeffect
        if effect is not None:
            return ','.join(f'{{{{CookEffect ID to name|{val}}}}}' for val in effect)

    @property
    def desc(self):
        """The short description of the object, with color codes included (ampersands escaped)."""
        desc = super().desc
        if desc is not None:
            return escape_ampersands(desc)

    @property
    def extra(self):
        """Any other features that do not have an associated variable."""
        fields = super().extra
        if fields is not None:
            text = ' | '.join(f'{field} = {attrib}' for field, attrib in fields)
            return f'{{{{Extra info|{text}}}}}'

    @property
    def faction(self):
        """The factions this creature has loyalty to, formatted for the wiki."""
        # <part Name="Brain" Wanders="false" Factions="Joppa-100,Barathrumites-100" />
        factions = super().faction
        if factions is not None:
            ret = ''
            for faction, value in factions:
                if ret != '':
                    ret += '</br>'
                ret += f'{{{{creature faction|{{{{FactionID to name|{faction}}}}}|{value}}}}}'
            return ret

    @property
    def title(self):
        """The display name of the item, with ampersands escaped."""
        title = super().title
        if title is not None:
            return escape_ampersands(title)

    @property
    def uniquechara(self):
        if self.inherits_from('Creature') or self.inherits_from('ActivePlant'):
            if self.name in config['Wiki']['Categories']['Unique Characters']:
                return 'yes'
