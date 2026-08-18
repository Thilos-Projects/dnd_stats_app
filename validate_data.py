
import json
import os
from pathlib import Path

ALLOWED_ROLES = {"gm", "player"}

def TestUsers(executable_path: Path) -> dict:
    #test users.json each entry id hast to start with User_ there has to be a username and a password_hash and a role. The role can bo GM ore Player.
    users_file_path = executable_path / "Users.json"
    if not users_file_path.exists():
        raise FileNotFoundError(f"Users.json not found in {executable_path}")
    with open(users_file_path, "r", encoding="utf-8") as f:
        users_data = json.load(f)
    next_id = users_data.get("next_id")
    if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 1:
        raise ValueError("Users.json must contain a positive integer next_id")
    for user_id, user in users_data.items():
        if user_id == "next_id":
            continue
        if not user_id.startswith("User_"):
            raise ValueError(f"User id {user_id} does not start with 'User_'")
        if "username" not in user:
            raise ValueError(f"User {user_id} does not have a username")
        if "password_hash" not in user:
            raise ValueError(f"User {user_id} does not have a password_hash")
        if "role" not in user:
            raise ValueError(f"User {user_id} does not have a role")
        if user["role"] not in ALLOWED_ROLES:
            raise ValueError(f"User {user_id} has an invalid role {user['role']}")
    return users_data

def TestForStatSheetTemplate(executable_path: Path) -> None:
    #test for stat_sheet_template.json if it exists and is a valid json file
    stat_sheet_template_file_path = executable_path / "stat_sheet_template.json"
    if not stat_sheet_template_file_path.exists():
        raise FileNotFoundError(f"stat_sheet_template.json not found in {executable_path}")
    with open(stat_sheet_template_file_path, "r", encoding="utf-8") as f:
        try:
            json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"stat_sheet_template.json is not a valid json file: {e}")

def TestForGlobalDocuments(executable_path: Path) -> tuple[dict, dict, dict, dict]:
    #look for the Global folder in executable path it has to exist
    #Look for the dokuments Items.json, Skills.json, SpellEffects.json, StatusEffekts.json. They have to be valid json files.
    global_folder_path = executable_path / "Global"
    if not global_folder_path.exists():
        raise FileNotFoundError(f"Global folder not found in {executable_path}")
    for json_file_name in ["Items.json", "Skills.json", "SpellEffects.json", "StatusEffekts.json"]:
        json_file_path = global_folder_path / json_file_name
        if not json_file_path.exists():
            raise FileNotFoundError(f"{json_file_name} not found in {global_folder_path}")
        with open(json_file_path, "r", encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"{json_file_name} is not a valid json file: {e}")

    #test Items.json:
    #each elements Key has to start with "Item_" it has to contain thees fields:
    #"name": "", "description": "", "owner": "", "equipped": false, "stat_bonus": { "Mut": 0, "Klugheit": 0, "Intuition": 0, "Charisma": 0, "Fingerfertigkeit": 0, "Gewandheit": 0, "Konstitution": 0, "Körperkraft": 0, "MagieSpeicher": 0, "MagieRegeneration": 0}
    #the owner hase to be none or a user from users.json.
    #no number in the stat_bonus can be grater than 10 or less than -10.
    items_file_path = global_folder_path / "Items.json"
    with open(items_file_path, "r", encoding="utf-8") as f:
        items_data = json.load(f)
    #users_file_path = executable_path / "Users.json"
    #with open(users_file_path, "r", encoding="utf-8") as f:
    #    users_data = json.load(f)

    fields = ["name", "description", "owner", "equipped", "stat_bonus"]
    inner_fields = ["Mut", "Klugheit", "Intuition", "Charisma", "Fingerfertigkeit", "Gewandheit", "Konstitution", "Körperkraft", "MagieSpeicher", "MagieRegeneration"]
    for item_id, item in items_data.items():
        if not item_id.startswith("Item_"):
            raise ValueError(f"Item id {item_id} does not start with 'Item_'")
        for field in fields:
            if field not in item:
                raise ValueError(f"Item {item_id} does not have the required field '{field}'")
        for inner_field in inner_fields:
            if inner_field not in item["stat_bonus"]:
                raise ValueError(f"Item {item_id} does not have the required stat bonus field '{inner_field}'")
        if item["owner"] is not None and not item["owner"].startswith("Charakter_"):
            raise ValueError(f"Item {item_id} has an invalid owner '{item['owner']}'")
        for stat, value in item["stat_bonus"].items():
            if value < -10 or value > 10:
                raise ValueError(f"Item {item_id} has an invalid stat bonus '{stat}': {value}")

    #test ItemTemplates.json (optional file, same shape as an item without owner/equipped):
    item_templates_file_path = global_folder_path / "ItemTemplates.json"
    if item_templates_file_path.exists():
        with open(item_templates_file_path, "r", encoding="utf-8") as f:
            try:
                item_templates_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"ItemTemplates.json is not a valid json file: {e}")
        for template_id, template in item_templates_data.items():
            if not template_id.startswith("ItemTemplate_"):
                raise ValueError(f"Item template id {template_id} does not start with 'ItemTemplate_'")
            for field in ["name", "description", "stat_bonus"]:
                if field not in template:
                    raise ValueError(f"Item template {template_id} does not have the required field '{field}'")
            for inner_field in inner_fields:
                if inner_field not in template["stat_bonus"]:
                    raise ValueError(f"Item template {template_id} does not have the required stat bonus field '{inner_field}'")
            for stat, value in template["stat_bonus"].items():
                if value < -10 or value > 10:
                    raise ValueError(f"Item template {template_id} has an invalid stat bonus '{stat}': {value}")

    #test Skills.json:
    #each elements Key has to start with "Skill_" it has to contain thees fields:
    fields = ["name", "beschreibung", "stat_bonus", "talent_bonus", "skill_bonus", "alters_anstieg"]
    stat_Fields = ["Mut", "Klugheit", "Intuition", "Charisma", "Fingerfertigkeit", "Gewandheit", "Konstitution", "Körperkraft"]
    talent_Fields = ["Körpertalent", "Geseltschaftstalent", "Naturtalent", "Wissenstalent", "Handwerkstalent"]
    skill_Fields = ["Fliegen", "Gaukelei", "Klettern", "Körperbeherschung", "Kraftakt", "Reiten",
        "Schwimmen", "Selbstbeherschung", "Singen", "Sinnesschärfe", "Tanzen", "Taschendiebstal",
        "Verbergen", "Zechen", "Bekehren/Überzeugen", "Betöhren", "Einschüchtern", "Etikette",
        "Gassenwissen", "Menschenkenntniss", "Überreden", "Verkleiden", "Willenskraft", "Fährtensuche",
        "Fesseln", "Fischen/Angeln", "Orrientierung", "Pflanzenkunde", "Tierkunde", "Wildnisleben",
        "Brett/Glücksspiel", "Geographie", "Götter/Kulte", "Kriegstkunst", "Magiekunde", "Mechanik",
        "Rechnen", "Rechtskunde", "Sagen/Legenden", "Sphärenkunde", "Sternkunde", "Alchemie", "Bote/Schiffe",
        "Fahrzäuge", "Handel", "HeilkundeGifte", "HeilkundeKrankheiten", "HeilkundeSeelen", "HeilkundeWunden", 
        "Holzbearbeitung", "Lebensmittelbearbeitung", "Lederbearbeitung", "Malen/Zeichnen", "Metallbearbeitung", 
        "Musizieren", "Schlösserknacken", "Steinbearbeitung", "Stoffbearbeitung" 
    ]
    #keiner der Werte in den Feldern darf größer als 10 oder kleiner als -10 sein.
    
    skills_file_path = global_folder_path / "Skills.json"
    with open(skills_file_path, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    for skill_id, skill in skills_data.items():
        if not skill_id.startswith("Skill_"):
            raise ValueError(f"Skill id {skill_id} does not start with 'Skill_'")
        for field in fields:
            if field not in skill:
                raise ValueError(f"Skill {skill_id} does not have the required field '{field}'")
        for field in stat_Fields:
            if field not in skill.get("stat_bonus", {}):
                raise ValueError(f"Skill {skill_id} does not have the required stat field '{field}'")
        for field in talent_Fields:
            if field not in skill.get("talent_bonus", {}):
                raise ValueError(f"Skill {skill_id} does not have the required talent field '{field}'")
        for field in skill_Fields:
            if field not in skill.get("skill_bonus", {}):
                raise ValueError(f"Skill {skill_id} does not have the required skill field '{field}'")
        for stat, value in skill.get("stat_bonus", {}).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < -2 or value > 2:
                raise ValueError(f"Skill {skill_id} has an invalid stat bonus '{stat}': {value}")
        for talent, value in skill.get("talent_bonus", {}).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < -2 or value > 2:
                raise ValueError(f"Skill {skill_id} has an invalid talent bonus '{talent}': {value}")
        for skill_name, value in skill.get("skill_bonus", {}).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < -2 or value > 2:
                raise ValueError(f"Skill {skill_id} has an invalid skill bonus '{skill_name}': {value}")
        learning_time = skill["alters_anstieg"]
        if isinstance(learning_time, bool) or not isinstance(learning_time, (int, float)) or learning_time < 0:
            raise ValueError(f"Skill {skill_id} has an invalid alters_anstieg: {learning_time}")

    #spellEffects.json:
    #each elements Key has to start with "SpellEffect_" it has to contain thees fields:
    fields = [
        "name",
        "description",
        "default duration",
        "default time to death",
        "stat_bonus",
        "talent_bonus",
        "skill_bonus"
    ]

    spellEffekt_file_path = global_folder_path / "SpellEffects.json"
    with open(spellEffekt_file_path, "r", encoding="utf-8") as f:
        spelleffekt_data = json.load(f)

    for spelleffekt_id, spelleffekt in spelleffekt_data.items():
        if not spelleffekt_id.startswith("SpellEffect_"):
            raise ValueError(f"SpellEffect id {spelleffekt_id} does not start with 'SpellEffect_'")
        for field in fields:
            if field not in spelleffekt:
                raise ValueError(f"SpellEffect {spelleffekt_id} does not have the required field '{field}'")
        for field in stat_Fields:
            if field not in spelleffekt.get("stat_bonus", {}):
                raise ValueError(f"SpellEffect {spelleffekt_id} does not have the required stat field '{field}'")
        for field in talent_Fields:
            if field not in spelleffekt.get("talent_bonus", {}):
                raise ValueError(f"SpellEffect {spelleffekt_id} does not have the required talent field '{field}'")
        for field in skill_Fields:
            if field not in spelleffekt.get("skill_bonus", {}):
                raise ValueError(f"SpellEffect {spelleffekt_id} does not have the required skill field '{field}'")
        for stat_name, value in spelleffekt.get("stat_bonus", {}).items():
            if value < -10 or value > 10:
                raise ValueError(f"SpellEffect {spelleffekt_id} has an invalid stat bonus '{stat_name}': {value}")
        for talent_name, value in spelleffekt.get("talent_bonus", {}).items():
            if value < -10 or value > 10:
                raise ValueError(f"SpellEffect {spelleffekt_id} has an invalid talent bonus '{talent_name}': {value}")
        for skill_name, value in spelleffekt.get("skill_bonus", {}).items():
            if value < -10 or value > 10:
                raise ValueError(f"SpellEffect {spelleffekt_id} has an invalid skill bonus '{skill_name}': {value}")

    #and the same for StatusEffekts.json
    fields = [
        "name",
        "beschreibung",
        "default duration",
        "default time to death",
        "stat_bonus",
        "talent_bonus"
    ]

    statusEffekt_file_path = global_folder_path / "StatusEffekts.json"
    with open(statusEffekt_file_path, "r", encoding="utf-8") as f:
        statusEffekt_data = json.load(f)

    for statusEffekt_id, statusEffekt in statusEffekt_data.items():
        if not statusEffekt_id.startswith("StatusEffekt_"):
            raise ValueError(f"StatusEffekt id {statusEffekt_id} does not start with 'StatusEffekt_'")
        for field in fields:
            if field not in statusEffekt:
                raise ValueError(f"StatusEffekt {statusEffekt_id} does not have the required field '{field}'")
        for field in stat_Fields:
            if field not in statusEffekt.get("stat_bonus", {}):
                raise ValueError(f"StatusEffekt {statusEffekt_id} does not have the required stat field '{field}'")
        for field in talent_Fields:
            if field not in statusEffekt.get("talent_bonus", {}):
                raise ValueError(f"StatusEffekt {statusEffekt_id} does not have the required talent field '{field}'")
        for time_field in ["default duration", "default time to death"]:
            value = statusEffekt[time_field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"StatusEffekt {statusEffekt_id} has an invalid {time_field}: {value}")
        for stat_name, value in statusEffekt.get("stat_bonus", {}).items():
            if value < -10 or value > 10:
                raise ValueError(f"StatusEffekt {statusEffekt_id} has an invalid stat bonus '{stat_name}': {value}")
        for talent_name, value in statusEffekt.get("talent_bonus", {}).items():
            if value < -10 or value > 10:
                raise ValueError(f"StatusEffekt {statusEffekt_id} has an invalid talent bonus '{talent_name}': {value}")
    return items_data, skills_data, spelleffekt_data, statusEffekt_data

def TestForUserFolder(
    executable_path: Path,
    users_data: dict,
    items_data: dict,
    skills_data: dict,
    spelleffekt_data: dict,
    statusEffekt_data: dict,
) -> None:
    #look in users.json, any kay has to have a folder in the User folder. The name is "User_Default_0" => "Default_0" is the folder name.
    #if the folder Contains folders, the folders have to contain a StatSheet.json a Inventory.json a Charakter.json and a Documents Folder.
    #all .json files have to be vallid Json.

    found_Characters = []
    needed_Characters = []

    userFolder_file_path = executable_path / "User"
    users = [
        key.removeprefix("User_")
        for key in users_data
        if key.startswith("User_")
    ]
    for user in users:
        user_path = userFolder_file_path / user
        if not user_path.exists():
            raise FileNotFoundError(f"User folder {user} not found in {userFolder_file_path}")
        for folder in os.listdir(user_path):
            folder_path = user_path / folder
            if not folder_path.is_dir():
                continue
            stat_sheet_file_path = folder_path / "StatSheet.json"
            inventory_file_path = folder_path / "Inventory.json"
            character_file_path = folder_path / "Character.json"
            documents_folder_path = folder_path / "documents"
            if not stat_sheet_file_path.exists():
                raise FileNotFoundError(f"StatSheet.json not found in {folder_path}")
            if not inventory_file_path.exists():
                raise FileNotFoundError(f"Inventory.json not found in {folder_path}")
            if not character_file_path.exists():
                raise FileNotFoundError(f"Character.json not found in {folder_path}")
            if not documents_folder_path.exists():
                raise FileNotFoundError(f"documents folder not found in {folder_path}")
            for json_file in [stat_sheet_file_path, inventory_file_path, character_file_path]:
                with open(json_file, "r", encoding="utf-8") as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"{json_file} is not a valid json file: {e}")

            #test Charakter.json. the key "ID" has to start with "Charakter_" and the rest of value has to match the folder name. 
            # The key "display_name" has to be a string. 
            # The key "known_Charakters" has to be a list of strings, each string has to start with "Charakter_" each entry has to be a Charakter ID from a Charakter.json in the same user folder. The key "known_Charakters" can be empty. 

            with open(character_file_path, "r", encoding="utf-8") as f:
                character_data = json.load(f)
            if "ID" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have an 'ID' field")
            if not character_data["ID"].startswith("Charakter_"):
                raise ValueError(f"Character.json in {folder_path} has an 'ID' field that does not start with 'Charakter_'")
            if character_data["ID"] != f"Charakter_{folder}":
                raise ValueError(f"Character.json in {folder_path} has an 'ID' field that does not match the folder name")
            found_Characters.append(character_data["ID"])
            if "display_name" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have a 'display_name' field")
            if not isinstance(character_data["display_name"], str):
                raise ValueError(f"Character.json in {folder_path} has a 'display_name' field that is not a string")
            if "known_Charakters" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have a 'known_Charakters' field")
            if not isinstance(character_data["known_Charakters"], list):
                raise ValueError(f"Character.json in {folder_path} has a 'known_Charakters' field that is not a list")
            needed_Characters.extend(character_data["known_Charakters"])

            if "known_Skills" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have a 'known_Skills' field")
            if not isinstance(character_data["known_Skills"], list):
                raise ValueError(f"Character.json in {folder_path} has a 'known_Skills' field that is not a list")
            for skill_id in character_data["known_Skills"]:
                if not isinstance(skill_id, str):
                    raise ValueError(f"Character.json in {folder_path} has a non-string skill id in 'known_Skills'")
                if not skill_id.startswith("Skill_"):
                    raise ValueError(f"Character.json in {folder_path} has a 'known_Skills' entry that does not start with 'Skill_': {skill_id}")
                if skill_id not in skills_data:
                    raise ValueError(f"Character.json in {folder_path} has a 'known_Skills' entry {skill_id} that is not in Skills.json")

            if "known_SpellEffects" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have a 'known_SpellEffects' field")
            if not isinstance(character_data["known_SpellEffects"], list):
                raise ValueError(f"Character.json in {folder_path} has a 'known_SpellEffects' field that is not a list")
            for spell_effect_id in character_data["known_SpellEffects"]:
                if not isinstance(spell_effect_id, str):
                    raise ValueError(f"Character.json in {folder_path} has a non-string spell effect id in 'known_SpellEffects'")
                if not spell_effect_id.startswith("SpellEffect_"):
                    raise ValueError(f"Character.json in {folder_path} has a 'known_SpellEffects' entry that does not start with 'SpellEffect_': {spell_effect_id}")
                if spell_effect_id not in spelleffekt_data:
                    raise ValueError(f"Character.json in {folder_path} has a 'known_SpellEffects' entry {spell_effect_id} that is not in SpellEffects.json")

            if "known_StatusEffects" not in character_data:
                raise ValueError(f"Character.json in {folder_path} does not have a 'known_StatusEffects' field")
            if not isinstance(character_data["known_StatusEffects"], list):
                raise ValueError(f"Character.json in {folder_path} has a 'known_StatusEffects' field that is not a list")
            for status_effect_id in character_data["known_StatusEffects"]:
                if not isinstance(status_effect_id, str):
                    raise ValueError(f"Character.json in {folder_path} has a non-string status effect id in 'known_StatusEffects'")
                if not status_effect_id.startswith("StatusEffekt_"):
                    raise ValueError(f"Character.json in {folder_path} has a 'known_StatusEffects' entry that does not start with 'StatusEffekt_': {status_effect_id}")
                if status_effect_id not in statusEffekt_data:
                    raise ValueError(f"Character.json in {folder_path} has a 'known_StatusEffects' entry {status_effect_id} that is not in StatusEffekts.json")


            #test Inventory.json each element has to be an Id from Items.json each id can only be used once in all Inventorsy. The Owner id in the Items.json has to match the Character ID.
            #if the Equipped Flag is set, the item has to be listed in StatSheet.json / equipped_items / rows [] under "ID"
            #if the flag is not set, the item must not be listet in StatSheet.json / equipped_items / rows [] under "ID"

            with open(inventory_file_path, "r", encoding="utf-8") as f:
                inventory_data = json.load(f)
            with open(stat_sheet_file_path, "r", encoding="utf-8") as f:
                stat_sheet_data = json.load(f)
            for item_id in inventory_data:
                if item_id not in items_data:
                    raise ValueError(f"Inventory.json in {folder_path} has an item id {item_id} that does not exist in Items.json")
                if items_data[item_id]["owner"] != character_data["ID"]:
                    raise ValueError(f"Inventory.json in {folder_path} has an item id {item_id} that has an owner {items_data[item_id]['owner']} that does not match the character id {character_data['ID']}")
                equipped_items = stat_sheet_data.get("equipped_items", {}).get("rows", [])
                if items_data[item_id]["equipped"]:
                    if not any(equipped_item.get("ID") == item_id for equipped_item in equipped_items):
                        raise ValueError(f"Inventory.json in {folder_path} has an item id {item_id} that is equipped but is not listed in StatSheet.json / equipped_items / rows []")
                else:
                    if any(equipped_item.get("ID") == item_id for equipped_item in equipped_items):
                        raise ValueError(f"Inventory.json in {folder_path} has an item id {item_id} that is not equipped but is listed in StatSheet.json / equipped_items / rows []")

            #test StatSheet.json. In the keys "equipped_items", "learned_abilities", "active_spell_effects", "active_status_effects" each of them Has an "ID" key.
            #the ID of equipped_item has to be in Inventory.json and in Items.json, and has to have the equipped flag in Items.json.
            #the ID of learned_abilities has to be in Skills.json.
            #the ID of active_spell_effects has to be in SpellEffects.json.
            #the ID of active_status_effects has to be in StatusEffekts.json.

            if "equipped_items" not in stat_sheet_data:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'equipped_items' field")
            if "learned_abilities" not in stat_sheet_data:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'learned_abilities' field")
            if "active_spell_effects" not in stat_sheet_data:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'active_spell_effects' field")
            if "active_status_effects" not in stat_sheet_data:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'active_status_effects' field")
            if "rows" not in stat_sheet_data["equipped_items"]:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'equipped_items' field with 'rows'")
            if "rows" not in stat_sheet_data["learned_abilities"]:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'learned_abilities' field with 'rows'")
            if "rows" not in stat_sheet_data["active_spell_effects"]:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'active_spell_effects' field with 'rows'")
            if "rows" not in stat_sheet_data["active_status_effects"]:
                raise ValueError(f"StatSheet.json in {folder_path} does not have an 'active_status_effects' field with 'rows'")
            for equipped_item in stat_sheet_data["equipped_items"]["rows"]:
                if equipped_item.get("ID") not in inventory_data:
                    raise ValueError(f"StatSheet.json in {folder_path} has an equipped item id {equipped_item.get('ID')} that is not in Inventory.json")
                if equipped_item.get("ID") not in items_data:
                    raise ValueError(f"StatSheet.json in {folder_path} has an equipped item id {equipped_item.get('ID')} that is not in Items.json")
                if not items_data[equipped_item.get("ID")]["equipped"]:
                    raise ValueError(f"StatSheet.json in {folder_path} has an equipped item id {equipped_item.get('ID')} that is not marked as equipped in Items.json")
            for learned_ability_id in stat_sheet_data["learned_abilities"]["rows"]:
                if learned_ability_id.get("ID") not in skills_data.keys():
                    raise ValueError(f"StatSheet.json in {folder_path} has a learned ability id {learned_ability_id.get('ID')} that is not in Skills.json")
            for active_spell_effect_id in stat_sheet_data["active_spell_effects"]["rows"]:
                if active_spell_effect_id.get("ID") not in spelleffekt_data.keys():
                    raise ValueError(f"StatSheet.json in {folder_path} has an active spell effect id {active_spell_effect_id.get('ID')} that is not in SpellEffects.json")
            for active_status_effect_id in stat_sheet_data["active_status_effects"]["rows"]:
                if active_status_effect_id.get("ID") not in statusEffekt_data.keys():
                    raise ValueError(f"StatSheet.json in {folder_path} has an active status effect id {active_status_effect_id.get('ID')} that is not in StatusEffekts.json")

    #compare found_Characters and needed_Characters. 
    # If any character in needed_Characters is not in found_Characters, raise an error.
    if not all(character in found_Characters for character in needed_Characters):
        missing_characters = [character for character in needed_Characters if character not in found_Characters]
        raise ValueError(f"The following characters are referenced in known_Charakters but do not exist: {missing_characters}")

def main() -> None:
    executable_path = Path(__file__).parent / "data"
    users_data = TestUsers(executable_path)
    TestForStatSheetTemplate(executable_path)
    resources = TestForGlobalDocuments(executable_path)
    TestForUserFolder(executable_path, users_data, *resources)

if __name__ == "__main__":
    main()

    