"""Manage global spell effects and their active assignment to characters."""

from __future__ import annotations

import Skills
import _global_resources

SPELL_EFFECTS_PATH = _global_resources.DATA_PATH / "Global" / "SpellEffects.json"
RESOURCE_NAME = "SpellEffect"
RESOURCE_PREFIX = "SpellEffect_"
ROW_NAME = "active_spell_effects"
KNOWN_FIELD = "known_SpellEffects"
EFFECT_STAT_FIELDS = Skills.STAT_FIELDS + ("MagieSpeicher", "MagieRegeneration")


def createSpellEffect(user_id: str, username: str, password_hash: str, name: str, description: str, default_duration: int = 0, default_time_to_death: int = 0, stat_bonus: dict[str, int] | None = None, talent_bonus: dict[str, int] | None = None, skill_bonus: dict[str, int] | None = None) -> str:
    _global_resources.require_manager(user_id, username, password_hash, RESOURCE_NAME)
    if not isinstance(name, str) or not name.strip() or not isinstance(description, str):
        raise ValueError("name must be non-empty and description must be a string")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (default_duration, default_time_to_death)):
        raise ValueError("default duration and default time to death must be non-negative integers")
    effects = _global_resources.load_json(SPELL_EFFECTS_PATH)
    effect_id = _global_resources.next_id(effects, RESOURCE_PREFIX)
    effects[effect_id] = {
        "name": name,
        "description": description,
        "default duration": default_duration,
        "default time to death": default_time_to_death,
        "stat_bonus": Skills._bonus(stat_bonus, EFFECT_STAT_FIELDS, "stat_bonus"),
        "talent_bonus": Skills._bonus(talent_bonus, Skills.TALENT_FIELDS, "talent_bonus"),
        "skill_bonus": Skills._bonus(skill_bonus, Skills.SKILL_FIELDS, "skill_bonus"),
    }
    _global_resources.save_json(SPELL_EFFECTS_PATH, effects)
    return effect_id


def deleteSpellEffect(user_id: str, username: str, password_hash: str, spell_effect_id: str) -> None:
    _global_resources.delete_resource(user_id, username, password_hash, spell_effect_id, resource_path=SPELL_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD)


def assignSpellEffectToCharacter(user_id: str, username: str, password_hash: str, spell_effect_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, spell_effect_id, character_id, resource_path=SPELL_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=False)


def removeSpellEffectFromCharacter(user_id: str, username: str, password_hash: str, spell_effect_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, spell_effect_id, character_id, resource_path=SPELL_EFFECTS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=True)


def main() -> None:
    """Run the complete permission, known-list, row, duplicate, and cleanup test."""
    import Characters

    _global_resources.run_resource_self_test(
        resource_module=__import__(__name__),
        resource_name=RESOURCE_NAME,
        resource_prefix=RESOURCE_PREFIX,
        row_name=ROW_NAME,
        known_field=KNOWN_FIELD,
        create_resource=createSpellEffect,
        edit_known=Characters.editKnownSpellEffects,
        assign_resource=assignSpellEffectToCharacter,
        remove_resource=removeSpellEffectFromCharacter,
        delete_resource_fn=deleteSpellEffect,
    )
    print("SpellEffects self-test passed")


if __name__ == "__main__":
    main()