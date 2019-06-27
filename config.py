import yaml

CONFIG_FILE = "config.yml"

with open(CONFIG_FILE) as f:
    config = yaml.safe_load(f)
