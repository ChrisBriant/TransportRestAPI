from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^helloworld/', views.helloworld, name='helloworld'),
	url(r'^traintest/', views.traintest, name='traintest'),
	url(r'^trainslatest/', views.trainslatest, name='trainslatest'),
	url(r'^busses/', views.busses, name='busses')
]
