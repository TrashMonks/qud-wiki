"""Class to assist with managing individual wiki articles on the Caves of Qud wiki."""

import re

from mwclient import Site

from config import config
from wiki_config import site, wiki_config

CREATED_SUMMARY = f'Created by {wiki_config["operator"]} using {config["Wiki name"]} {config["Version"]}'
EDITED_SUMMARY = f'Updated by {wiki_config["operator"]} using {config["Wiki name"]} {config["Version"]}'
# Link to work on or update regex:
# https://regex101.com/r/suH7vR/1
# 1st matching group: everything before template
# 2nd matching group: template
# 3rd matching group: everything after template
TEMPLATE_RE = r"(.*)(^{{(?:Item|Character|Food|Corpse).*^}}$\s\[\[Category:\w+\]\]$)(.*)"


class WikiPage:
    """Represent an individual article."""
    def __init__(self, qud_object):
        """Load the Caves of Qud wiki page for the given Qud object."""
        # is this page name overridden?
        if qud_object.name in config['Wiki']['Article overrides']:
            article_name = config['Wiki']['Article overrides'][qud_object.name]
        else:
            article_name = qud_object.displayname
        # capitalize first character
        self.blacklisted = False  # whether we will refuse all wiki work for this item
        if '[' in article_name or len(article_name) == 0:
            # mostly base categories that aren't listed as such, or objects that aren't meant
            # to be rendered (no display name)
            self.blacklisted = True
        else:
            self.article_name = article_name[0].upper() + article_name[1:]
            self.template_text = qud_object.wiki_template()
            self.page = site.pages[article_name]

    def upload_template(self):
        """Write the template for our object into the article and save it."""
        if self.page.exists:
            # complex case: have to get text indices corresponding to beginning of pre-template,
            # and end of post-template
            match = re.match(TEMPLATE_RE, self.page.text(), re.MULTILINE | re.DOTALL)
            start = match.start(2)
            end = match.end(2)
            pre_template_text = self.page.text()[:start]
            post_template_text = self.page.text()[end:]
            new_text = pre_template_text + self.template_text + post_template_text
            self.page.save(text=new_text, summary=EDITED_SUMMARY)
        else:
            # simple case, creating an article
            self.page.save(text=self.template_text, summary=CREATED_SUMMARY)
