# Script outside of server
import django
import os
 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bang.settings")
django.setup()

from background_task.models import Task
import numpy as np
import subprocess

queue_lines = list(np.unique(['base' if x is None else x for x in list(Task.objects.all().values_list('queue', flat=True))]))

print(queue_lines)
for queue in queue_lines:
    output = subprocess.run('start python run_tasks.py {}'.format(str(queue)), shell=True)