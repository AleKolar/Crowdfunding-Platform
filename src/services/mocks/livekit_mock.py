# src/services/mocks/livekit_mock.py
"""
Заглушка для LiveKit в тестовом режиме
"""
class AccessToken:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self._identity = None
        self._name = None
        self._grants = None
        self._ttl = None

    def with_identity(self, identity):
        self._identity = identity
        return self

    def with_name(self, name):
        self._name = name
        return self

    def with_grants(self, grants):
        self._grants = grants
        return self

    def with_ttl(self, ttl):
        self._ttl = ttl
        return self

    def to_jwt(self):
        # Возвращаем фиктивный токен для тестов
        return f"mock_token_{self._identity}_{id(self)}"


class VideoGrants:
    def __init__(self):
        self.room_create = False
        self.room_join = False
        self.room = None
        self.can_publish = False
        self.can_subscribe = False
        self.can_publish_data = False
        self.room_admin = False
        self.hidden = False
        self.recorder = False