# explore_video_grants.py
from livekit.api.access_token import VideoGrants

# Создаем объект и смотрим какие атрибуты доступны
grants = VideoGrants()

print("VideoGrants attributes:")
for attr in dir(grants):
    if not attr.startswith('_'):
        value = getattr(grants, attr)
        print(f"  {attr}: {value} ({type(value)})")

# Проверим документацию
try:
    help(VideoGrants)
except:
    print("No help available for VideoGrants")