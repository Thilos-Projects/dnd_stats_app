"""Manage global status effects and their active assignment to characters."""

from __future__ import annotations

import Skills
import _global_resources

STATUS_EFFECTS_PATH = _global_resources.DATA_PATH / "Global" / "StatusEffekts.json"
RESOURCE_NAME = "StatusEffekt"
RESOURCE_PREFIX = "StatusEffekt_"
ROW_NAME = "active_status_effects"
KNOWN_FIELD = "known_StatusEffects"
EFFECT_STAT_FIELDS = Skills.STAT_FIELDS + ("MagieSpeicher", "MagieRegeneration")


def createStatusEffect(user_id: str, username: str, password_hash: str, name: str, beschreibung: str, default_duration: int = 0, default_time_to_death: int = 0, stat_bonus: dict[str, int] | None = None, talent_bonus: dict[str, int] | None = None) -> str:
    _global_resources.require_manager(user_id, username, password_hash, RESOURCE_NAME)
    if not isinstance(name, str) or not name.strip() or not isinstance(beschreibung, str):
        raise ValueError("name must be non-empty and beschreibung must be a string")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (default_duration, default_time_to_death)):
        raise ValueError("default duration and default time to death must be non-negative integers")
    effects = _global_resources.load_json(STATUS_EFFECTS_PATH)
    effect_id = _global_resources.next_id(effects, RESOURCE_PREFIX)
    effects[effect_id] = {
        "name": name,
        "beschreibung": beschreibung,
        "default duration": default_duration,
        "default time to death": default_time_to_death,
        "stat_bonus": Skills._bonus(stat_bonus, EFFECT_STAT_FIELDS, "stat_bonus"),
        "talent_bonus": Skills._bonus(talent_bonus, Skills.TALENT_FIELDS, "talent_bonus"),
    }
    _global_resources.save_json(STATUS_EFFECTS_PATH, effects)
    return effect_id


def deleteStatusEffect(user_id: str, username: str, password_hash: str, status_effect_id: str) -> None:
    _global_resources.delete_resource(user_id, username, password_hash, status_effect_id, resource_path=STATUS_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD)


def assignStatusEffectToCharacter(user_id: str, username: str, password_hash: str, status_effect_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, status_effect_id, character_id, resource_path=STATUS_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=False)


def removeStatusEffectFromCharacter(user_id: str, username: str, password_hash: str, status_effect_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, status_effect_id, character_id, resource_path=STATUS_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=True)

def listAllStatusEffects(user_id: str, username: str, password_hash: str) -> dict[str, dict]:
    """List all status effects the user can see."""
    _global_resources.require_user(user_id, username, password_hash)
    effects = _global_resources.load_json(STATUS_EFFECTS_PATH)
    role = _global_resources.get_user_role(user_id)
    is_manager = role is not None and role.lower() == "gm"
    if is_manager:
        return effects
    # Filter effects based on what the player knows
    known_effects = _global_resources.get_user_known_resources(user_id, KNOWN_FIELD)
    visible_effects = {effect_id: effect for effect_id, effect in effects.items() if effect_id in known_effects}
    return visible_effects

def main() -> None:
    """Run the complete permission, known-list, row, duplicate, and cleanup test."""
    import Characters

    _global_resources.run_resource_self_test(
        resource_module=__import__(__name__),
        resource_name=RESOURCE_NAME,
        resource_prefix=RESOURCE_PREFIX,
        row_name=ROW_NAME,
        known_field=KNOWN_FIELD,
        create_resource=createStatusEffect,
        edit_known=Characters.editKnownStatusEffects,
        assign_resource=assignStatusEffectToCharacter,
        remove_resource=removeStatusEffectFromCharacter,
        delete_resource_fn=deleteStatusEffect,
    )
    print("Statuseffekts self-test passed")


if __name__ == "__main__":
    main()