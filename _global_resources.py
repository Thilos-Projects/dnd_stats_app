"""Shared persistence and access-control helpers for global character resources."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import Users

DATA_PATH = Path(__file__).parent / "data"
MANAGER_ROLES = {"gm"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def require_manager(user_id: str, username: str, password_hash: str, resource_name: str) -> None:
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")
    role = Users.getUserRole(user_id)
    if role is None or role.lower() not in MANAGER_ROLES:
        raise PermissionError(f"Only GM users may manage {resource_name}")


def require_user(user_id: str, username: str, password_hash: str) -> None:
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")


def get_user_role(user_id: str) -> str | None:
    return Users.getUserRole(user_id)


def get_user_known_resources(user_id: str, known_field: str) -> set[str]:
    """Aggregate a known_* field across every character owned by user_id."""
    owner_folder = user_id.removeprefix("User_")
    known: set[str] = set()
    for character_file in (DATA_PATH / "User" / owner_folder).glob("*/Character.json"):
        character = load_json(character_file)
        known.update(character.get(known_field, []))
    return known


def find_character(character_id: str) -> tuple[Path, str, dict[str, Any]]:
    for character_file in (DATA_PATH / "User").glob("*/*/Character.json"):
        character = load_json(character_file)
        if character.get("ID") == character_id:
            return character_file.parent, character_file.parent.parent.name, character
    raise ValueError(f"Character {character_id} does not exist")


def authorize_character_resource(
    user_id: str,
    username: str,
    password_hash: str,
    owner_folder: str,
    character: dict[str, Any],
    known_field: str,
    resource_id: str,
    resource_name: str,
) -> None:
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")
    role = Users.getUserRole(user_id)
    if role is not None and role.lower() in MANAGER_ROLES:
        return
    if owner_folder != user_id.removeprefix("User_"):
        raise PermissionError("Only the character owner or a GM may manage this resource")
    if resource_id not in character.get(known_field, []):
        raise PermissionError(f"The character does not know this {resource_name}")


def next_id(resources: dict[str, Any], prefix: str) -> str:
    used_numbers = [
        int(resource_id.removeprefix(prefix))
        for resource_id in resources
        if resource_id.startswith(prefix) and resource_id.removeprefix(prefix).isdigit()
    ]
    return f"{prefix}{max(used_numbers, default=0) + 1}"


def get_resource(resources: dict[str, Any], resource_id: str, resource_name: str) -> dict[str, Any]:
    if resource_id not in resources:
        raise ValueError(f"{resource_name} {resource_id} does not exist")
    return resources[resource_id]


def update_character_rows(
    user_id: str,
    username: str,
    password_hash: str,
    resource_id: str,
    character_id: str,
    *,
    resource_path: Path,
    resource_name: str,
    row_name: str,
    known_field: str,
    remove: bool,
) -> None:
    resources = load_json(resource_path)
    get_resource(resources, resource_id, resource_name)
    character_path, owner_folder, character = find_character(character_id)
    authorize_character_resource(user_id, username, password_hash, owner_folder, character, known_field, resource_id, resource_name)
    stat_sheet_path = character_path / "StatSheet.json"
    stat_sheet = load_json(stat_sheet_path)
    rows = stat_sheet[row_name]["rows"]
    matching_rows = [row for row in rows if row.get("ID") == resource_id]
    if remove:
        if not matching_rows:
            raise ValueError(f"{resource_name} {resource_id} is not active on {character_id}")
        stat_sheet[row_name]["rows"] = [row for row in rows if row.get("ID") != resource_id]
    else:
        if matching_rows:
            raise ValueError(f"{resource_name} {resource_id} is already active on {character_id}")
        rows.append({"ID": resource_id})
    save_json(stat_sheet_path, stat_sheet)


def delete_resource(
    user_id: str,
    username: str,
    password_hash: str,
    resource_id: str,
    *,
    resource_path: Path,
    resource_name: str,
    row_name: str,
    known_field: str,
) -> None:
    require_manager(user_id, username, password_hash, resource_name)
    resources = load_json(resource_path)
    get_resource(resources, resource_id, resource_name)
    for stat_sheet_path in (DATA_PATH / "User").glob("*/**/StatSheet.json"):
        stat_sheet = load_json(stat_sheet_path)
        if any(row.get("ID") == resource_id for row in stat_sheet.get(row_name, {}).get("rows", [])):
            raise ValueError(f"Remove {resource_name} {resource_id} from its characters before deleting it")
    for character_path in (DATA_PATH / "User").glob("*/**/Character.json"):
        character = load_json(character_path)
        if resource_id in character.get(known_field, []):
            raise ValueError(f"Remove {resource_name} {resource_id} from known lists before deleting it")
    del resources[resource_id]
    save_json(resource_path, resources)


def _expect_error(expected: type[Exception], action: Any, description: str) -> None:
    try:
        action()
    except expected:
        return
    raise AssertionError(f"Expected {expected.__name__}: {description}")


def run_resource_self_test(
    *,
    resource_module: Any,
    resource_name: str,
    resource_prefix: str,
    row_name: str,
    known_field: str,
    create_resource: Any,
    edit_known: Any,
    assign_resource: Any,
    remove_resource: Any,
    delete_resource_fn: Any,
) -> None:
    """Exercise manager/player permissions and restore every touched data file."""
    import Characters

    test_tag = uuid.uuid4().hex[:10]
    users = {
        "gm": (f"{test_tag}_gm", "gm_password", "gm"),
        "player": (f"{test_tag}_player", "player_password", "player"),
        "other": (f"{test_tag}_other", "other_password", "player"),
    }
    user_ids: dict[str, str] = {}
    character_ids: dict[str, str] = {}
    resource_ids: list[str] = []
    resource_path = next(
        value for key, value in resource_module.__dict__.items()
        if key.endswith("_PATH") and isinstance(value, Path) and value.parent.name == "Global"
    )
    touched_paths = [DATA_PATH / "Users.json", resource_path]
    backups = {path: path.read_bytes() for path in touched_paths}

    try:
        for key, (username, password, role) in users.items():
            user_ids[key] = Users.createUser(Users.AdminPassword, username, password, role)

        for key, owner in (("player", "player"), ("other", "other"), ("gm", "gm")):
            username, password, _ = users[owner]
            character_ids[key] = Characters.createCharacter(
                user_ids[owner], username, password, f"{test_tag}_{key}", f"{test_tag} {key}"
            )

        gm_username, gm_password, _ = users["gm"]
        player_username, player_password, _ = users["player"]
        other_username, other_password, _ = users["other"]
        manager_credentials = (user_ids["gm"], gm_username, gm_password)
        player_credentials = (user_ids["player"], player_username, player_password)
        other_credentials = (user_ids["other"], other_username, other_password)

        _expect_error(
            PermissionError,
            lambda: create_resource(*player_credentials, "forbidden", "forbidden"),
            "a player cannot create a global resource",
        )
        _expect_error(
            PermissionError,
            lambda: create_resource(user_ids["gm"], gm_username, "wrong_password", "forbidden", "forbidden"),
            "wrong credentials cannot create a global resource",
        )

        resource_ids.append(create_resource(*manager_credentials, f"{test_tag} gm", "GM resource"))
        resource_ids.append(create_resource(*manager_credentials, f"{test_tag} manager 2", "Manager resource 2"))
        stored = load_json(resource_path)
        for resource_id in resource_ids:
            assert resource_id.startswith(resource_prefix)
            assert "owner" not in stored[resource_id], "global resources must not have a user owner"

        edit_known(*manager_credentials, character_ids["player"], resource_ids[:1])
        edit_known(*manager_credentials, character_ids["other"], resource_ids[:1])

        assign_resource(*manager_credentials, resource_ids[0], character_ids["other"])
        assign_resource(*manager_credentials, resource_ids[1], character_ids["gm"])
        remove_resource(*manager_credentials, resource_ids[1], character_ids["gm"])
        _expect_error(
            PermissionError,
            lambda: assign_resource(*other_credentials, resource_ids[1], character_ids["player"]),
            "a player cannot modify another player's character",
        )
        assign_resource(*player_credentials, resource_ids[0], character_ids["player"])
        _expect_error(
            ValueError,
            lambda: assign_resource(*player_credentials, resource_ids[0], character_ids["player"]),
            "a resource cannot be activated twice on one character",
        )
        _expect_error(
            PermissionError,
            lambda: assign_resource(*player_credentials, resource_ids[1], character_ids["player"]),
            "a player cannot activate an unknown resource",
        )

        player_folder = user_ids["player"].removeprefix("User_")
        stat_sheet = load_json(DATA_PATH / "User" / player_folder / f"{test_tag}_player" / "StatSheet.json")
        assert stat_sheet[row_name]["rows"] == [{"ID": resource_ids[0]}]
        _expect_error(
            ValueError,
            lambda: delete_resource_fn(*manager_credentials, resource_ids[0]),
            "an active resource cannot be deleted",
        )
        _expect_error(
            PermissionError,
            lambda: delete_resource_fn(*player_credentials, resource_ids[1]),
            "a player cannot delete a global resource",
        )

        remove_resource(*player_credentials, resource_ids[0], character_ids["player"])
        remove_resource(*manager_credentials, resource_ids[0], character_ids["other"])
        _expect_error(
            ValueError,
            lambda: remove_resource(*player_credentials, resource_ids[0], character_ids["player"]),
            "a resource cannot be removed twice",
        )
        _expect_error(
            ValueError,
            lambda: delete_resource_fn(*manager_credentials, resource_ids[0]),
            "a known resource cannot be deleted",
        )
        edit_known(*manager_credentials, character_ids["player"], [])
        edit_known(*manager_credentials, character_ids["other"], [])

        delete_resource_fn(*manager_credentials, resource_ids[0])
        delete_resource_fn(*manager_credentials, resource_ids[1])
        assert all(resource_id not in load_json(resource_path) for resource_id in resource_ids)
        _expect_error(
            ValueError,
            lambda: delete_resource_fn(*manager_credentials, resource_ids[0]),
            "a deleted resource cannot be deleted again",
        )
    finally:
        for user_id in user_ids.values():
            try:
                Users.deleteUser(Users.AdminPassword, user_id)
            except Exception:
                user_path = DATA_PATH / "User" / user_id.removeprefix("User_")
                if user_path.exists():
                    shutil.rmtree(user_path)
        for path, content in backups.items():
            path.write_bytes(content)