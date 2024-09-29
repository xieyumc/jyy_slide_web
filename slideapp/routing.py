# slideapp/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/slide/(?P<slide_id>\d+)/$', consumers.SlideConsumer.as_asgi()),
]