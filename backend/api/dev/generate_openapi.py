import yaml

from src.app import app

print(yaml.dump(app.openapi(), allow_unicode=True, sort_keys=False))
