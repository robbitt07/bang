from django.contrib.auth.models import User
from django import forms

from pagedown.widgets import PagedownWidget

from appadmin.models import ProcessPackages
from dag.models import DAG, DAGItem, DAGDependency, DAGAsset


class DAGForm(forms.ModelForm):
	dag_name = forms.CharField(widget=forms.TextInput(attrs={
						'class': 'form-control', 'size': '5',})
						, required=True)
	
	initial_run_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs=
                                {'class': 'form-control float-left',})
                                , label='Initial Run Time', required=False)

	repeat = forms.IntegerField(widget=forms.NumberInput(
						attrs={'class': 'form-control', 'size': '5',})
						,required=False, initial=0)

	job_owner = forms.ModelChoiceField(User.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)

	class Meta:
		model = DAG
		fields = ['dag_name', 'initial_run_time', 'repeat', 'job_owner',]


class DAGItemScriptForm(forms.ModelForm):
	item_type = forms.CharField(widget=forms.HiddenInput(), required=False)
	
	dag = forms.ModelChoiceField(DAG.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)
	
	parent = forms.ModelChoiceField(DAGItem.objects.none(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)

	job_name = forms.CharField(widget=forms.TextInput(attrs={
						'class': 'form-control', 'size': '5',})
						, required=True)
	
	job_owner = forms.ModelChoiceField(User.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)

	job_script = forms.CharField(widget=PagedownWidget(show_preview=False,
									attrs={'class': 'form-control float-left', 'rows': '20',}
									), label='Job Script', required=False)

	class Meta:
		model = DAGItem
		fields = ['item_type', 'dag', 'parent', 'job_name', 'job_owner'
					,'job_script', ]


class DAGItemPathForm(forms.ModelForm):
	item_type = forms.CharField(widget=forms.HiddenInput(), required=False)
	
	dag = forms.ModelChoiceField(DAG.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)
	
	parent = forms.ModelChoiceField(DAGItem.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)

	job_name = forms.CharField(widget=forms.TextInput(attrs={
						'class': 'form-control', 'size': '5',})
						, required=True)
	
	script_full_path = forms.CharField(widget=forms.TextInput(attrs={
						'class': 'form-control', 'size': '5',})
						, required=True)

	job_owner = forms.ModelChoiceField(User.objects.all(),
					widget = forms.Select(attrs = {'class' : 'form-control',})
					,required=False)

	class Meta:
		model = DAGItem
		fields = ['item_type', 'dag', 'parent', 'job_name', 'script_full_path',
					'job_owner']


class DAGDependencyForm(forms.ModelForm):
	dag_item = forms.ModelChoiceField(DAGItem.objects.all()
										,widget = forms.Select(attrs = {'class' : 'form-control',})
										,required=False)
						
	package = forms.ModelChoiceField(ProcessPackages.objects.all()
										,widget = forms.Select(attrs = {'class' : 'form-control',})
										,required=False)

	sub_module = forms.CharField(widget=forms.TextInput(attrs={
									'class': 'form-control', 'size': '5',})
									, required=True)

	class Meta:
		model = DAGDependency
		fields = ['dag_item', 'package', 'sub_module',]


class DAGAssetForm(forms.ModelForm):
	dag_item = forms.ModelChoiceField(DAGItem.objects.all(),
										widget = forms.Select(attrs = {'class' : 'form-control',})
										,required=False)
						
	dag_asset = forms.FileField(widget=forms.ClearableFileInput(attrs=
								{'class': 'form-control float-left', 'size': '5',}
								), label='DAG Asset File', required=False)

	notes = forms.CharField(widget=forms.TextInput(attrs={
						'class': 'form-control', 'size': '5',})
						, required=True)

	class Meta:
		model = DAGAsset
		fields = ['dag_item', 'dag_asset', 'notes',]



