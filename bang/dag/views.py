from django.db.models import Max
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (DetailView
									,ListView
									,UpdateView
									,CreateView
									,DeleteView)
from django.views import View

from appadmin.models import ProcessPackages
from background_task.models import Task
from dag.forms import (DAGForm
						,DAGItemScriptForm
						,DAGItemPathForm
						,DAGDependencyForm
						,DAGAssetForm)
from dag.models import (DAG
						,DAGItem
						,DagItemHistory
						,DAGDependency
						,DAGAsset
						,DAGItemLogging
						,DAGProcess)
from dag.pipeline import base_dag_run

import difflib
import json
import re
import subprocess


class DAGCreateView(CreateView):
	model = DAGForm
	template_name = 'dag/dag_form.html'
	form_class = DAGForm

	def form_valid(self, form):
		self.object = form.save()
		
		base_dag_run(dag_pk=self.object.pk
						,schedule=form.cleaned_data['initial_run_time']
						,repeat=form.cleaned_data['repeat']
						,verbose_name=self.object.dag_hash
						,creator=self.object
						,queue=self.object.dag_name)

		return HttpResponseRedirect(self.get_success_url())


class DAGListView(ListView):
	model = DAG
	template_name = 'dag/dag_list.html'
	context_object_name = 'object_list'
	paginate_by = 50


class DAGDetailView(DetailView):
	model = DAG
	template_name = 'dag/dag_detail.html'

	def get_context_data(self, **kwargs):
		context = super(DAGDetailView, self).get_context_data(**kwargs)
		current_tasks = Task.objects.filter(creator_content_type=ContentType.objects.get_for_model(DAG)
											,creator_object_id=context['object'].pk)
		context['current_tasks'] = current_tasks
		
		recent_logging = DAGItemLogging.objects.filter(dag_item__dag_id=context['object'].pk)[0:30]
		context['recent_logging'] = recent_logging
		return context
		

class DAGUpdateView(UpdateView):
	model = DAG
	template_name = 'dag/dag_form.html'
	form_class = DAGForm

	def form_valid(self, form):
		self.object = form.save()
		dag_obj= DAG.objects.get(pk=self.kwargs['pk'])
		
		for task_obj in dag_obj.get_open_tasks():
			task_obj.delete()
					
		base_dag_run(dag_pk=self.object.pk
						,schedule=form.cleaned_data['initial_run_time']
						,repeat=form.cleaned_data['repeat']
						,verbose_name=self.object.dag_hash
						,creator=self.object
						,queue=self.object.dag_name)

		return HttpResponseRedirect(self.get_success_url())


class DAGDeleteView(DeleteView):
	model = DAG
	template_name = 'dag/dag_check_delete.html'
	success_url = reverse_lazy('index')

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		for task_obj in self.object.get_open_tasks():
			task_obj.delete()

		self.object.delete()
		return HttpResponseRedirect(self.get_success_url())



### ------------------------------------------------------------------------
### DAG Items  ( Internal Script )
### ------------------------------------------------------------------------
class DAGItemScriptCreateView(CreateView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_form.html'
	form_class = DAGItemScriptForm

	def get_initial(self):
		return { 'item_type': 'SCRIPT'}


class DAGItemParentOptionView(View):

	def get(self, *args, **kwargs):
		pk = self.request.GET['pk']
		dag_items = DAGItem.objects.filter(dag=pk)
		return render(self.request, 'dag/dag_item/dag_item_parent_options.html', {'dag_items': dag_items})


class DAGItemDetailView(DetailView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_detail.html'
	
	def get_context_data(self, **kwargs):
		context = super(DAGItemDetailView, self).get_context_data(**kwargs)

		recent_logging = self.object.logs.all()[0:10]
		context['recent_logging'] = recent_logging

		return context		


class DAGItemScriptUpdateView(UpdateView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_form.html'
	form_class = DAGItemScriptForm

	def get_form(self, *args, **kwargs):
		form = super(DAGItemScriptUpdateView, self).get_form(*args, **kwargs)
		dag_obj = DAGItem.objects.get(pk=self.kwargs['pk']).dag
		form.fields['parent'].queryset = DAGItem.objects.filter(dag=dag_obj)
		return form

	def form_valid(self, form):
		self.object = form.save()

		## Version History
		version_num = self.object.version_history.aggregate(Max('version_number'))['version_number__max']
		if version_num is None:
			version_num = 1
		else:
			version_num += 1

		initial_script = form.initial['job_script']
		current_script = form.cleaned_data['job_script']

		diff_result = difflib.ndiff(initial_script.strip().split('\n')
											,current_script.strip().split('\n'))
		diff_list = [text for text in diff_result if text[:3] not in ('+++', '---', '@@ ')]
		diff_text = '\n'.join(diff_list)
		diff_info = [{'color' : 'red' if x[0] == '-' else 'light-green' if x[0] == '+' else ''
						,'text' : x} for x in diff_list]

		dih = DagItemHistory(dag_item=self.object
								,version_number=version_num
								,script_text=initial_script
								,script_diff_text=diff_text
								,script_diff_list=str(diff_info)
								,user_edit=self.request.user)
		dih.save()

		return HttpResponseRedirect(self.get_success_url())

	
class DAGItemDeleteView(DeleteView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_check_delete.html'
	success_url = reverse_lazy('index')


class DAGItemScriptVersionHistory(DetailView):
	model = DagItemHistory
	template_name = 'dag/dag_item/dagitem_version_history.html'
	

class DagItemScriptVersionHistoryExport(View):

	def get(self, request, *args, **kwargs):
		referer = request.META.get('HTTP_REFERER')
		pk = kwargs.get('pk', None)
		if pk is None:
			return HttpResponseRedirect(referer)
		else:
			instance = get_object_or_404(DagItemHistory, pk=pk)
			try:
				content = instance.script_text
				file_name = '{}.py'.format(str(instance.dag_item.job_name))
			except:
				content = None
				pass

			# Create the HttpResponse object with the appropriate CSV header.
			response = HttpResponse(content, content_type='text/plain')
			response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
			return response


### ------------------------------------------------------------------------
### DAG Items  ( Path to Script )
### ------------------------------------------------------------------------
class DAGItemPathCreateView(CreateView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_path_form.html'
	form_class = DAGItemPathForm

	def get_initial(self):
		return { 'item_type': 'PATH'}


class DAGItemPathUpdateView(UpdateView):
	model = DAGItem
	template_name = 'dag/dag_item/dagitem_path_form.html'
	form_class = DAGItemPathForm

	def get_form(self, *args, **kwargs):
		form = super(DAGItemPathUpdateView, self).get_form(*args, **kwargs)
		dag_obj = DAGItem.objects.get(pk=self.kwargs['pk']).dag
		form.fields['parent'].queryset = DAGItem.objects.filter(dag=dag_obj)
		return form


### ------------------------------------------------------------------------
### DAG Dependency
### ------------------------------------------------------------------------
def dependency_list(request, pk):
	instance = get_object_or_404(DAGItem, pk=pk)
	if instance.item_type == 'SCRIPT':  ## Internal Script
		job_script = instance.job_script
	else:								## External Script/Path
		job_script = open(instance.script_full_path).read()
	
	dep_suggest_list = [x.split()[1].split('.')[0] for x in re.split(r"[~\r\n]+", job_script) 
							if x.startswith('import') or x.startswith('from')]

	current_packages = [x.package.pk for x in instance.dependencies.filter(sub_module__isnull=True)]

	package_all = ProcessPackages.objects.all()

	package_initial_list = [{'pk' : package.pk,
								'import_name' : package.import_name,
								'suggested' : bool(package.import_name in dep_suggest_list),
								'is_imported' : bool(package.pk in current_packages)} 
									for package in package_all]

	if request.method == "POST":
		
		package_initial_ids = [x.pk for x in package_all]
		result_list = {value:request.POST.get('pkg_{}'.format(str(value)), '') == 'on'
									for value in package_initial_ids}
		checked_list = [k for k, v in result_list.items() if v]
			
		### Removals
		removal_list = list(set(current_packages) - set(checked_list))
		DAGDependency.objects.filter(dag_item=instance, package_id__in=removal_list, sub_module__isnull=True).delete()

		### Additions
		for package_id in list(set(checked_list) - set(current_packages)):
			dp = DAGDependency.objects.create(dag_item=instance
												,package=package_all.get(pk=package_id))
			dp.save()

		return redirect(instance.get_absolute_url())
	
	context = {
		"object" : instance,
		"package_list" : package_initial_list
	}

	return render(request, "dag/dag_dependencies_form.html", context)


### ------------------------------------------------------------------------
### DAG Dependency Adhoc
### ------------------------------------------------------------------------
class DAGDependencyCreateView(CreateView):
	model = DAGDependency
	template_name = 'dag/dag_item/dagitem_dependency_form.html'
	form_class = DAGDependencyForm

	def get_initial(self):
		try:
			dag_item_id = self.request.GET.get('dag_item', None)
			dag_item = DAGItem.objects.get(pk=dag_item_id)
		except:
			dag_item = None
		initial = {'dag_item' : dag_item}
		return initial

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


class DAGDependencyUpdateView(UpdateView):
	model = DAGDependency
	template_name = 'dag/dag_item/dagitem_dependency_form.html'
	form_class = DAGDependencyForm

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


class DAGDependencyDeleteView(DeleteView):
	model = DAGDependency
	template_name = 'dag/dag_item/dagitem_check_delete.html'

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


### ------------------------------------------------------------------------
### DAG Assets
### ------------------------------------------------------------------------
class DAGAssetCreateView(CreateView):
	model = DAGAsset
	template_name = 'dag/dag_item/dagitem_form.html'
	form_class = DAGAssetForm

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


class DAGAssetUpdateView(UpdateView):
	model = DAGAsset
	template_name = 'dag/dag_item/dagitem_form.html'
	form_class = DAGAssetForm

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


class DAGAssetDeleteView(DeleteView):
	model = DAGAsset
	template_name = 'dag/dag_item/dagitem_check_delete.html'

	def get_success_url(self):
		return reverse('dag:dagitem_detail', args=(self.object.dag_item_id,))


### ------------------------------------------------------------------------
### DAG Process
### ------------------------------------------------------------------------
class DAGProcessListView(ListView):
	model = DAGProcess
	template_name = 'dag/dag_process/dagprocess_list.html'
	context_object_name = 'object_list'
	paginate_by = 50


class DAGProcessDetailView(DetailView):
	model = DAGProcess
	template_name = 'dag/dag_process/dagprocess_detail.html'


class DAGProcessInitiateView(View):
	
	def get(self, request, *args, **kwargs):
		referer = request.META.get('HTTP_REFERER')
		dag_obj = DAG.objects.get(pk=self.kwargs['pk'])
		subprocess.run('start python run_tasks.py {}'.format(str(dag_obj.dag_name)), shell=True)
		return HttpResponseRedirect(referer)


class DAGProcessStartView(View):

	def get(self, request, *args, **kwargs):
		referer = request.META.get('HTTP_REFERER')
		dag_process_obj = DAGProcess.objects.get(pk=self.kwargs['pk'])
		dag_process_obj.start_process()
		return HttpResponseRedirect(referer)


class DAGProcessEndView(View):
	
	def get(self, request, *args, **kwargs):
		referer = request.META.get('HTTP_REFERER')
		dag_process_obj = DAGProcess.objects.get(pk=self.kwargs['pk'])
		dag_process_obj.end_process()
		return HttpResponseRedirect(referer)