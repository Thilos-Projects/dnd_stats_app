"""Manage global items and their assignment to character inventories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import Users
import Characters
import validate_data
import _global_resources

DATA_PATH = Path(__file__).parent / "data"
ITEMS_PATH = DATA_PATH / "Global" / "Items.json"
STAT_BONUS_FIELDS = (
    "Mut",
    "Klugheit",
    "Intuition",
    "Charisma",
    "Fingerfertigkeit",
    "Gewandheit",
    "Konstitution",
    "Körperkraft",
    "MagieSpeicher",
    "MagieRegeneration",
)


def _load_json(path: Path) -> Any:
    return _global_resources.load_json(path)

def _save_json(path: Path, data: Any) -> None:
    _global_resources.save_json(path, data)

def _require_manager(user_id: str, username: str, password_hash: str) -> None:
    _global_resources.require_manager(user_id, username, password_hash, "items")

def _require_manager_or_character_owner(
    user_id: str,
    username: str,
    password_hash: str,
    character_path: Path,
) -> None:
    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")

    role = Users.getUserRole(user_id)
    if role is not None and role.lower() == "gm":
        return
    if character_path.parent.name != user_id.removeprefix("User_"):
        raise PermissionError("Only the character owner or a GM may manage equipment")

def _next_item_id(items: dict[str, Any]) -> str:
    used_numbers = [
        int(item_id.removeprefix("Item_"))
        for item_id in items
        if item_id.startswith("Item_") and item_id.removeprefix("Item_").isdigit()
    ]
    return f"Item_{max(used_numbers, default=0) + 1}"

def _normalise_stat_bonus(stat_bonus: dict[str, int] | None) -> dict[str, int]:
    bonuses = {field: 0 for field in STAT_BONUS_FIELDS}
    if stat_bonus is None:
        return bonuses
    if set(stat_bonus) != set(STAT_BONUS_FIELDS):
        raise ValueError(f"stat_bonus must contain exactly: {', '.join(STAT_BONUS_FIELDS)}")
    for field, value in stat_bonus.items():
        if isinstance(value, bool) or not isinstance(value, int) or not -10 <= value <= 10:
            raise ValueError(f"Stat bonus {field} must be an integer between -10 and 10")
        bonuses[field] = value
    return bonuses

def _find_character(character_id: str) -> tuple[Path, dict[str, Any]]:
    character_path, _, character = _global_resources.find_character(character_id)
    return character_path, character

def _load_item(items: dict[str, Any], item_id: str) -> dict[str, Any]:
    if item_id not in items:
        raise ValueError(f"Item {item_id} does not exist")
    return items[item_id]

def createItem(
    user_id: str,
    username: str,
    password_hash: str,
    name: str,
    description: str,
    stat_bonus: dict[str, int] | None = None,
) -> str:
    """Create an unassigned item and return its generated item ID."""
    _require_manager(user_id, username, password_hash)
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Item name must be a non-empty string")
    if not isinstance(description, str):
        raise ValueError("Item description must be a string")

    items = _load_json(ITEMS_PATH)
    item_id = _next_item_id(items)
    items[item_id] = {
        "name": name,
        "description": description,
        "owner": None,
        "equipped": False,
        "stat_bonus": _normalise_stat_bonus(stat_bonus),
    }
    _save_json(ITEMS_PATH, items)
    return item_id

def deleteItem(user_id: str, username: str, password_hash: str, item_id: str) -> None:
    """Delete an unassigned item. Assigned items must be removed first."""
    _require_manager(user_id, username, password_hash)
    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] is not None:
        raise ValueError("Remove the item from its character before deleting it")
    del items[item_id]
    _save_json(ITEMS_PATH, items)

def assignItemToCharacter(
    user_id: str, username: str, password_hash: str, item_id: str, character_id: str
) -> None:
    """Assign an unowned item to a character inventory."""
    _require_manager(user_id, username, password_hash)
    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] is not None:
        raise ValueError(f"Item {item_id} is already assigned to {item['owner']}")

    character_path, _ = _find_character(character_id)
    inventory_path = character_path / "Inventory.json"
    inventory = _load_json(inventory_path)
    if item_id in inventory:
        raise ValueError(f"Item {item_id} is already in this inventory")

    inventory.append(item_id)
    item["owner"] = character_id
    _save_json(inventory_path, inventory)
    _save_json(ITEMS_PATH, items)

def equipItem(
    user_id: str, username: str, password_hash: str, item_id: str, character_id: str
) -> None:
    """Mark an assigned item as equipped and add it to the character stat sheet."""
    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] != character_id:
        raise ValueError(f"Item {item_id} is not assigned to {character_id}")

    character_path, _ = _find_character(character_id)
    _require_manager_or_character_owner(user_id, username, password_hash, character_path)
    inventory = _load_json(character_path / "Inventory.json")
    if item_id not in inventory:
        raise ValueError(f"Item {item_id} is missing from the character inventory")

    stat_sheet_path = character_path / "StatSheet.json"
    stat_sheet = _load_json(stat_sheet_path)
    rows = stat_sheet["equipped_items"]["rows"]
    if not any(row.get("ID") == item_id for row in rows):
        rows.append({"ID": item_id})
    item["equipped"] = True
    _save_json(stat_sheet_path, stat_sheet)
    _save_json(ITEMS_PATH, items)

def unequipItem(
    user_id: str, username: str, password_hash: str, item_id: str, character_id: str
) -> None:
    """Remove an item from the character stat sheet and clear its equipped flag."""
    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] != character_id:
        raise ValueError(f"Item {item_id} is not assigned to {character_id}")

    character_path, _ = _find_character(character_id)
    _require_manager_or_character_owner(user_id, username, password_hash, character_path)
    stat_sheet_path = character_path / "StatSheet.json"
    stat_sheet = _load_json(stat_sheet_path)
    rows = stat_sheet["equipped_items"]["rows"]
    stat_sheet["equipped_items"]["rows"] = [row for row in rows if row.get("ID") != item_id]
    item["equipped"] = False
    _save_json(stat_sheet_path, stat_sheet)
    _save_json(ITEMS_PATH, items)

def removeItemFromCharacter(
    user_id: str, username: str, password_hash: str, item_id: str, character_id: str
) -> None:
    """Remove an un-equipped item from a character inventory."""
    _require_manager(user_id, username, password_hash)
    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] != character_id:
        raise ValueError(f"Item {item_id} is not assigned to {character_id}")
    if item["equipped"]:
        raise ValueError("Unequip the item before removing it from the character")

    character_path, _ = _find_character(character_id)
    inventory_path = character_path / "Inventory.json"
    inventory = _load_json(inventory_path)
    if item_id not in inventory:
        raise ValueError(f"Item {item_id} is missing from the character inventory")

    inventory.remove(item_id)
    item["owner"] = None
    _save_json(inventory_path, inventory)
    _save_json(ITEMS_PATH, items)

def moveItemBetweenCharacters(
    user_id: str,
    username: str,
    password_hash: str,
    item_id: str,
    from_character_id: str,
    to_character_id: str,
) -> None:
    """Move an un-equipped item when source character A knows target B."""
    if from_character_id == to_character_id:
        raise ValueError("Source and target character must be different")

    items = _load_json(ITEMS_PATH)
    item = _load_item(items, item_id)
    if item["owner"] != from_character_id:
        raise ValueError(f"Item {item_id} is not assigned to {from_character_id}")
    if item["equipped"]:
        raise ValueError("Unequip the item before moving it to another character")

    source_path, source_character = _find_character(from_character_id)
    target_path, _ = _find_character(to_character_id)
    if to_character_id not in source_character.get("known_Charakters", []):
        raise PermissionError("The source character does not know the target character")

    if not Users.loginTestUser(user_id, username, password_hash):
        raise PermissionError("Invalid user credentials")
    role = Users.getUserRole(user_id)
    is_manager = role is not None and role.lower() == "gm"
    source_owner_id = f"User_{source_path.parent.name}"
    if not is_manager and user_id != source_owner_id:
        raise PermissionError("Only the source character owner or a GM may move the item")

    source_inventory_path = source_path / "Inventory.json"
    target_inventory_path = target_path / "Inventory.json"
    source_inventory = _load_json(source_inventory_path)
    target_inventory = _load_json(target_inventory_path)
    if item_id not in source_inventory:
        raise ValueError(f"Item {item_id} is missing from the source inventory")
    if item_id in target_inventory:
        raise ValueError(f"Item {item_id} is already in the target inventory")

    source_inventory.remove(item_id)
    target_inventory.append(item_id)
    item["owner"] = to_character_id
    _save_json(source_inventory_path, source_inventory)
    _save_json(target_inventory_path, target_inventory)
    _save_json(ITEMS_PATH, items)

def _expect_error(expected: type[Exception], action: Any, description: str) -> None:
    """Assert that one test action rejects the requested operation."""
    try:
        action()
    except expected:
        return
    raise AssertionError(f"Expected {expected.__name__}: {description}")


def main() -> None:
    """Exercise every public item operation with multiple users and characters."""
    print("[1/7] Create test users and characters")
    users = {
        "gm": ("items_test_gm", "gm_password", "gm"),
        "alice": ("items_test_alice", "alice_password", "player"),
        "bob": ("items_test_bob", "bob_password", "player"),
    }
    user_ids: dict[str, str] = {}
    characters: dict[str, str] = {}
    item_ids: list[str] = []

    try:
        for key, (username, password_hash, role) in users.items():
            user_ids[key] = Users.createUser(Users.AdminPassword, username, password_hash, role)

        character_specs = {
            "gm_a": ("gm", "items_test_gm_a", "GM Character A"),
            "gm_b": ("gm", "items_test_gm_b", "GM Character B"),
            "alice_a": ("alice", "items_test_alice_a", "Alice Character A"),
            "alice_b": ("alice", "items_test_alice_b", "Alice Character B"),
            "bob_a": ("bob", "items_test_bob_a", "Bob Character A"),
            "bob_b": ("bob", "items_test_bob_b", "Bob Character B"),
        }
        for key, (owner, folder_name, display_name) in character_specs.items():
            username, password_hash, _ = users[owner]
            characters[key] = Characters.createCharacter(
                user_ids[owner], username, password_hash, folder_name, display_name
            )

        print("[2/7] Configure known-character relationships")
        gm_username, gm_password, _ = users["gm"]
        Characters.editKnownCharacters(
            user_ids["gm"], gm_username, gm_password, characters["gm_a"], [characters["gm_b"]]
        )
        Characters.editKnownCharacters(
            user_ids["gm"], gm_username, gm_password, characters["alice_a"], [characters["bob_a"]]
        )
        Characters.editKnownCharacters(
            user_ids["gm"], gm_username, gm_password, characters["bob_a"], [characters["alice_a"]]
        )

        print("[3/7] Test createItem and create permissions")
        alice_username, alice_password, _ = users["alice"]
        item_a = createItem(
            user_ids["gm"], gm_username, gm_password, "Alice sword", "Sword for Alice"
        )
        item_ids.append(item_a)
        item_b = createItem(
            user_ids["gm"], gm_username, gm_password, "Bob shield", "Shield for Bob"
        )
        item_ids.append(item_b)
        item_c = createItem(
            user_ids["gm"], gm_username, gm_password, "Transfer ring", "Ring for transfer tests"
        )
        item_ids.append(item_c)
        item_delete = createItem(
            user_ids["gm"], gm_username, gm_password, "Delete test", "Temporary item"
        )
        item_ids.append(item_delete)
        _expect_error(
            PermissionError,
            lambda: createItem(
                user_ids["alice"], alice_username, alice_password, "Forbidden", "Not allowed"
            ),
            "a player cannot create items",
        )
        _expect_error(
            PermissionError,
            lambda: createItem(
                user_ids["gm"], gm_username, "wrong_password", "Forbidden", "Not allowed"
            ),
            "invalid credentials cannot create items",
        )
        _expect_error(
            ValueError,
            lambda: createItem(user_ids["gm"], gm_username, gm_password, "", "Invalid name"),
            "an item needs a name",
        )

        print("[4/7] Test assignItemToCharacter and assigned-item restrictions")
        assignItemToCharacter(
            user_ids["gm"], gm_username, gm_password, item_a, characters["alice_a"]
        )
        assignItemToCharacter(
            user_ids["gm"], gm_username, gm_password, item_b, characters["bob_a"]
        )
        assignItemToCharacter(
            user_ids["gm"], gm_username, gm_password, item_c, characters["alice_a"]
        )
        _expect_error(
            PermissionError,
            lambda: assignItemToCharacter(
                user_ids["alice"], alice_username, alice_password, item_delete, characters["alice_b"]
            ),
            "a player cannot assign an item",
        )
        _expect_error(
            ValueError,
            lambda: assignItemToCharacter(
                user_ids["gm"], gm_username, gm_password, item_a, characters["alice_b"]
            ),
            "an assigned item cannot be assigned a second time",
        )
        _expect_error(
            ValueError,
            lambda: deleteItem(user_ids["gm"], gm_username, gm_password, item_a),
            "an assigned item cannot be deleted",
        )

        print("[5/7] Test equipItem, unequipItem, and removeItemFromCharacter")
        equipItem(user_ids["alice"], alice_username, alice_password, item_a, characters["alice_a"])
        equipItem(user_ids["alice"], alice_username, alice_password, item_a, characters["alice_a"])
        _expect_error(
            PermissionError,
            lambda: equipItem(
                user_ids["bob"], users["bob"][0], users["bob"][1], item_a, characters["alice_a"]
            ),
            "another player cannot equip Alice's item",
        )
        _expect_error(
            ValueError,
            lambda: removeItemFromCharacter(
                user_ids["gm"], gm_username, gm_password, item_a, characters["alice_a"]
            ),
            "an equipped item cannot be removed",
        )
        unequipItem(user_ids["gm"], gm_username, gm_password, item_a, characters["alice_a"])
        equipItem(user_ids["gm"], gm_username, gm_password, item_b, characters["bob_a"])
        unequipItem(user_ids["bob"], users["bob"][0], users["bob"][1], item_b, characters["bob_a"])
        _expect_error(
            PermissionError,
            lambda: unequipItem(
                user_ids["alice"], alice_username, alice_password, item_b, characters["bob_a"]
            ),
            "another player cannot unequip Bob's item",
        )
        removeItemFromCharacter(
            user_ids["gm"], gm_username, gm_password, item_a, characters["alice_a"]
        )
        removeItemFromCharacter(
            user_ids["gm"], gm_username, gm_password, item_b, characters["bob_a"]
        )

        print("[6/7] Test moveItemBetweenCharacters and known-character rules")
        _expect_error(
            PermissionError,
            lambda: moveItemBetweenCharacters(
                user_ids["alice"], alice_username, "wrong_password", item_c,
                characters["alice_a"], characters["bob_a"]
            ),
            "invalid credentials cannot move items",
        )
        moveItemBetweenCharacters(
            user_ids["alice"], alice_username, alice_password, item_c,
            characters["alice_a"], characters["bob_a"]
        )
        _expect_error(
            PermissionError,
            lambda: moveItemBetweenCharacters(
                user_ids["alice"], alice_username, alice_password, item_c,
                characters["bob_a"], characters["alice_b"]
            ),
            "a transfer requires the source character to know the target",
        )
        moveItemBetweenCharacters(
            user_ids["gm"], gm_username, gm_password, item_c,
            characters["bob_a"], characters["alice_a"]
        )
        equipItem(user_ids["alice"], alice_username, alice_password, item_c, characters["alice_a"])
        _expect_error(
            ValueError,
            lambda: moveItemBetweenCharacters(
                user_ids["gm"], gm_username, gm_password, item_c,
                characters["alice_a"], characters["bob_a"]
            ),
            "an equipped item cannot be moved",
        )
        unequipItem(user_ids["alice"], alice_username, alice_password, item_c, characters["alice_a"])
        removeItemFromCharacter(
            user_ids["gm"], gm_username, gm_password, item_c, characters["alice_a"]
        )

        print("[7/7] Validate data and delete unassigned items")
        deleteItem(user_ids["gm"], gm_username, gm_password, item_delete)
        _expect_error(
            ValueError,
            lambda: deleteItem(user_ids["gm"], gm_username, gm_password, "Item_does_not_exist"),
            "deleting an unknown item fails",
        )
        validate_data.TestForGlobalDocuments(DATA_PATH)
        print("Item management test completed successfully.")
    finally:
        items = _load_json(ITEMS_PATH)
        for item_id in item_ids:
            if item_id not in items:
                continue
            item = items[item_id]
            owner = item.get("owner")
            if owner is not None:
                try:
                    owner_path, _ = _find_character(owner)
                    owner_user_id = f"User_{owner_path.parent.name}"
                    owner_username, owner_password, _ = next(
                        credentials for key, credentials in users.items() if user_ids[key] == owner_user_id
                    )
                    if item.get("equipped"):
                        unequipItem(
                            user_ids["gm"], gm_username, gm_password, item_id, owner
                        )
                    removeItemFromCharacter(
                        user_ids["gm"], gm_username, gm_password, item_id, owner
                    )
                except (ValueError, PermissionError):
                    pass
            if item_id in _load_json(ITEMS_PATH):
                try:
                    deleteItem(user_ids["gm"], gm_username, gm_password, item_id)
                except (ValueError, PermissionError):
                    pass

        for character_id in characters.values():
            try:
                Characters.deleteCharacter(user_ids["gm"], gm_username, gm_password, character_id)
            except ValueError:
                pass
        for user_id in user_ids.values():
            Users.deleteUser(Users.AdminPassword, user_id)


if __name__ == "__main__":
    main()
