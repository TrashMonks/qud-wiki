import re

from hagadias.gameroot import GameRoot

irregular_verbs = {
            "are": "is",
            "were": "was",
            "have": "has",
            "'re": "'s",
            "don't": "doesn't",
            "'ve": "'s"
            }
irregular_nouns = {
        "man": "men",
        "woman": "women"
    }

re_exp = r"=(?P<type>\w+)(?(1)[\.:](?P<word>\w+)?:?(?P<afterpronoun>afterpronoun)?)="

class GenderParser():
    def __init__(self):
        gameroot = self.open_gameroot()
        self.genders = gameroot.get_genders()
        self.pronouns = gameroot.get_pronouns()

    def open_gameroot(self):
        """Attempt to load a GameRoot from the saved root game directory."""
        try:
            with open('last_xml_location') as f:
                dir_name = f.read()
        except FileNotFoundError:
            raise
        return GameRoot(dir_name)

    def parse(self, description: str, gender: str, pronoun=None):
        b_make_plural = False
        return re.sub(re_exp, lambda m: self.conjugate(m.group('type'),
                                                       m.group('word'),
                                                       m.group('afterpronoun')), description)
    
    def conjugate(self, wordtype, word, afterpronoun, description):
            b_afterpronoun = afterpronoun is not None

            if wordtype == "article":
                return "a "
            elif wordtype == "pluralize":
                b_make_plural = True
                return ""
            else:
                return f"={wordtype}="

            if word is not None:
                b_capitalized = word[0].isupper()
                if wordtype == "pronouns":
                    cap_word = word.capitalize() 
                    if cap_word == "indicativeProximal":
                        if self.is_plural(gender, pronoun):
                            returnstring = "this"
                        else:
                            returnstring = "these"
                    else:
                        returnstring = self.look_up_pronoun(cap_word, gender, pronoun)
                elif wordtype == "verb":
                    if b_afterpronoun and self.is_plural(gender, pronoun):
                        returnstring = word
                    else:
                        returnstring == self.singular_verb(word)
                if b_make_plural:
                    returnstring = self.pluralize(returnstring)
                    b_make_plural = False
                if b_capitalized:
                    return returnstring.capitalize()
                else:
                    return returnstring

    def look_up_pronoun(self, conjugation: str, gendertype: str, pronountype=None):
        pronoun = None
        if pronountype is not None:
            pronoun = self.pronouns[pronountype][conjugation]
        if pronoun is None:
            pronoun = self.genders[gendertype][conjugation]
        return pronoun

    def singular_verb(self, verb: str):
        if verb in irregular_verbs:
            return irregular_verbs[verb]
        else:
            return f"{verb}s"

    def pluralize(self, noun):
        if noun in irregular_nouns:
            return irregular_nouns[noun]
        endletter = noun[-1]
        endtwoletters = noun[-2]
        if endletter == "s":
            return noun
        if endletter == "y":
            return f"{noun[:-1]}ies"
        if endletter in {"z", "x"} or endtwoletters in {"ch", "sh"}:
            return f"{noun}es"
        return f"{noun}s"

    def is_plural(self, gender: str,pronoun: str):
        if pronoun is not None:
            return self.pronouns[pronoun]['pseudoplural']
        return False  #TODO: check gender look for plural + psuedoplurals
