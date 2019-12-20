import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bang.settings")
django.setup()


from appadmin.utils import update_dependencies

update_dependencies()