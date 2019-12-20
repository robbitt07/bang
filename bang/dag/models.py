from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse

from appadmin.models import ProcessPackages
from background_task import background
from background_task.models import Task
from background_task.models_completed import CompletedTask

from hashlib import sha1
import os
import psutil
import subprocess
import time


def dag_asset_name(instance, filename):
	file_str = str('.'.join(filename.split('.')[:-1]))
	extension = str(filename.split('.')[-1])
	return os.path.join('dag_assest', instance.dag_item.job_name,
							'{}.{}'.format(file_str, extension))


class DAG(models.Model):
	dag_name = models.CharField(max_length=50)
	dag_hash = models.CharField(max_length=40, db_index=True, blank=True)

	### Scheduling
	initial_run_time = models.DateTimeField()
	repeat = models.BigIntegerField(default=0)

	### Meta information
	job_owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='dags')
	active_status = models.BooleanField(default=True)

	### Task related information
	run_in_progress = models.BooleanField(default=False)
	run_at = models.DateTimeField(blank=True, null=True)
	has_error = models.BooleanField(default=False)
	last_error = models.TextField(blank=True)

	created_on = models.DateTimeField(auto_now_add=True)
	last_update = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'dag_dag'
		ordering = ['run_at']
		verbose_name = 'DAG'
		verbose_name_plural = 'DAGs'

	def has_valid_structure(self):
		has_initial = self.dag_items.filter(parent__isnull=True).count() == 1
		return has_initial

	def get_initial_task(self):
		if self.has_valid_structure():
			return self.dag_items.filter(parent__isnull=True).first()
		else:
			return DAGItem.objects.none()

	def get_absolute_url(self):
		return reverse('dag:dag_detail', args=(self.pk,))

	def get_update_url(self):
		return reverse('dag:dag_update', args=(self.pk,))		
	
	def get_delete_url(self):
		return reverse('dag:dag_delete', args=(self.pk,)) 

	def get_initiate_url(self):
		return reverse('dag:dag_initiate_process', args=(self.pk,))
			
	def get_open_tasks(self):
		return Task.objects.filter(verbose_name=self.dag_hash)

	def get_task(self):
		try:
			task_obj = Task.objects.get(verbose_name=self.dag_hash)
			return task_obj
		except:
			return None
			
	def next_run_time(self):
		try:
			task_obj = Task.objects.get(verbose_name=self.dag_hash)
			return task_obj.run_at
		except:
			return None

	def get_complete_tasks(self):
		return CompletedTask.objects.filter(verbose_name=self.dag_hash).order_by('-locked_at')[0:15]

	def __str__(self):
		return str(self.dag_name)

		
### Creates Background Task Hash after DAG creation
@receiver(pre_save, sender=DAG)
def create_dag_hash_pre(sender, instance, **kwargs):
	if instance.dag_hash is None or instance.dag_hash == '':
		s = "{}{}".format(instance.dag_name, time.time())
		dag_hash = sha1(s.encode('utf-8')).hexdigest()
		instance.dag_hash = dag_hash


class DAGItem(models.Model):
	ITEM_TYPE_OPTION = (
		('SCRIPT', 'Script Internal'),
		('PATH', 'Path to Script'),
	)
	dag = models.ForeignKey(DAG, on_delete=models.CASCADE, null=True, blank=True, related_name='dag_items')
	parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
	job_name = models.CharField(max_length=250, unique=True)
	item_type = models.CharField(max_length=50, choices=ITEM_TYPE_OPTION, default='SCRIPT', null=True, blank=True)

	### DAG Item Script Text
	job_script = models.TextField(blank=True, null=True)
	job_key_arguments = models.TextField(blank=True, null=True)

	### DAG Item Script Path
	script_full_path = models.CharField(max_length=1000, blank=True, null=True)

	### Meta information
	job_owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='dag_items')
	active_status = models.BooleanField(default=True)

	### Task related information
	run_in_progress = models.BooleanField(default=False)
	has_error = models.BooleanField(default=False)
	last_error = models.TextField(blank=True)

	created_on = models.DateTimeField(auto_now_add=True)
	last_update = models.DateTimeField(auto_now=True)
	
	class Meta:
		db_table = 'dag_item'
		verbose_name = 'DAG Item'
		verbose_name_plural = 'DAG Items'    

	def get_script(self):
		if self.item_type == 'SCRIPT':
			return self.job_script
		else:
			return open(self.script_full_path).read()

	def get_absolute_url(self):
		return reverse('dag:dagitem_detail', args=(self.pk,))

	def get_update_url(self):
		if self.item_type == 'SCRIPT':
			return reverse('dag:dagitem_script_update', args=(self.pk,))
		else:
			return reverse('dag:dagitem_path_update', args=(self.pk,))
	
	def get_delete_url(self):
		return reverse('dag:dagitem_delete', args=(self.pk,)) 

	def get_dependency_url(self):
		return reverse('dag:dagitem_dependency_list', args=(self.pk,)) 		

	def has_parent(self):
		return bool(self.parent)

	def has_children(self):
		return bool(self.children.all().count())

	def print_parent(self):
		try:
			return self.parent.job_name
		except:
			return None

	def __str__(self):
		return '{} - {} ({})'.format(str(self.dag), str(self.job_name), str(self.print_parent()))


class DagItemHistory(models.Model):
	dag_item = models.ForeignKey(DAGItem, on_delete=models.CASCADE, related_name='version_history')
	version_number = models.IntegerField()
	script_text = models.TextField(blank=True, null=True)
	script_diff_text = models.TextField(blank=True, null=True)
	script_diff_list = models.TextField(blank=True, null=True)
	
	version_datetime = models.DateTimeField(auto_now_add=True)
	user_edit = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='dag_item_version_history')

	class Meta:
		db_table = 'dag_item_version_history'
		ordering = ['dag_item', '-version_number']
		verbose_name = 'DAG Item Version History'
		verbose_name_plural = 'DAG Items Version History'    

	@property
	def get_script_diff_list(self):
		try:
			return eval(self.script_diff_list)
		except:
			return []
		
	def get_absolute_url(self):
		return reverse('dag:dagitem_version_history', args=(self.pk,))
	
	def __str__(self):
		return '{} - {}'.format(str(self.dag_item), str(self.script_diff_text))


class DAGDependency(models.Model):
	dag_item = models.ForeignKey(DAGItem, on_delete=models.CASCADE, related_name='dependencies')
	package = models.ForeignKey(ProcessPackages, on_delete=models.SET_NULL, blank=True, null=True, related_name='dag_items')
	sub_module = models.CharField(max_length=50, null=True, blank=True)

	class Meta:
		ordering = [Lower('package__package_name'),]
		db_table = 'dag_item_dependency'
		verbose_name = 'DAG Dependency'
		verbose_name_plural = 'DAG Dependencies'

	def get_absolute_url(self):
		return reverse('dag:dagitem_detail', args=(self.dag_item_id,))

	def get_update_url(self):
		return reverse('dag:dagitem_dependency_update', args=(self.pk,))
	
	def get_delete_url(self):
		return reverse('dag:dagitem_dependency_delete', args=(self.pk,)) 

	def get_end_sub_mod(self):
		return self.sub_module.split('.')[-1]
		
	def __str__(self):
		return '{} | {}'.format(str(self.dag_item), str(self.package))


class DAGAsset(models.Model):
	dag_item = models.ForeignKey(DAGItem, on_delete=models.CASCADE, related_name='assets')
	dag_asset = models.FileField(null = True, blank = True, upload_to = dag_asset_name)
	notes = models.CharField(max_length=1000, null=True, blank=True)

	class Meta:
		unique_together = ('dag_item', 'dag_asset',)
		db_table = 'dag_item_asset'
		verbose_name = 'DAG Asset'
		verbose_name_plural = 'DAG Assets'

	def __str__(self):
		return '{} | {}'.format(str(self.dag_item), str(self.dag_asset))



class DAGItemLogging(models.Model):
	dag_item = models.ForeignKey(DAGItem, on_delete=models.CASCADE, related_name='logs')
	run_hash = models.CharField(max_length=40, db_index=True, blank=True)

	start_time = models.DateTimeField(null=True, blank=True)
	end_time = models.DateTimeField(null=True, blank=True)

	created_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_on']
		db_table = 'dag_item_logging'
		verbose_name = 'DAG Item Logging'
		verbose_name_plural = 'DAG Items Logging'

	def run_time(self):
		try:
			return (self.end_time - self.start_time).seconds
		except:
			return 0
			
	def __str__(self):
		return str(self.dag_item)


class LoggingEvent(models.Model):
	dag_item_logging = models.ForeignKey(DAGItemLogging, on_delete=models.CASCADE, related_name='events')
	
	log_metric = models.CharField(max_length=250)
	log_value = models.DecimalField(max_digits=20, decimal_places=2)

	created_on = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['dag_item_logging', 'created_on']
		db_table = 'dag_item_logging_event'
		verbose_name = 'DAG Item Logging Event'
		verbose_name_plural = 'DAG Items Logging Events'

	def __str__(self):
		return str(self.dag_item_logging)	


class DAGProcess(models.Model):
	dag = models.OneToOneField(DAG, on_delete=models.CASCADE, related_name='current_process')
	pid = models.IntegerField(null=True, blank=True)
	start_time = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = [Lower('dag__dag_name'),]
		db_table = 'dag_process'
		verbose_name = 'DAG Process'
		verbose_name_plural = 'DAG Process'

	@property
	def is_active(self):
		try:
			psutil.Process(self.pid)
			return True
		except:
			return False

	@property
	def dag_cpu_percent(self):
		try:
			return sum([child.cpu_percent() for child in psutil.Process(self.pid).children(recursive=True)])
		except:
			return 0
	
	@property
	def dag_memerory_percent(self):
		try:
			return sum([child.memory_percent() for child in psutil.Process(self.pid).children(recursive=True)])
		except:
			return 0

	@property
	def dag_number_children(self):
		try:
			return len([child for child in psutil.Process(self.pid).children(recursive=True)])
		except:
			return 0

	def start_process(self):
		subprocess.run('start python run_tasks.py {}'.format(str(self.dag.dag_name)), shell=True)
		try:
			dag_task = self.dag.get_task()
			dag_task.locked_by = None
			dag_task.locked_at = None
			dag_task.last_error  = None
			dag_task.save()
		except:
			pass

	def end_process(self):
		os.system("taskkill /f /t /pid {}".format(self.pid))
		try:
			dag_task = self.dag.get_task()
			dag_task.locked_by = None
			dag_task.locked_at = None
			dag_task.save()
		except:
			pass

	def get_absolute_url(self):
		return reverse('dag:dag_process_detail', args=(self.pk,))

	def get_dag_absolute_url(self):
		return reverse('dag:dag_detail', args=(self.dag.pk,))

	def get_start_url(self):
		return reverse('dag:dag_start_process', args=(self.pk,))

	def get_end_url(self):
		return reverse('dag:dag_end_process', args=(self.pk,))

	def __str__(self):
		return '{} {}'.format(str(self.dag), str(self.pid))


class DAGProcessStatus(models.Model):
	dag_process = models.ForeignKey(DAGProcess, on_delete=models.CASCADE)
	pid_running = models.IntegerField(null=True, blank=True)
	memory_consumption = models.DecimalField(max_digits=10, decimal_places=4)
	cpu_consumption = models.DecimalField(max_digits=10, decimal_places=4)
	child_processes = models.IntegerField(null=True, blank=True)

	observed_time = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-observed_time',]
		db_table = 'dag_process_status'
		verbose_name = 'DAG Process Status'
		verbose_name_plural = 'DAG Process Status'

	def __str__(self):
		return '{} {}'.format(str(self.dag_process), str(self.observed_time))


@background(schedule=1, queue='testing')
def dag_process_tracking(dag_process_id):
	dag_process = DAGProcess.objects.get(pk=dag_process_id)
	dps = DAGProcessStatus(dag_process=dag_process
							,pid_running=dag_process.pid
							,memory_consumption=dag_process.dag_memerory_percent
							,cpu_consumption=dag_process.dag_cpu_percent
							,child_processes=dag_process.dag_number_children)
	dps.save()


### Creates Background Task Hash after DAG Process Creation
@receiver(post_save, sender=DAGProcess)
def creat_consumption_task(sender, instance, created, **kwargs):
	try:
		task_obj = Task.objects.get(verbose_name='consumption_task_{}'.format(instance.pk))
		task_obj.delete()
		dag_process_tracking(instance.pk, repeat=5, verbose_name='consumption_task_{}'.format(instance.pk))
	except Exception as e:
		print(str(e))