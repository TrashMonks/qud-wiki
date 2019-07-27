from mwclient import Site

from config import config
from wiki_config import site, wiki_config

TEMPLATE_RE = ''

CREATED_SUMMARY = 'automatically created by Qud Blueprint Explorer'
EDITED_SUMMARY = 'automatically edited by Qud Blueprint Explorer'


class WikiPage:
    def __init__(self, qud_object):
        """Load the Caves of Qud wiki page for the object with the given Qud object."""
        # is this page name overridden?
        if qud_object.name in config['Wiki']['Article overrides']:
            article_name = config['Wiki']['Article overrides'][qud_object.name]
        else:
            article_name = qud_object.displayname
        # capitalize first character
        self.article_name = article_name[0].upper() + article_name[1:]
        self.template_text = qud_object.wikify()
        self.page = site.pages[article_name]

    def exists(self):
        """Whether this page exists already."""
        return self.page.exists

    def upload_template(self):
        """Write the template for our object into the article and save it."""
        if not self.exists():
            # simple case, creating an article
            self.page.save(text=self.template_text, summary=CREATED_SUMMARY)
        else:
            pass

    @property
    def infobox(self):
        """Retrieve the info template from the current page."""

        before = match.string[:match.start()]
        fixed = match.string[match.start():match.end()].replace('\n', '&#10;')
        after = match.string[match.end():]