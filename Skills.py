"""Manage global skills and their active assignment to characters."""

from __future__ import annotations

import _global_resources

SKILLS_PATH = _global_resources.DATA_PATH / "Global" / "Skills.json"
RESOURCE_NAME = "Skill"
RESOURCE_PREFIX = "Skill_"
ROW_NAME = "learned_abilities"
KNOWN_FIELD = "known_Skills"
STAT_FIELDS = ("Mut", "Klugheit", "Intuition", "Charisma", "Fingerfertigkeit", "Gewandheit", "Konstitution", "Körperkraft")
TALENT_FIELDS = ("Körpertalent", "Geseltschaftstalent", "Naturtalent", "Wissenstalent", "Handwerkstalent")
SKILL_FIELDS = ("Fliegen", "Gaukelei", "Klettern", "Körperbeherschung", "Kraftakt", "Reiten", "Schwimmen", "Selbstbeherschung", "Singen", "Sinnesschärfe", "Tanzen", "Taschendiebstal", "Verbergen", "Zechen", "Bekehren/Überzeugen", "Betöhren", "Einschüchtern", "Etikette", "Gassenwissen", "Menschenkenntniss", "Überreden", "Verkleiden", "Willenskraft", "Fährtensuche", "Fesseln", "Fischen/Angeln", "Orrientierung", "Pflanzenkunde", "Tierkunde", "Wildnisleben", "Brett/Glücksspiel", "Geographie", "Götter/Kulte", "Kriegstkunst", "Magiekunde", "Mechanik", "Rechnen", "Rechtskunde", "Sagen/Legenden", "Sphärenkunde", "Sternkunde", "Alchemie", "Bote/Schiffe", "Fahrzäuge", "Handel", "HeilkundeGifte", "HeilkundeKrankheiten", "HeilkundeSeelen", "HeilkundeWunden", "Holzbearbeitung", "Lebensmittelbearbeitung", "Lederbearbeitung", "Malen/Zeichnen", "Metallbearbeitung", "Musizieren", "Schlösserknacken", "Steinbearbeitung", "Stoffbearbeitung")


def _bonus(values: dict[str, int] | None, fields: tuple[str, ...], name: str) -> dict[str, int]:
    if values is None:
        return {field: 0 for field in fields}
    if set(values) != set(fields):
        raise ValueError(f"{name} must contain exactly: {', '.join(fields)}")
    for field, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int) or not -10 <= value <= 10:
            raise ValueError(f"{name} {field} must be an integer between -10 and 10")
    return dict(values)


def createSkill(
    user_id: str,
    username: str,
    password_hash: str,
    name: str,
    beschreibung: str,
    bedingung_zum_einsetzen: str = "",
    wuerfe_zum_einsetzen: str = "",
    effekt: str = "",
    stat_bonus: dict[str, int] | None = None,
    talent_bonus: dict[str, int] | None = None,
    skill_bonus: dict[str, int] | None = None,
    alters_anstieg: int = 0,
) -> str:
    _global_resources.require_manager(user_id, username, password_hash, RESOURCE_NAME)
    if not isinstance(name, str) or not name.strip() or not isinstance(beschreibung, str):
        raise ValueError("name must be non-empty and beschreibung must be a string")
    if not isinstance(bedingung_zum_einsetzen, str):
        raise ValueError("bedingung_zum_einsetzen must be a string")
    if not isinstance(wuerfe_zum_einsetzen, str):
        raise ValueError("wuerfe_zum_einsetzen must be a string")
    if not isinstance(effekt, str):
        raise ValueError("effekt must be a string")
    if isinstance(alters_anstieg, bool) or not isinstance(alters_anstieg, int):
        raise ValueError("alters_anstieg must be an integer")
    skills = _global_resources.load_json(SKILLS_PATH)
    skill_id = _global_resources.next_id(skills, RESOURCE_PREFIX)
    skills[skill_id] = {
        "name": name,
        "beschreibung": beschreibung,
        "bedingung_zum_einsetzen": bedingung_zum_einsetzen,
        "wuerfe_zum_einsetzen": wuerfe_zum_einsetzen,
        "effekt": effekt,
        "stat_bonus": _bonus(stat_bonus, STAT_FIELDS, "stat_bonus"),
        "talent_bonus": _bonus(talent_bonus, TALENT_FIELDS, "talent_bonus"),
        "skill_bonus": _bonus(skill_bonus, SKILL_FIELDS, "skill_bonus"),
        "alters_anstieg": alters_anstieg,
    }
    _global_resources.save_json(SKILLS_PATH, skills)
    return skill_id


def deleteSkill(user_id: str, username: str, password_hash: str, skill_id: str) -> None:
    _global_resources.delete_resource(user_id, username, password_hash, skill_id, resource_path=SKILLS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD)


def assignSkillToCharacter(user_id: str, username: str, password_hash: str, skill_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, skill_id, character_id, resource_path=SKILLS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=False)


def removeSkillFromCharacter(user_id: str, username: str, password_hash: str, skill_id: str, character_id: str) -> None:
    _global_resources.update_character_rows(user_id, username, password_hash, skill_id, character_id, resource_path=SKILLS_PATH, resource_name=RESOURCE_NAME, row_name=ROW_NAME, known_field=KNOWN_FIELD, remove=True)

def listAllSkills(user_id: str, username: str, password_hash: str) -> dict[str, dict]:
    """List all skills. the USer Can see"""
    #a gm can see all skills, a player can only see the skills that are in his konws_skills list.
    
    _global_resources.require_user(user_id, username, password_hash)
    skills = _global_resources.load_json(SKILLS_PATH)
    role = _global_resources.get_user_role(user_id)
    is_manager = role is not None and role.lower() == "gm"
    if is_manager:
        return skills
    # Filter skills based on what the player knows
    #get User's known skills
    known_skills = _global_resources.get_user_known_resources(user_id, KNOWN_FIELD)
    visible_skills = {skill_id: skill for skill_id, skill in skills.items() if skill_id in known_skills}
    return visible_skills

def main() -> None:
    """Run the complete permission, known-list, row, duplicate, and cleanup test."""
    import Characters

    _global_resources.run_resource_self_test(
        resource_module=__import__(__name__),
        resource_name=RESOURCE_NAME,
        resource_prefix=RESOURCE_PREFIX,
        row_name=ROW_NAME,
        known_field=KNOWN_FIELD,
        create_resource=createSkill,
        edit_known=Characters.editKnownSkills,
        assign_resource=assignSkillToCharacter,
        remove_resource=removeSkillFromCharacter,
        delete_resource_fn=deleteSkill,
    )
    print("Skills self-test passed")


if __name__ == "__main__":
    main()