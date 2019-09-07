import yaml

from mwclient import Site

with open('wiki.yml') as f:
    wiki_config = yaml.safe_load(f)

site = Site(wiki_config['base'], path=wiki_config['path'])
site.login(wiki_config['username'], wiki_config['password'])
bee = site.pages['portable beehive']
