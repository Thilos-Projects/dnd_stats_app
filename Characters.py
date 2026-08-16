"""Character management: creation, deletion, listing, and known-character curation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import Users
import validate_data
import _global_resources

DATA_PATH = Path(__file__).parent / "data"
USER_ROOT = DATA_PATH / "User"
STAT_SHEET_TEMPLATE_PATH = DATA_PATH / "stat_sheet_template.json"
INVENTORY_TEMPLATE_PATH = DATA_PATH / "inventory_template.json"
MANAGER_ROLES = {"gm"}
TEST_ADMIN_PASSWORD = "1234"  # matches Users.AdminPassword, needed to create/delete test users


def _load_json(path: Path) -> Any:
    return _global_resources.load_json(path)

def _save_json(path: Path, data: Any) -> None:
    _global_resources.save_json(path, data)

def _require_login(user_id: str, username: str, password_hash: str) -> str:
    """Validate credentials and return the caller's role (lower-case)."""
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")
    role = Users.getUserRole(user_id)
    if role is None:
        raise PermissionError("Unknown user")
    return role.lower()

def _user_folder_name(user_id: str) -> str:
    return user_id.removeprefix("User_")

def _character_id(folder_name: str) -> str:
    return f"Charakter_{folder_name}"


def _validate_folder_name(folder_name: str) -> None:
    if not isinstance(folder_name, str) or not folder_name.strip():
        raise ValueError("folder_name must be a non-empty string")
    if folder_name in {".", ".."} or Path(folder_name).name != folder_name:
        raise ValueError("folder_name must be a single path component")

def _characters_in_user_folder(user_path: Path) -> list[str]:
    characters = []
    for folder in user_path.iterdir():
        character_file = folder / "Character.json"
        if folder.is_dir() and character_file.exists():
            characters.append(_load_json(character_file)["ID"])
    return characters

def _find_character(character_id: str) -> tuple[Path, str, dict[str, Any]]:
    """Return (character_folder, owning user folder name, character data) for a character id."""
    return _global_resources.find_character(character_id)

def createCharacter(
    user_id: str,
    username: str,
    password_hash: str,
    folder_name: str,
    display_name: str,
) -> str:
    """Create a new character in the caller's own user folder. Any validated user may do this."""
    _require_login(user_id, username, password_hash)

    _validate_folder_name(folder_name)
    if not isinstance(display_name, str) or not display_name.strip():
        raise ValueError("display_name must be a non-empty string")

    user_path = USER_ROOT / _user_folder_name(user_id)
    if not user_path.exists():
        raise ValueError(f"User folder for {user_id} does not exist")

    character_path = user_path / folder_name
    if character_path.exists():
        raise ValueError(f"Character folder {folder_name} already exists for {user_id}")

    character_path.mkdir(parents=True)
    (character_path / "documents").mkdir(parents=True, exist_ok=True)

    character_data = {
        "ID": _character_id(folder_name),
        "display_name": display_name,
        "known_Charakters": [],
        "known_Skills": [],
        "known_SpellEffects": [],
        "known_StatusEffects": [],
    }
    _save_json(character_path / "Character.json", character_data)
    _save_json(character_path / "Inventory.json", _load_json(INVENTORY_TEMPLATE_PATH))
    _save_json(character_path / "StatSheet.json", _load_json(STAT_SHEET_TEMPLATE_PATH))

    return character_data["ID"]

def deleteCharacter(user_id: str, username: str, password_hash: str, character_id: str) -> None:
    """Delete a character. Owners may delete their own characters; GM may delete any."""
    role = _require_login(user_id, username, password_hash)
    character_path, owner_folder, _ = _find_character(character_id)

    if owner_folder != _user_folder_name(user_id) and role not in MANAGER_ROLES:
        raise PermissionError("Only the owning user or a GM may delete this character")

    shutil.rmtree(character_path)

def listOwnCharacters(user_id: str, username: str, password_hash: str) -> list[str]:
    """List every character ID in the caller's own user folder."""
    _require_login(user_id, username, password_hash)
    user_path = USER_ROOT / _user_folder_name(user_id)
    if not user_path.exists():
        return []
    return _characters_in_user_folder(user_path)

def listUserCharacters(
    user_id: str, username: str, password_hash: str, target_user_id: str
) -> list[str]:
    """List character IDs of another user's folder. Requires GM unless the target is the caller."""
    role = _require_login(user_id, username, password_hash)
    if target_user_id != user_id and role not in MANAGER_ROLES:
        raise PermissionError("Only GM may view another user's characters")

    if not Users.hasUser(target_user_id):
        raise ValueError(f"User {target_user_id} does not exist")

    user_path = USER_ROOT / _user_folder_name(target_user_id)
    if not user_path.exists():
        return []
    return _characters_in_user_folder(user_path)

def listAllCharacters(user_id: str, username: str, password_hash: str) -> list[str]:
    """List every character ID across all users. Requires GM role."""
    role = _require_login(user_id, username, password_hash)
    if role not in MANAGER_ROLES:
        raise PermissionError("Only GM may list all characters")

    characters: list[str] = []
    for user_path in USER_ROOT.iterdir():
        if user_path.is_dir():
            characters.extend(_characters_in_user_folder(user_path))
    return characters

def _get_known_list(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    field_name: str,
) -> list[str]:
    """Read a character's known_* list. Requires GM, or the character to belong to the caller."""
    role = _require_login(user_id, username, password_hash)
    character_path, owner_folder, character_data = _find_character(character_id)

    if owner_folder != _user_folder_name(user_id) and role not in MANAGER_ROLES:
        raise PermissionError(f"Only the owning user or a GM may view {field_name}")

    return list(character_data.get(field_name, []))


def getKnownCharacters(user_id: str, username: str, password_hash: str, character_id: str) -> list[str]:
    """Return a character's known_Charakters list. Requires GM, or ownership of the character."""
    return _get_known_list(user_id, username, password_hash, character_id, "known_Charakters")


def getKnownSkills(user_id: str, username: str, password_hash: str, character_id: str) -> list[str]:
    """Return a character's known_Skills list. Requires GM, or ownership of the character."""
    return _get_known_list(user_id, username, password_hash, character_id, "known_Skills")


def getKnownSpellEffects(user_id: str, username: str, password_hash: str, character_id: str) -> list[str]:
    """Return a character's known_SpellEffects list. Requires GM, or ownership of the character."""
    return _get_known_list(user_id, username, password_hash, character_id, "known_SpellEffects")


def getKnownStatusEffects(user_id: str, username: str, password_hash: str, character_id: str) -> list[str]:
    """Return a character's known_StatusEffects list. Requires GM, or ownership of the character."""
    return _get_known_list(user_id, username, password_hash, character_id, "known_StatusEffects")


def _edit_known_list(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    field_name: str,
    known_ids: list[str],
    *,
    json_file_name: str | None = None,
    id_prefix: str | None = None,
    validator: callable | None = None,
) -> None:
    """Replace a character's known_* list using GM rights."""
    role = _require_login(user_id, username, password_hash)
    if role not in MANAGER_ROLES:
        raise PermissionError(f"Only GM may edit {field_name}")

    if not isinstance(known_ids, list) or not all(isinstance(item, str) for item in known_ids):
        raise ValueError(f"{field_name} must be a list of strings")

    character_path, _, character_data = _find_character(character_id)
    for known_id in known_ids:
        if validator is not None:
            validator(known_id)
        elif json_file_name and id_prefix:
            global_data = _load_json(DATA_PATH / "Global" / json_file_name)
            if known_id not in global_data:
                raise ValueError(f"{field_name} entry {known_id} does not exist in {json_file_name}")
            if not known_id.startswith(id_prefix):
                raise ValueError(f"{field_name} entry {known_id} does not start with '{id_prefix}'")
        else:
            _find_character(known_id)

    character_data[field_name] = known_ids
    _save_json(character_path / "Character.json", character_data)


def editKnownCharacters(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    known_characters: list[str],
) -> None:
    """Replace a character's known_Charakters list. Requires GM role."""
    _edit_known_list(
        user_id,
        username,
        password_hash,
        character_id,
        "known_Charakters",
        known_characters,
        validator=lambda known_id: _find_character(known_id),
    )


def editKnownSkills(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    known_skills: list[str],
) -> None:
    """Replace a character's known_Skills list. Requires GM role."""
    _edit_known_list(
        user_id,
        username,
        password_hash,
        character_id,
        "known_Skills",
        known_skills,
        json_file_name="Skills.json",
        id_prefix="Skill_",
    )


def editKnownSpellEffects(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    known_spell_effects: list[str],
) -> None:
    """Replace a character's known_SpellEffects list. Requires GM role."""
    _edit_known_list(
        user_id,
        username,
        password_hash,
        character_id,
        "known_SpellEffects",
        known_spell_effects,
        json_file_name="SpellEffects.json",
        id_prefix="SpellEffect_",
    )


def editKnownStatusEffects(
    user_id: str,
    username: str,
    password_hash: str,
    character_id: str,
    known_status_effects: list[str],
) -> None:
    """Replace a character's known_StatusEffects list. Requires GM role."""
    _edit_known_list(
        user_id,
        username,
        password_hash,
        character_id,
        "known_StatusEffects",
        known_status_effects,
        json_file_name="StatusEffekts.json",
        id_prefix="StatusEffekt_",
    )


def main() -> None:
    """Create a GM and a Player user with characters, exercise every access path, then clean up."""
    users_file_path = DATA_PATH / "Users.json"
    users_file_backup = users_file_path.read_bytes()
    gm_user_id = Users.createUser(TEST_ADMIN_PASSWORD, "test_gm", "gm_password_hash", "gm")
    player_user_id = Users.createUser(TEST_ADMIN_PASSWORD, "test_player", "player_password_hash", "player")
    created_characters: list[tuple[str, str, str, str]] = []  # (owner_id, username, pw, char_id)

    try:
        gm_char_id = createCharacter(
            gm_user_id, "test_gm", "gm_password_hash", "gm_hero_0", "GM Held"
        )
        created_characters.append((gm_user_id, "test_gm", "gm_password_hash", gm_char_id))

        player_char_id = createCharacter(
            player_user_id, "test_player", "player_password_hash", "player_hero_0", "Spieler Held"
        )
        created_characters.append((player_user_id, "test_player", "player_password_hash", player_char_id))

        player_char_id_2 = createCharacter(
            player_user_id, "test_player", "player_password_hash", "player_hero_1", "Spieler Held Zwei"
        )
        created_characters.append((player_user_id, "test_player", "player_password_hash", player_char_id_2))

        # Data integrity check via the provided validation script.
        try:
            validate_data.main()
        except Exception as e:
            print(f"Data integrity validation failed unexpectedly: {e}")

        # --- Access variant checks ---

        # Wrong credentials must never grant access.
        try:
            listOwnCharacters(player_user_id, "test_player", "wrong_password_hash")
            print("Player logged in with a wrong password (this should not happen).")
        except PermissionError:
            pass

        # A player can list their own characters.
        try:
            own = listOwnCharacters(player_user_id, "test_player", "player_password_hash")
            if player_char_id not in own or player_char_id_2 not in own:
                print("Player's own character list is missing expected characters (this should not happen).")
        except PermissionError as e:
            print(f"Player could not list their own characters (this should not happen): {e}")

        # A GM can list their own characters.
        try:
            gm_own = listOwnCharacters(gm_user_id, "test_gm", "gm_password_hash")
            if gm_char_id not in gm_own:
                print("GM's own character list is missing the expected character (this should not happen).")
        except PermissionError as e:
            print(f"GM could not list their own characters (this should not happen): {e}")

        # A player must not be able to list all characters.
        try:
            listAllCharacters(player_user_id, "test_player", "player_password_hash")
            print("Player was able to list all characters (this should not happen).")
        except PermissionError:
            pass

        # A GM must be able to list all characters.
        try:
            all_chars = listAllCharacters(gm_user_id, "test_gm", "gm_password_hash")
            if gm_char_id not in all_chars or player_char_id not in all_chars:
                print("GM's all-characters list is missing expected characters (this should not happen).")
        except PermissionError as e:
            print(f"GM could not list all characters (this should not happen): {e}")

        # A player must not be able to view another user's character list.
        try:
            listUserCharacters(player_user_id, "test_player", "player_password_hash", gm_user_id)
            print("Player was able to view another user's characters (this should not happen).")
        except PermissionError:
            pass

        # A GM must be able to view another user's character list.
        try:
            player_chars_via_gm = listUserCharacters(
                gm_user_id, "test_gm", "gm_password_hash", player_user_id
            )
            if player_char_id not in player_chars_via_gm:
                print("GM could not see the player's characters correctly (this should not happen).")
        except PermissionError as e:
            print(f"GM could not view the player's characters (this should not happen): {e}")

        # A player must not be able to edit known_Charakters, even their own character.
        try:
            editKnownCharacters(
                player_user_id, "test_player", "player_password_hash", player_char_id, [gm_char_id]
            )
            print("Player was able to edit known_Charakters (this should not happen).")
        except PermissionError:
            pass

        # A GM must be able to edit known_Charakters, including on another user's character.
        try:
            editKnownCharacters(
                gm_user_id, "test_gm", "gm_password_hash", player_char_id, [gm_char_id]
            )
            _, _, updated_character = _find_character(player_char_id)
            if updated_character["known_Charakters"] != [gm_char_id]:
                print("GM's known_Charakters edit was not applied correctly (this should not happen).")
        except PermissionError as e:
            print(f"GM could not edit known_Charakters (this should not happen): {e}")

        # Re-validate integrity now that a known_Charakters cross-reference exists.
        try:
            validate_data.main()
        except Exception as e:
            print(f"Data integrity validation failed unexpectedly after editing known_Charakters: {e}")

        # A player can read their own known_* lists.
        try:
            known = getKnownCharacters(player_user_id, "test_player", "player_password_hash", player_char_id)
            if known != [gm_char_id]:
                print("Player's known_Charakters getter returned unexpected data (this should not happen).")
        except PermissionError as e:
            print(f"Player could not read their own known_Charakters (this should not happen): {e}")

        # A player must not be able to read another user's known_* lists.
        try:
            getKnownCharacters(player_user_id, "test_player", "player_password_hash", gm_char_id)
            print("Player was able to read another user's known_Charakters (this should not happen).")
        except PermissionError:
            pass

        # A GM must be able to read any character's known_* lists.
        try:
            gm_view = getKnownCharacters(gm_user_id, "test_gm", "gm_password_hash", player_char_id)
            if gm_view != [gm_char_id]:
                print("GM's known_Charakters getter returned unexpected data (this should not happen).")
        except PermissionError as e:
            print(f"GM could not read the player's known_Charakters (this should not happen): {e}")

        # The other known_* getters follow the same access rule; spot-check one of them.
        try:
            getKnownSkills(player_user_id, "test_player", "player_password_hash", gm_char_id)
            print("Player was able to read another user's known_Skills (this should not happen).")
        except PermissionError:
            pass

        # Clear the reference before deletion so no dangling known_Charakters remain.
        editKnownCharacters(gm_user_id, "test_gm", "gm_password_hash", player_char_id, [])

        # A player must not be able to delete another user's character.
        try:
            deleteCharacter(player_user_id, "test_player", "player_password_hash", gm_char_id)
            print("Player was able to delete another user's character (this should not happen).")
        except PermissionError:
            pass

        # A player can delete their own character.
        try:
            deleteCharacter(player_user_id, "test_player", "player_password_hash", player_char_id_2)
            created_characters.remove((player_user_id, "test_player", "player_password_hash", player_char_id_2))
        except PermissionError as e:
            print(f"Player could not delete their own character (this should not happen): {e}")

        # A GM can delete another user's character.
        try:
            deleteCharacter(gm_user_id, "test_gm", "gm_password_hash", player_char_id)
            created_characters.remove((player_user_id, "test_player", "player_password_hash", player_char_id))
        except PermissionError as e:
            print(f"GM could not delete the player's character (this should not happen): {e}")

        print("Character management test completed.")
    finally:
        for owner_id, username, password_hash, character_id in created_characters:
            try:
                deleteCharacter(owner_id, username, password_hash, character_id)
            except ValueError:
                pass  # already deleted during the test
        Users.deleteUser(TEST_ADMIN_PASSWORD, player_user_id)
        Users.deleteUser(TEST_ADMIN_PASSWORD, gm_user_id)
        users_file_path.write_bytes(users_file_backup)

if __name__ == "__main__":
    main()
