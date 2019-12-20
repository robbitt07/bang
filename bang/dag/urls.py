from django.urls import path, include
from django.conf.urls import url
from django.views.generic import TemplateView


from dag import api
from dag import views

app_name = 'dag'

urlpatterns = [
    path('dag/', views.DAGListView.as_view(), name='dag_list'), 
    path('dag/create/', views.DAGCreateView.as_view(), name='dag_create'),
    path('dag/detail/<int:pk>/', views.DAGDetailView.as_view(), name='dag_detail'), 
    path('dag/update/<int:pk>/', views.DAGUpdateView.as_view(), name='dag_update'), 
    path('dag/delete/<int:pk>/', views.DAGDeleteView.as_view(), name='dag_delete'), 

    path('dagitem/create/', views.DAGItemScriptCreateView.as_view(), name='dagitem_script_create'),
    path('dagitem/detail/<int:pk>/', views.DAGItemDetailView.as_view(), name='dagitem_detail'), 
    path('dagitem/update/<int:pk>/', views.DAGItemScriptUpdateView.as_view(), name='dagitem_script_update'), 
    path('dagitem/delete/<int:pk>/', views.DAGItemDeleteView.as_view(), name='dagitem_delete'),

    path('dagitem_path/create/', views.DAGItemPathCreateView.as_view(), name='dagitem_path_create'),
    path('dagitem_path/update/<int:pk>/', views.DAGItemPathUpdateView.as_view(), name='dagitem_path_update'), 

    path('dagitem/dependency_list/<int:pk>/', views.dependency_list, name='dagitem_dependency_list'), 
    path('dagitem/dependency/create/', views.DAGDependencyCreateView.as_view(), name='dagitem_dependency_create'),
    path('dagitem/dependency/update/<int:pk>/', views.DAGDependencyUpdateView.as_view(), name='dagitem_dependency_update'), 
    path('dagitem/dependency/delete/<int:pk>/', views.DAGDependencyDeleteView.as_view(), name='dagitem_dependency_delete'),

    path('dagitem/version_history/<int:pk>/', views.DAGItemScriptVersionHistory.as_view(), name='dagitem_version_history'),
    path('dagitem/version_history/export/<int:pk>/', views.DagItemScriptVersionHistoryExport.as_view(), name='dagitem_version_history_export'),
    
    path('dagasset/create/', views.DAGAssetCreateView.as_view(), name='dagasset_create'), 
    path('dagasset/update/<int:pk>/', views.DAGAssetUpdateView.as_view(), name='dagasset_update'), 
   
]

### DAG Items
urlpatterns += [
    path('dagitem/parent_options/', views.DAGItemParentOptionView.as_view(), name='dagitem_parent_options'), 
   
]

### DAG Process
urlpatterns += [
    path('process/', views.DAGProcessListView.as_view(), name='dag_process_list'), 
    path('process/<int:pk>/', views.DAGProcessDetailView.as_view(), name='dag_process_detail'),
    path('process/initiate/<int:pk>/', views.DAGProcessInitiateView.as_view(), name='dag_initiate_process'), 
    path('process/start/<int:pk>/', views.DAGProcessStartView.as_view(), name='dag_start_process'), 
    path('process/end/<int:pk>/', views.DAGProcessEndView.as_view(), name='dag_end_process'),
]


urlpatterns += [
    path('api/v1/process/list/', api.DAGProcessStatusListView.as_view(), name='api_process_list'),
]   