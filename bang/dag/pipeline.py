from background_task import background

from dag.models import DAG
from dag.utils import DAGItemLogger

from importlib import import_module
import os
from queue import Queue
import warnings


class DAGQueue(object):
	def __init__(self):
		self.q = Queue()

	def build_dag_queue(self, task):
		self.q.put(task)
		if task.has_children():
			for child in task.children.all():
				self.build_dag_queue(child)
		return self.q  

	def get(self):
		if self.q.empty():
			warnings.warn('Queue is empty')
			return None
		else:
			return self.q.get()

	def size(self):
		return self.q.qsize()

	def empty(self):
		return self.q.empty()

	def run(self):
		while not self.q.empty():
			dag_item = self.q.get()
	
			dep_dict = {}
			for dep in dag_item.dependencies.all():
				if dep.sub_module is None:
					dep_dict.update({dep.package.common_short_hand or dep.package.import_name : import_module(dep.package.import_name)})
				else:
					dep_dict.update({dep.get_end_sub_mod() : import_module('{}.{}'.format(dep.package.import_name, dep.sub_module))})
					
			### Create logging
			dil = DAGItemLogger(dag_item_id=dag_item.pk)
			dep_dict.update({'dil' : dil})
			
			### Internal Script versus Path
			if dag_item.item_type == 'SCRIPT':  ## Internal Script
				exec(dag_item.job_script, dep_dict)
			else:								## Path to Script
				current_path = os.getcwd()
				try:
					os.chdir(os.path.dirname(dag_item.script_full_path))
					exec(open(os.path.basename(dag_item.script_full_path)).read(), dep_dict)
					os.chdir(current_path)
				except Exception as e:
					print(str(e))
					os.chdir(current_path)
				dil.finish()
	

@background(schedule=1)
def base_dag_run(dag_pk):
	dag_obj = DAG.objects.get(pk=dag_pk)
	dq = DAGQueue()
	dq.build_dag_queue(dag_obj.get_initial_task())
	dq.run()