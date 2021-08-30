import os
import re
from typing import Union

from qbe.config import config
from hagadias.helpers import strip_oldstyle_qud_colors, strip_newstyle_qud_colors
from hagadias.qudobject_props import QudObjectProps

from qbe.helpers import displayname_to_wiki

IMAGE_OVERRIDES = config['Templates']['Image overrides']


def escape_ampersands(text: str):
    """Convert & to &amp; for use in wiki template."""
    return re.sub('&', '&amp;', text)


class QudObjectWiki(QudObjectProps):
    """Represents a Caves of Qud game object to the wiki interface.

    Inherits from QudObjectProps which provides all the derived information about the object.

    Passes requests to its QudObjectProps superclass and translates the results for templates,
    with HTML escaped characters, etc."""

    def wiki_template(self, gamever) -> str:
        """Return the fully wikified template representing this object and add a category.

        gamever is a string giving the version of Caves of Qud."""
        fields = config['Templates']['Fields']
        flavor = self.wiki_template_type()
        before_title = '{{Qud text|'
        after_title = '}}'
        template = '{{' + f'{flavor}\n'
        template += "| title = " + before_title + self.title + after_title + "\n"
        for field in fields:
            if field == 'title':
                continue
            if flavor == 'Corpse':
                if field == 'hunger':
                    continue
                if field == 'image':
                    if not (self.is_specified('part_Render_Tile')
                            or self.is_specified('part_Render_TileColor')
                            or self.is_specified('part_Render_ColorString')
                            or self.is_specified('part_Render_DetailColor')):
                        continue  # uses default corpse tile/colors, so don't add image field
            attrib = getattr(self, field)
            if attrib is not None:
                # do some final cleanup before sending to template
                if field == 'renderstr':
                    # } character messes with mediawiki template rendering
                    attrib = attrib.replace('}', '&#125;')
                # replace Booleans with wiki-compatible 'yes' and 'no'
                if isinstance(attrib, bool):
                    attrib = 'yes' if attrib else 'no'
                elif isinstance(attrib, list):
                    attrib = ', '.join(attrib)
                template += f'| {field} = {attrib}\n'
        category = self.wiki_category()
        if category:
            template += f'| categories = {category}\n'
        if gamever != 'unknown':
            template += f'| gameversion = {gamever}\n'
        template += '}}\n'
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
        if (self.part_Physics_Takeable == "false" or self.part_Physics_Takeable == "False") and \
                self.part_Gas is None and not self.inherits_from('MeleeWeapon') and \
                not self.is_specified('part_MeleeWeapon') and \
                not self.inherits_from('MissileWeapon'):
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

    def wiki_namespace(self) -> str:
        ns = None
        for config_ns, names in config['Wiki']['Article Namespaces'].items():
            for name in names:
                if self.inherits_from(name):
                    ns = config_ns
        return ns

    def is_wiki_eligible(self) -> bool:
        """Return whether this object should be included in the wiki."""
        if self.name == 'Argyve\'s Data Disk Encoded':
            return True  # special case because of '['
        if self.name == 'DefaultFist':
            return True  # special case because this is the player's fist
        if self.is_specified('tag_BaseObject'):
            return False
        if self.displayname == '' or '[' in self.displayname:
            return False
        eligible = True  # equal to initial +Object in config.yml
        for entry in config['Wiki']['Article eligibility categories']:
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
    def commerce(self) -> Union[float, int, None]:
        """Remove trailing decimal points on values."""
        value = super().commerce
        if value is not None:
            if self.part_Physics_Takeable is not None and self.part_Physics_Takeable == 'false':
                if value == 0.01:
                    # ignore for non-takeable objects that inherit 0.01 from PhysicalObject
                    return None
            return value if 0 < value < 1 else int(value)

    @property
    def cookeffect(self) -> Union[str, None]:
        """The possible cooking effects of an item."""
        effect = super().cookeffect
        if effect is not None:
            return ','.join(f'{val}' for val in effect)

    @property
    def desc(self) -> Union[str, None]:
        """The short description of the object, with color codes included (ampersands escaped)."""
        text = super().desc
        if text is not None:
            text = displayname_to_wiki(text)
        return text

    @property
    def displayname(self) -> Union[str, None]:
        """The display name of the object, with color codes removed. Used in QBE UI"""
        if self.name in config['Wiki']['Displayname overrides']:
            dname = config['Wiki']['Displayname overrides'][self.name]
            dname = strip_oldstyle_qud_colors(dname)
            dname = strip_newstyle_qud_colors(dname)
        else:
            dname = super().displayname
        return dname

    @property
    def dynamictable(self) -> Union[str, None]:
        """What dynamic tables the object is a member of."""
        tables = super().dynamictable
        if tables is not None:
            return ' </br>'.join(f'{{{{Dynamic object|{table}|{self.name}}}}}' for table in tables)

    @property
    def eatdesc(self) -> Union[str, None]:
        """The text when you eat this item."""
        text = super().eatdesc
        if text is not None:
            text = displayname_to_wiki(text)
        return text

    @property
    def extra(self) -> Union[str, None]:
        """Any other features that do not have an associated variable."""
        fields = []
        if self.featureweightinfo == 'no':  # put weight in extrainfo if it's not featured
            fields.append(('weight', self.weight))
        extrafields = config['Templates']['ExtraFields']
        for field in extrafields:
            attrib = getattr(self, field)
            if attrib is not None:
                # convert Booleans to wiki-compatible 'yes' and 'no'
                if isinstance(attrib, bool):
                    attrib = 'yes' if attrib else 'no'
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
    def featureweightinfo(self) -> Union[str, None]:
        """'no' if the weight should be shown as extra data. 'yes' if the weight should be
        featured near the top of the wiki infobox. Weight is featured only for takeable objects
        (i.e. items). For other things it plays a much less prominent role only for explosion
        calculations, getting stuck in webs, etc. """
        w = self.weight
        if w is not None:
            if self.part_Physics_Takeable is None or self.part_Physics_Takeable == 'true':
                return 'yes'
            else:
                return 'no'

    @property
    def gasemitted(self) -> Union[str, None]:
        """The gas emitted by the weapon (typically missile weapon 'pumps')."""
        gas = super().gasemitted
        if gas is not None:
            return f'{{{{ID to name|{gas}}}}}'

    @property
    def gif(self) -> Union[str, None]:
        """The gif image filename. On the wiki, this is used only by single-tile images with a
        GIF animation. For multi-tile images, this field will be ignored in favor of
        overrideimages."""
        if self.has_gif_tile():
            path = self.image
            if path is not None and path != 'none':
                return os.path.splitext(path)[0] + ' animated.gif'

    @property
    def image(self) -> Union[str, None]:
        """The image filename for the object's primary image. May be specified in our config.
        If the object has additional alternate images, their filenames will be derived from
        this one."""
        if self.name in IMAGE_OVERRIDES:
            return IMAGE_OVERRIDES[self.name]
        elif self.has_tile():
            name = self.displayname
            name = re.sub(r"[^a-zA-Z\d ]", '', name)
            name = name.casefold() + '.png'
            return name
        else:
            return 'none'

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
    def liquidburst(self) -> Union[str, None]:
        liquid = super().liquidburst
        if liquid is not None:
            return '{{ID to name|' + liquid + '}}'

    @property
    def mods(self) -> Union[str, None]:
        """Mods that are attached to the current item.

        Retrieves a list of tuples of strings (modid, tier) and renders to a template.
        """
        mods = super().mods
        if mods is not None:
            return ' </br>'.join(f'{{{{ModID to name|{mod}|{tier}}}}}' for mod, tier in mods)

    @property
    def movespeedbonus(self) -> Union[str, None]:
        """The movespeed bonus of an item, prefixed with a + if positive."""
        bonus = super().movespeedbonus
        if bonus is not None:
            return '+' + str(bonus) if bonus > 0 else str(bonus)

    @property
    def mutations(self) -> Union[str, None]:
        """The mutations the creature has along with their level."""
        mutations = super().mutations
        if mutations is not None:
            templates = []
            ego = self.attribute_helper_avg("Ego")
            for mutation, level in mutations:
                mutation_entry = \
                    f'{{{{creature mutation|{{{{MutationID to name|{mutation}}}}}|{level}'
                if ego is not None:
                    mutation_entry += f'|{ego}'
                mutation_entry += '}}'
                templates.append(mutation_entry)
            return ' </br>'.join(templates)

    @property
    def oneat(self) -> Union[str, None]:
        """Effects granted when the object is eaten."""
        effects = super().oneat
        if effects is not None:
            return ' </br>'.join(f'{{{{OnEat ID to name|{effect}}}}}' for effect in effects)

    @property
    def overrideimages(self) -> Union[str, None]:
        """A full list of images for this object, expressed as individual {{altimage}} templates
        for each image (and, if applicable, for that image's corresponding GIF). This property is
        returned for any object that has more than one tile variant. On the wiki, this property
        is used to replace the single image that is usually shown alone for an object with an
        image carousel that can rotate through all of the images for this object. """
        if self.number_of_tiles() > 1:
            metadata = self.tiles_and_metadata()[1]
            val = '{{altimage start}}'
            for meta in metadata:
                val += '{{altimage'
                val += f' | {meta.filename}'
                if meta.is_animated():
                    val += f' | gif = {meta.gif_filename}'
                if meta.type is not None:
                    val += f' | type = {meta.type}'
                val += '}}'
            val += '{{altimage end}}'
            return val

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
            return ''.join(f'{{{{reputation bonus|{{{{FactionID to name|'
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
        if self.name in config['Wiki']['Displayname overrides']:
            title = config['Wiki']['Displayname overrides'][self.name]
        else:
            title = super().title
        if title is not None:
            title = displayname_to_wiki(title)
            return escape_ampersands(title)

    @property
    def unknownname(self) -> Union[str, None]:
        """The name of the object when unidentified, such as 'weird artifact'."""
        name = super().unknownname
        if name is not None:
            return displayname_to_wiki(name)

    @property
    def unknownaltname(self) -> Union[str, None]:
        """The name of the object when partially identified, such as 'backpack'."""
        altname = super().unknownaltname
        if altname is not None:
            return displayname_to_wiki(altname)

    @property
    def uniquechara(self) -> Union[str, None]:
        """Whether this is a unique character, for wiki purposes."""
        if self.inherits_from('Creature') or self.inherits_from('ActivePlant'):
            if self.name in config['Wiki']['Categories']['Unique Characters']:
                return 'yes'

    @property
    def unidentifiedinfo(self) -> Union[str, None]:
        """Details about this object when it is unidentified."""
        tile = self.unknowntile
        name = self.unknownname
        altname = self.unknownaltname
        if tile or name or altname:
            result = '{{Unidentified info'
            result += f' | tile = {tile}' if tile is not None else ''
            result += f' | name = {name}' if name is not None else ''
            result += f' | altname = {altname}' if altname is not None else ''
            result += ' }}'
            return result

    @property
    def weaponskill(self) -> Union[str, None]:
        """The skill that is used to wield this object as a weapon."""
        skill = super().weaponskill
        if skill is not None:
            return f'{{{{SkillID to name|{skill}}}}}'
