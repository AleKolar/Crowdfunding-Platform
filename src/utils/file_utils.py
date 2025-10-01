# src/utils/file_utils.py
import os
import aiofiles
from typing import Tuple
from fastapi import UploadFile, HTTPException
from starlette import status

from src.database.models.models_content import MediaType

# Поддерживаемые MIME types
SUPPORTED_MIME_TYPES = {
    'image/jpeg': MediaType.IMAGE,
    'image/png': MediaType.IMAGE,
    'image/gif': MediaType.GIF,
    'image/webp': MediaType.IMAGE,
    'image/svg+xml': MediaType.IMAGE,
    'video/mp4': MediaType.VIDEO,
    'video/mpeg': MediaType.VIDEO,
    'video/quicktime': MediaType.VIDEO,
    'video/webm': MediaType.VIDEO,
    'video/x-msvideo': MediaType.VIDEO,
    'audio/mpeg': MediaType.AUDIO,
    'audio/wav': MediaType.AUDIO,
    'audio/ogg': MediaType.AUDIO,
    'audio/mp4': MediaType.AUDIO,
    'audio/x-wav': MediaType.AUDIO,
    'application/pdf': MediaType.DOCUMENT,
    'application/msword': MediaType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': MediaType.DOCUMENT,
    'application/vnd.ms-excel': MediaType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': MediaType.DOCUMENT,
    'text/plain': MediaType.DOCUMENT,
}

# Расширения файлов как fallback
EXTENSION_TO_MEDIA_TYPE = {
    '.jpg': MediaType.IMAGE,
    '.jpeg': MediaType.IMAGE,
    '.png': MediaType.IMAGE,
    '.gif': MediaType.GIF,
    '.webp': MediaType.IMAGE,
    '.svg': MediaType.IMAGE,
    '.mp4': MediaType.VIDEO,
    '.mov': MediaType.VIDEO,
    '.avi': MediaType.VIDEO,
    '.webm': MediaType.VIDEO,
    '.mp3': MediaType.AUDIO,
    '.wav': MediaType.AUDIO,
    '.ogg': MediaType.AUDIO,
    '.m4a': MediaType.AUDIO,
    '.pdf': MediaType.DOCUMENT,
    '.doc': MediaType.DOCUMENT,
    '.docx': MediaType.DOCUMENT,
    '.txt': MediaType.DOCUMENT,
}

# Максимальные размеры файлов (в байтах)
MAX_FILE_SIZES = {
    MediaType.IMAGE: 10 * 1024 * 1024,      # 10MB
    MediaType.VIDEO: 100 * 1024 * 1024,     # 100MB
    MediaType.AUDIO: 50 * 1024 * 1024,      # 50MB
    MediaType.DOCUMENT: 20 * 1024 * 1024,   # 20MB
    MediaType.GIF: 15 * 1024 * 1024,        # 15MB
    MediaType.OTHER: 5 * 1024 * 1024,       # 5MB
}

def get_media_type_from_extension(filename: str) -> MediaType:
    """Определение типа медиа по расширению файла"""
    ext = os.path.splitext(filename)[1].lower()
    return EXTENSION_TO_MEDIA_TYPE.get(ext, MediaType.OTHER)

async def validate_and_get_media_type(file: UploadFile) -> Tuple[MediaType, str]:
    """Упрощенная валидация файла по расширению без python-magic"""

    contents = await file.read()
    await file.seek(0)

    media_type = get_media_type_from_extension(file.filename)

    if not media_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла: {file.filename}"
        )

    # Проверка размера файла
    max_size = MAX_FILE_SIZES.get(media_type, 5 * 1024 * 1024)
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {max_size // 1024 // 1024}MB"
        )

    return media_type, f"determined/from-extension-{media_type.value}"


def generate_file_path(project_id: int, media_type: MediaType, filename: str) -> str:
    """Генерация пути для сохранения файла"""
    # Создаем уникальное имя файла
    import uuid

    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    # Структура папок: media/projects/{project_id}/{type}/{filename}
    return f"media/projects/{project_id}/{media_type.value}/{unique_filename}"


async def save_uploaded_file(file: UploadFile, file_path: str) -> int:
    """Сохранение загруженного файла"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return len(content)