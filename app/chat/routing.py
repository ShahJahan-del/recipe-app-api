from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Captures alphanumeric strings and hands them to the ChatConsumer
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]