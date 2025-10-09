# src/dependencies/rbac.py
from fastapi import HTTPException, Depends
from starlette import status

from src import schemas
from src.security.auth import get_current_user

def permission(required_roles: list):
    """Декоратор для проверки прав доступа"""

    def role_checker(current_user: schemas.UserResponse = Depends(get_current_user)):
        # Проверяем, что пользователь активен
        if not getattr(current_user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        # Проверяем роли
        user_roles = getattr(current_user, 'roles', [])
        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user

    return role_checker


# Специфичные проверки для разных ролей
admin_permission = permission(["admin"])
manager_permission = permission(["manager"])
admin_or_manager_permission = permission(["admin", "manager"])


# Дополнительная проверка активности аккаунта
def active_user_permission():
    """Проверка, что пользователь активен"""

    def checker(current_user: schemas.UserResponse = Depends(get_current_user)):
        if not getattr(current_user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        return current_user

    return checker