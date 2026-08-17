"""Character document management with per-call credential checks."""

from __future__ import annotations

import base64
from pathlib import Path

import Users
import _global_resources

ALLOWED_TEXT_EXTENSIONS = {".txt", ".md"}
ALLOWED_IMAGE_EXTENSIONS = {".png"}
ALLOWED_EXTENSIONS = ALLOWED_TEXT_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS
MANAGER_ROLES = {"gm", "admin"}


def _authorize_character_documents(user_id: str, username: str, password_hash: str, character_id: str) -> Path:
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")
    role = (_global_resources.get_user_role(user_id) or "").lower()
    character_path, owner_folder, _ = _global_resources.find_character(character_id)
    if owner_folder != user_id.removeprefix("User_") and role not in MANAGER_ROLES:
        raise PermissionError("Only the owning user or a GM/Admin may access these documents")
    documents_path = character_path / "documents"
    documents_path.mkdir(parents=True, exist_ok=True)
    return documents_path


def _validated_name(file_name: str) -> str:
    if not isinstance(file_name, str) or not file_name.strip():
        raise ValueError("file_name must be a non-empty string")
    normalized = file_name.strip()
    if normalized in {".", ".."} or Path(normalized).name != normalized:
        raise ValueError("file_name must be a single path component")
    extension = Path(normalized).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .txt, .md and .png files are allowed")
    return normalized


def _document_kind(file_name: str) -> str:
    return "image" if Path(file_name).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS else "text"


def listCharacterDocuments(user_id: str, username: str, password_hash: str, character_id: str) -> list[dict[str, str | int]]:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    entries: list[dict[str, str | int]] = []
    for entry in documents_path.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        entries.append(
            {
                "name": entry.name,
                "type": _document_kind(entry.name),
                "size": entry.stat().st_size,
            }
        )
    entries.sort(key=lambda item: str(item["name"]).lower())
    return entries


def openCharacterDocument(user_id: str, username: str, password_hash: str, character_id: str, file_name: str) -> dict[str, str]:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    normalized_name = _validated_name(file_name)
    file_path = documents_path / normalized_name
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Document {normalized_name} does not exist")
    file_type = _document_kind(normalized_name)
    if file_type == "image":
        content = base64.b64encode(file_path.read_bytes()).decode("ascii")
        return {"name": normalized_name, "type": file_type, "mime_type": "image/png", "content_base64": content}
    return {"name": normalized_name, "type": file_type, "content": file_path.read_text(encoding="utf-8")}


def createCharacterTextDocument(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    file_name: str,
    content: str = "",
) -> str:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    normalized_name = _validated_name(file_name)
    if Path(normalized_name).suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
        raise ValueError("Only .txt and .md files can be created as text documents")
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    file_path = documents_path / normalized_name
    if file_path.exists():
        raise ValueError(f"Document {normalized_name} already exists")
    file_path.write_text(content, encoding="utf-8")
    return normalized_name


def updateCharacterTextDocument(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    file_name: str,
    content: str,
) -> str:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    normalized_name = _validated_name(file_name)
    if Path(normalized_name).suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
        raise ValueError("Only .txt and .md files can be edited in the text editor")
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    file_path = documents_path / normalized_name
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Document {normalized_name} does not exist")
    file_path.write_text(content, encoding="utf-8")
    return normalized_name


def uploadCharacterDocument(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    file_name: str,
    content: str,
    encoding: str = "text",
) -> str:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    normalized_name = _validated_name(file_name)
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    if encoding not in {"text", "base64"}:
        raise ValueError("encoding must be 'text' or 'base64'")
    extension = Path(normalized_name).suffix.lower()
    file_path = documents_path / normalized_name
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        if encoding != "base64":
            raise ValueError("Image uploads must use base64 encoding")
        file_path.write_bytes(base64.b64decode(content, validate=True))
        return normalized_name
    if encoding == "base64":
        text_content = base64.b64decode(content, validate=True).decode("utf-8")
    else:
        text_content = content
    file_path.write_text(text_content, encoding="utf-8")
    return normalized_name


def deleteCharacterDocument(user_id: str, username: str, password_hash: str, character_id: str, file_name: str) -> None:
    documents_path = _authorize_character_documents(user_id, username, password_hash, character_id)
    normalized_name = _validated_name(file_name)
    file_path = documents_path / normalized_name
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Document {normalized_name} does not exist")
    file_path.unlink()
