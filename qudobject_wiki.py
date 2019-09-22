import re
from typing import Union

from config import config
from hagadias.qudobject_props import QudObjectProps

IMAGE_OVERRIDES = config['Templates']['Image overrides']


def escape_ampersands(text: str):
    """Convert & to &amp; for use in wiki template."""
    return re.sub('&', '&amp;', text)


class QudObjectWiki(QudObjectProps):
    """Represents a Caves of Qud game object to the wiki interface.

    Inherits from QudObjectProps which provides all the derived information about the object.

    Passes requests to its QudObjectProps superclass and translates the results for templates,
    with HTML escaped characters, etc."""

    def wiki_template(self) -> str:
        """Return the fully wikified template representing this object and add a category."""
        fields = config['Templates']['Fields']
        flavor = self.wiki_template_type()
        intro_string = ''
        before_title = "{{Qud text|"
        after_title = "}}"
        template = intro_string + '{{' + f'{flavor}\n'
        template += "| title = " + before_title + self.title + after_title + "\n"
        for field in fields:
            if field == 'title':
                continue
            if flavor == 'Corpse' and field in ['hunger', 'image']:
                continue
            else:
                attrib = getattr(self, field)
                if attrib is not None:
                    if field == 'renderstr':
                        attrib = attrib.replace('}', '&#125;')
                    template += f"| {field} = {attrib}\n"
        category = self.wiki_category()
        if category:
            template += f"| categories = {category}\n"
        template += "}}\n"
        return template

    def wiki_template_type(self) -> str:
        """Determine which template to use for the wiki."""
        flavor = "Item"
        not_corpses = ('Albino Ape Pelt',
                       'Crystal of Eve',
                       'Black Puma Haunch',
                       'Arsplice Seed',
                       'Albino Ape Heart',
                       'Ogre Ape Heart')
        characters = ['Creature', 'BasePlant', 'BaseFungus', 'Baetyl', 'Wall']
        if any(self.inherits_from(character) for character in characters):
            flavor = "Character"
        elif self.inherits_from('Food'):
            flavor = "Food"
        elif (self.inherits_from('RobotLimb') or self.inherits_from('Corpse')) and \
                (self.name not in not_corpses):
            flavor = "Corpse"
        return flavor

    def wiki_category(self) -> str:
        """Determine what configured wiki category this object belongs in."""
        cat = None
        for config_cat, names in config['Wiki']['Categories'].items():
            for name in names:
                if self.inherits_from(name):
                    cat = config_cat
        return cat

    def is_wiki_eligible(self) -> bool:
        """Return whether this object should be included in the wiki."""
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
    def ammodamagetypes(self) -> Union[str, None]:
        """Damage attributes associated with the projectile (</br> delimited)."""
        types = super().ammodamagetypes
        if types is not None:
            return '</br>'.join(types)

    @property
    def butcheredinto(self) -> Union[str, None]:
        """What a corpse item can be butchered into."""
        into = super().butcheredinto
        if into is not None:
            return f'{{{{Corpse pop table|population={self.name}|object={{{{ID to name|' \
                   f'{into}}}}}|id={into}}}}}'

    @property
    def colorstr(self) -> Union[str, None]:
        """The Qud color code associated with the RenderString."""
        colorstr = super().colorstr
        if colorstr is not None:
            return escape_ampersands(colorstr)

    @property
    def cookeffect(self) -> Union[str, None]:
        """The possible cooking effects of an item."""
        effect = super().cookeffect
        if effect is not None:
            return ','.join(f'{{{{CookEffect ID to name|{val}}}}}' for val in effect)

    @property
    def corpse(self) -> Union[str, None]:
        """What corpse a character drops."""
        obj = super().corpse
        if obj is not None:
            return f'{{{{ID to name|{obj}}}}}'

    @property
    def desc(self) -> Union[str, None]:
        """The short description of the object, with color codes included (ampersands escaped)."""
        desc = super().desc
        if desc is not None:
            return escape_ampersands(desc)

    @property
    def dynamictable(self) -> Union[str, None]:
        """What dynamic tables the object is a member of."""
        tables = super().dynamictable
        if tables is not None:
            return ' </br>'.join(f'{{{{Dynamic object|{table}|{self.name}}}}}' for table in tables)

    @property
    def extra(self) -> Union[str, None]:
        """Any other features that do not have an associated variable."""
        fields = []
        extrafields = config['Templates']['ExtraFields']
        for field in extrafields:
            attrib = getattr(self, field)
            if attrib is not None:
                fields.append((field, attrib))
        if len(fields) > 0:
            text = ' | '.join(f'{field} = {attrib}' for field, attrib in fields)
            return f'{{{{Extra info|{text}}}}}'

    @property
    def faction(self) -> Union[str, None]:
        """The factions this creature has loyalty to, formatted for the wiki."""
        # <part Name="Brain" Wanders="false" Factions="Joppa-100,Barathrumites-100" />
        factions = super().faction
        if factions is not None:
            template = ''
            for faction, value in factions:
                if template != '':
                    template += '</br>'
                template += f'{{{{creature faction|{{{{FactionID to name|{faction}}}}}|{value}}}}}'
            return template

    @property
    def gasemitted(self) -> Union[str, None]:
        """The gas emitted by the weapon (typically missile weapon 'pumps')."""
        gas = super().gasemitted
        if gas is not None:
            return f'{{{{ID to name|{gas}}}}}'

    @property
    def harvestedinto(self) -> Union[str, None]:
        """What an item produces when harvested."""
        obj = super().harvestedinto
        if obj is not None:
            return f'{{{{ID to name|{obj}}}}}'

    @property
    def image(self) -> Union[str, None]:
        """The image filename. May be specified in our config."""
        if self.name in IMAGE_OVERRIDES:
            return IMAGE_OVERRIDES[self.name]
        else:
            return super().image

    @property
    def inventory(self) -> Union[str, None]:
        """The inventory of a character.

        Retrieves a list of tuples of strings (name, count, equipped, chance)
        and renders to a template."""
        inv = super().inventory
        if inv is not None:
            template = ''
            for name, count, equipped, chance in inv:
                template += f"{{{{inventory|" \
                            f"{name}|{count}|{equipped}|{chance}}}}}"
            return template

    @property
    def mods(self) -> Union[str, None]:
        """Mods that are attached to the current item.

        Retrieves a list of tuples of strings (modid, tier) and renders to a template.
        """
        mods = super().mods
        if mods is not None:
            return ' </br>'.join(f'{{{{ModID to name|{mod}|{tier}}}}}' for mod, tier in mods)

    @property
    def mutations(self) -> Union[str, None]:
        """The mutations the creature has along with their level."""
        mutations = super().mutations
        if mutations is not None:
            templates = []
            for mutation, level in mutations:
                templates.append(f'{{{{creature mutation|'
                                 f'{{{{MutationID to name|{mutation}}}}}|{level}|'
                                 f'{self.attribute_helper("Ego", "Average")}}}}}')
            return ' </br>'.join(templates)

    @property
    def oneat(self) -> Union[str, None]:
        """Effects granted when the object is eaten."""
        effects = super().oneat
        if effects is not None:
            return ' </br>'.join(f'{{{{OnEat ID to name|{effect}}}}}' for effect in effects)

    @property
    def preservedinto(self) -> Union[str, None]:
        """When preserved, what a preservable item produces."""
        result = super().preservedinto
        if result is not None:
            return f"{{{{ID to name|{result}}}}}"

    @property
    def renderstr(self) -> Union[str, None]:
        """The character used to render this object in ASCII mode."""
        render = super().renderstr
        if render == '}':
            render = '&#125;'
        return render

    @property
    def reputationbonus(self) -> Union[str, None]:
        """The faction rep bonuses granted by this object."""
        reps = super().reputationbonus
        if reps is not None:
            return ' </br>'.join(f'{{{{reputation bonus|{{{{FactionID to name|'
                                 f'{faction}}}}}|{value}}}}}' for faction, value in reps)

    @property
    def skills(self) -> Union[str, None]:
        """A creature's learned skills/powers."""
        skills = super().skills
        if skills is not None:
            return ' </br>'.join(f'{{{{SkillID to name|{skill}}}}}' for skill in skills)

    @property
    def title(self) -> Union[str, None]:
        """The display name of the item, with ampersands escaped."""
        title = super().title
        if title is not None:
            return escape_ampersands(title)

    @property
    def uniquechara(self) -> Union[str, None]:
        """Whether this is a unique character, for wiki purposes."""
        if self.inherits_from('Creature') or self.inherits_from('ActivePlant'):
            if self.name in config['Wiki']['Categories']['Unique Characters']:
                return 'yes'

    @property
    def weaponskill(self) -> Union[str, None]:
        """The skill that is used to wield this object as a weapon."""
        skill = super().weaponskill
        if skill is not None:
            return f'{{{{SkillID to name|{skill}}}}}'
