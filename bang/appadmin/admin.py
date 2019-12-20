from django.contrib import admin
from django.apps import apps

# Shortcut to config all models in the customers models framework
app = apps.get_app_config('appadmin')

for model_name, model in app.models.items():
	admin.site.register(model)
