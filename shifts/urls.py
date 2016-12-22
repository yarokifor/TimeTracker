from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^login$', views.login_handler),
    url(r'^logout$', views.logout_handler),
    url(r'^shifts$', views.shifts),
    url(r'^export$', views.export),
    url(r'^profile$', views.profile),

]
