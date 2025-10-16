# explore_video_grants.py
import sys
import os

# Путь к корню проекта для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from livekit.api.access_token import VideoGrants

    print("✅ Successfully imported VideoGrants from livekit.api.access_token")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import...")
    try:
        from livekit import api

        VideoGrants = api.VideoGrants
        print("✅ Successfully imported VideoGrants from livekit.api")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        sys.exit(1)


def explore_video_grants():
    """Исследование структуры VideoGrants"""

    # Создаем объект
    grants = VideoGrants()

    print("\n" + "=" * 60)
    print("🔍 VIDEOGRANTS ATTRIBUTES EXPLORATION")
    print("=" * 60)

    # Разделяем атрибуты на методы и свойства
    methods = []
    properties = []

    for attr in dir(grants):
        if attr.startswith('_'):
            continue

        value = getattr(grants, attr)
        if callable(value):
            methods.append(attr)
        else:
            properties.append((attr, value, type(value)))

    print(f"\n📊 PROPERTIES ({len(properties)}):")
    print("-" * 40)

    for attr, value, value_type in sorted(properties):
        print(f"  🏷️  {attr:25} : {value:15} ({value_type.__name__})")

    print(f"\n⚙️  METHODS ({len(methods)}):")
    print("-" * 40)
    for method in sorted(methods):
        print(f"  🔧 {method}()")

    # Детальная информация о свойствах
    print(f"\n🔎 DETAILED PROPERTIES ANALYSIS:")
    print("-" * 40)

    for attr, value, value_type in sorted(properties):
        print(f"\n  🎯 {attr}:")
        print(f"     Value: {value}")
        print(f"     Type:  {value_type}")
        print(f"     Default: {value}")

    # Тестируем установку значений
    print(f"\n🧪 TESTING VALUE ASSIGNMENT:")
    print("-" * 40)

    test_grants = VideoGrants()

    # Пробуем установить различные значения
    test_values = {
        'room_join': True,
        'room_create': False,
        'room_admin': True,
        'room_list': False,
        'room': "test_room_123",
        'can_publish': True,
        'can_subscribe': True,
        'can_publish_data': False,
        'hidden': True,
        'recorder': False,
    }

    successful_assignments = []
    failed_assignments = []

    for attr, test_value in test_values.items():
        try:
            if hasattr(test_grants, attr):
                setattr(test_grants, attr, test_value)
                actual_value = getattr(test_grants, attr)
                successful_assignments.append((attr, test_value, actual_value))
            else:
                failed_assignments.append(attr)
        except Exception as e:
            failed_assignments.append(f"{attr} (Error: {e})")

    print("✅ Successfully assigned:")
    for attr, expected, actual in successful_assignments:
        print(f"   {attr:25} : {expected} -> {actual}")

    if failed_assignments:
        print(f"\n❌ Failed to assign:")
        for attr in failed_assignments:
            print(f"   {attr}")


def check_documentation():
    """Проверка документации"""
    print("\n" + "=" * 60)
    print("📚 VIDEOGRANTS DOCUMENTATION")
    print("=" * 60)

    try:
        help(VideoGrants)
    except:
        print("No help available for VideoGrants")

    # Альтернативный способ получить информацию
    print(f"\n💡 BASIC INFO:")
    print(f"   Module: {VideoGrants.__module__}")
    print(f"   Name: {VideoGrants.__name__}")


def create_example_tokens():
    """Примеры создания токенов с разными правами"""
    print("\n" + "=" * 60)
    print("🎫 TOKEN CREATION EXAMPLES")
    print("=" * 60)

    try:
        from livekit.api.access_token import AccessToken
        from datetime import timedelta

        print("\n👑 CREATOR TOKEN EXAMPLE:")
        creator_grants = VideoGrants()
        creator_grants.room_create = True
        creator_grants.room_join = True
        creator_grants.room = "webinar_123"
        creator_grants.can_publish = True
        creator_grants.can_subscribe = True
        creator_grants.can_publish_data = True
        creator_grants.room_admin = True

        print("   Creator grants:")
        for attr in dir(creator_grants):
            if not attr.startswith('_') and not callable(getattr(creator_grants, attr)):
                value = getattr(creator_grants, attr)
                print(f"     {attr}: {value}")

        print("\n👥 PARTICIPANT TOKEN EXAMPLE:")
        participant_grants = VideoGrants()
        participant_grants.room_join = True
        participant_grants.room = "webinar_123"
        participant_grants.can_publish = False
        participant_grants.can_subscribe = True
        participant_grants.can_publish_data = True
        participant_grants.room_admin = False

        print("   Participant grants:")
        for attr in dir(participant_grants):
            if not attr.startswith('_') and not callable(getattr(participant_grants, attr)):
                value = getattr(participant_grants, attr)
                print(f"     {attr}: {value}")

        # Демонстрация создания токена (без реальных ключей)
        print(f"\n🔐 TOKEN CREATION DEMO:")
        try:
            # Это демо - используем тестовые ключи
            token = (AccessToken(api_key="demo_key", api_secret="demo_secret")
                     .with_identity("user_123")
                     .with_name("Test User")
                     .with_grants(participant_grants)
                     .with_ttl(timedelta(hours=2)))

            print("   Token created successfully (demo)")
            print(f"   Identity: user_123")
            print(f"   Name: Test User")
            print(f"   TTL: 2 hours")

        except Exception as e:
            print(f"   Token creation demo failed: {e}")

    except ImportError as e:
        print(f"❌ Cannot demonstrate token creation: {e}")


if __name__ == "__main__":
    print("🚀 STARTING VIDEOGRANTS EXPLORATION...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    explore_video_grants()
    check_documentation()
    create_example_tokens()

    print("\n" + "=" * 60)
    print("✅ EXPLORATION COMPLETED")
    print("=" * 60)