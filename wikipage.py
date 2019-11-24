"""Class to assist with managing individual wiki articles on the Caves of Qud wiki."""

import re

from config import config
from wiki_config import site, wiki_config

# Link to work on or update regex:
# https://regex101.com/r/suH7vR/2
# 1st matching group: everything before template
# 2th matching group: Template
# 3rd matching group: everything after template.
# First and last matching groups are added later in init
INTRO_STR = '<!-- START QBE: Autogenerated section - please leave this marker. ' \
                       'See the [[QBE]] page for more information. -->'
FINAL_STR = '<!-- END QBE -->'
TEMPLATE_RE = r"(?:<!--.+?-->)?\n*(?:{{As Of Patch\|[0-9.]+}})\n*({{(?:Item|Character|Food|Corpse).*^}})\n*(?:\[\[Category:.+?\]\])?\n?(?:<!--.+? -->)??"


class WikiPage:
    """Represent an individual article."""

    def __init__(self, qud_object, gamever):
        """Load the Caves of Qud wiki page for the given Qud object.

        Parameters:
            qud_object: the QudObject to represent
            gamever: a string giving the patch version of CoQ
            """
        self.CREATED_SUMMARY = f'Created by {wiki_config["operator"]}' \
                               f' to game version {gamever}' \
                               f' using {config["Wikified name"]} {config["Version"]}'
        self.EDITED_SUMMARY = f'Updated by {wiki_config["operator"]}' \
                              f' to game version {gamever}' \
                              f' using {config["Wikified name"]} {config["Version"]}'
        self.as_of_patch = f'{{{{As Of Patch|{gamever}}}}}'
        self.intro_string = INTRO_STR + '\n' + self.as_of_patch + '\n'
        self.final_string = FINAL_STR
        # Use base TEMPLATE_RE but surrounding text around template is also captured
        self.template_re = '(.*?)' + TEMPLATE_RE + '(.*?)'
        # is this page name overridden?
        if qud_object.name in config['Wiki']['Article overrides']:
            article_name = config['Wiki']['Article overrides'][qud_object.name]
        else:
            article_name = qud_object.displayname
        # capitalize first character
        if len(article_name) > 0:
            self.article_name = article_name[0].upper() + article_name[1:]
        else:
            self.article_name = article_name
        self.template_text = qud_object.wiki_template(gamever)
        self.page = site.pages[article_name]

    def upload_template(self):
        """Write the template for our object into the article and save it."""
        if self.page.exists:
            # complex case: have to get indices corresponding to beginning and end of the
            # existing template
            match = re.match(self.template_re, self.page.text(), re.MULTILINE | re.DOTALL)
            if match is None:
                raise ValueError('Article exists, but existing format not recognized. '
                                 'Try a manual edit first.')
            if match.group(1) is not None:
                start = match.end(1)
            else:
                start = match.start(2)
            if match.group(3) is not None:
                end = match.start(3)
            else:
                end = match.end(2)
            pre_template_text = self.page.text()[:start] + self.intro_string
            post_template_text = self.final_string + self.page.text()[end:]
            new_text = pre_template_text + self.template_text + post_template_text
            result = self.page.save(text=new_text, summary=self.EDITED_SUMMARY)
        else:
            # simple case: creating an article
            result = self.page.save(text=self.template_text, summary=self.CREATED_SUMMARY)
        print(result)
        return result['result']
