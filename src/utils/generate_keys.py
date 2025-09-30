"""
Утилита для генерации безопасных ключей
"""
import secrets
import argparse


def generate_secret_key():
    """Генерация безопасного SECRET_KEY"""
    return secrets.token_urlsafe(32)


def generate_config():
    """Генерация .env файла с безопасными ключами"""
    env_content = f"""# Auto-generated .env file
SECRET_KEY={generate_secret_key()}
ACCESS_TOKEN_EXPIRE_MINUTES=120
SMS_CODE_EXPIRE_MINUTES=10
DATABASE_URL=sqlite:///./auth.db
SMS_API_KEY=your-sms-provider-key
BCRYPT_ROUNDS=12
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ .env файл создан с безопасными ключами")
    print("⚠️  Не забудьте установить реальный SMS_API_KEY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генератор безопасных ключей")
    parser.add_argument('--config', action='store_true', help='Создать .env файл')

    args = parser.parse_args()

    if args.config:
        generate_config()
    else:
        print(f"SECRET_KEY: {generate_secret_key()}")