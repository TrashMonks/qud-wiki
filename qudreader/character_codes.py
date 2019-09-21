"""
Load Caves of Qud game data from gamefiles.
We're mostly interested in the two-character codes that map to specific implants and mutations.
"""

from xml.etree import ElementTree as et

# These files need to be copied in from, e.g.,
# SteamLibrary\SteamApps\common\Caves of Qud\CoQ_Data\StreamingAssets\Base
GENO = et.parse('xml/Genotypes.xml').getroot()
SKILLS = et.parse('xml/Skills.xml').getroot()
SUBTYPES = et.parse('xml/Subtypes.xml').getroot()
MUTATIONS = et.parse('xml/Mutations.xml').getroot()

STAT_NAMES = ('Strength', 'Agility', 'Toughness', 'Intelligence', 'Willpower', 'Ego')
# these are not available from XML:
IMPLANT_CODES = {'00': 'none',
                 '01': 'dermal insulation',
                 '04': 'optical bioscanner',
                 '05': 'optical technoscanner',
                 '06': 'night vision',
                 '07': 'hyper-elastic ankle tendons',
                 '08': 'parabolic muscular subroutine',
                 '09': 'translucent skin',
                 '11': 'stabilizer arm locks',
                 '12': 'rapid release finger flexors',
                 '13': 'carbide hand bones',
                 '14': 'pentaceps',
                 '15': 'inflatable axons',
                 # subtypes A-D, E-H, I-L
                 '16': ('nocturnal apex', 'cherubic visage', 'air current microsensor'),
                 }
# these are not available from XML:
MOD_BONUSES = {'BE': [2, 0, 0, 0, 0, 0],  # Double-muscled
               'BK': [0, 0, -1, 0, 0, 0],  # Heightened Quickness
               'B2': [-1, 2, 0, 0, 0, 0],  # Triple-jointed
               'B4': [0, 0, 2, 0, 0, 0],  # Two-hearted
               'CD': [0, 0, 0, 0, 0, -1],  # Beak (D)
               '00': [0, 0, 1, 0, 0, 0],  # True Kin but no implant
               }


def read_gamedata() -> dict:
    """
    Read character code snippets and assorted data from Qud XML files. Implant codes not in XML.
    """
    # Read genotypes: currently, only two (mutated human and true kin)
    genotype_codes = {}
    for genotype in GENO:
        genotype_codes[genotype.attrib['Code'].upper()] = genotype.attrib['Name']

    # Read skill class names and real names
    # These are not returned, but used to parse the powers of subtypes, below.
    skill_names = {}
    for skill_cat in SKILLS:
        skill_names[skill_cat.attrib['Class']] = '(' + skill_cat.attrib['Name'] + ")"
        for power in skill_cat:
            skill_names[power.attrib['Class']] = power.attrib['Name']

    class_bonuses = {}
    class_skills = {}
    caste_codes = {}

    # read True Kin Castes
    arcologies = SUBTYPES[0]
    for category in arcologies:
        for caste in category:
            caste_codes[caste.attrib['Code'].upper()] = caste.attrib['Name']
            stat_bonuses = [0, 0, 0, 0, 0, 0]
            for element in caste:
                if element.tag == 'stat' and (element.attrib['Name'] in STAT_NAMES):
                    bonus = int(element.attrib['Bonus'])
                    stat_bonuses[STAT_NAMES.index(element.attrib['Name'])] = bonus
            class_bonuses[caste.attrib['Name']] = stat_bonuses
            skills_raw = caste.find('skills')
            skills = []
            for skill in skills_raw:
                skills.append(skill_names[skill.attrib['Name']])
            class_skills[caste.attrib['Name']] = skills

    # read mutant Callings
    calling_codes = {}
    for calling in SUBTYPES[1]:
        calling_codes[calling.attrib['Code'].upper()] = calling.attrib['Name']
        stat_bonuses = [0, 0, 0, 0, 0, 0]
        for element in calling:
            if element.tag == 'stat' and (element.attrib['Name'] in STAT_NAMES):
                bonus = int(element.attrib['Bonus'])
                stat_bonuses[STAT_NAMES.index(element.attrib['Name'])] = bonus
        class_bonuses[calling.attrib['Name']] = stat_bonuses
        skills_raw = calling.find('skills')
        skills = []
        for skill in skills_raw:
            skills.append(skill_names[skill.attrib['Name']])
        class_skills[calling.attrib['Name']] = skills

    # read mutations
    mod_codes = {}
    for category in MUTATIONS:
        for mutation in category:
            mod_codes[mutation.attrib['Code'].upper()] = mutation.attrib['Name']
            # mark defects with '(D)' as in game
            if category.attrib['Name'] in ('PhysicalDefects', 'MentalDefects'):
                mod_codes[mutation.attrib['Code'].upper()] += ' (D)'
    # add implants to mutations
    mod_codes.update(IMPLANT_CODES)  # not in XML

    # some manual fixups
    mod_codes.pop('UU')
    for i in range(1, 6):
        mod_codes[f'U{i}'] = f'Unstable Genome ({i})'

    return {'genotype_codes': genotype_codes,
            'caste_codes': caste_codes,
            'calling_codes': calling_codes,
            'mod_codes': mod_codes,
            'class_bonuses': class_bonuses,
            'class_skills': class_skills,
            'mod_bonuses': MOD_BONUSES,
            }
