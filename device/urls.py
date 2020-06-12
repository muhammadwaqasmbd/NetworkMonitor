from django.urls import path
from . import views


urlpatterns = [
    path('',views.home,name="home"),
    path('live',views.home,name="home"),
    path('historic',views.historic,name="historic"),
    path('device',views.device,name="device"),
]
