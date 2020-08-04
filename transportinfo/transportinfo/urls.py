from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('trains/', include('trains.urls')),
    path('busses/', include('trains.urls')),
]
