from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from appadmin import views as admin_views
from dag import views as dag_views

urlpatterns = [
    path('', dag_views.DAGListView.as_view(), name='index'),
    path('admin/', admin.site.urls, name='admin_home'),
    path('login/', admin_views.login_user, name='login_user'),
    path('logout/', admin_views.logout_user, name='logout'),
    path('dag/', include('dag.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)