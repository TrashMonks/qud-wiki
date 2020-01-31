from wiki_config import site


def get_all_pages():
    """Helper function to return a list of all pages on the wiki."""
    return [page.page_title for page in site.allpages()]
