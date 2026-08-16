"""Single import point for the public `dnd_stats_app` API.

Bundles the public functions/classes of `Users`, `Characters`, `Items`, `Skills`,
`SpellEffects`, `Statuseffekts`, `stat_engine` and `validate_data` so that callers
(a future web app, a CLI, ...) only need to do::

    import api
    # or
    from api import createUser, createCharacter, load_and_compute

See `API.md` for the full documentation of every function re-exported here.
Private helpers (`_`-prefixed names) and the per-module `main()` self-tests are
intentionally not re-exported, matching the scope of `API.md`.
"""

from __future__ import annotations

# Users.py -- Benutzerverwaltung
from Users import (
    createUser,
    hasUser,
    listUsers,
    getUserRole,
    loginTestUser,
    deleteUser,
    tryFindUserID,
)

# Characters.py -- Charakterverwaltung
from Characters import (
    createCharacter,
    deleteCharacter,
    listOwnCharacters,
    listUserCharacters,
    listAllCharacters,
    getKnownCharacters,
    getKnownSkills,
    getKnownSpellEffects,
    getKnownStatusEffects,
    editKnownCharacters,
    editKnownSkills,
    editKnownSpellEffects,
    editKnownStatusEffects,
)

# Items.py -- Gegenstandsverwaltung
from Items import (
    createItem,
    deleteItem,
    assignItemToCharacter,
    equipItem,
    unequipItem,
    removeItemFromCharacter,
    moveItemBetweenCharacters,
    ListAllItems,
)

# Skills.py -- globale Skills
from Skills import (
    createSkill,
    deleteSkill,
    assignSkillToCharacter,
    removeSkillFromCharacter,
    listAllSkills,
)

# SpellEffects.py -- globale Zaubereffekte
from SpellEffects import (
    createSpellEffect,
    deleteSpellEffect,
    assignSpellEffectToCharacter,
    removeSpellEffectFromCharacter,
    listAllSpellEffects,
)

# Statuseffekts.py -- globale Statuseffekte
from Statuseffekts import (
    createStatusEffect,
    deleteStatusEffect,
    assignStatusEffectToCharacter,
    removeStatusEffectFromCharacter,
    listAllStatusEffects,
)

# stat_engine.py -- Formel-Engine für StatSheet.json
from stat_engine import (
    load_and_compute,
    StatSheetEngine,
    FormulaError,
    CircularReferenceError,
    CouldNotReach,
)

# validate_data.py -- Datenintegritätsprüfung
from validate_data import (
    TestUsers,
    TestForStatSheetTemplate,
    TestForGlobalDocuments,
    TestForUserFolder,
)
from validate_data import main as validate_all

__all__ = [
    # Users
    "createUser",
    "hasUser",
    "listUsers",
    "getUserRole",
    "loginTestUser",
    "deleteUser",
    "tryFindUserID",
    # Characters
    "createCharacter",
    "deleteCharacter",
    "listOwnCharacters",
    "listUserCharacters",
    "listAllCharacters",
    "getKnownCharacters",
    "getKnownSkills",
    "getKnownSpellEffects",
    "getKnownStatusEffects",
    "editKnownCharacters",
    "editKnownSkills",
    "editKnownSpellEffects",
    "editKnownStatusEffects",
    # Items
    "createItem",
    "deleteItem",
    "assignItemToCharacter",
    "equipItem",
    "unequipItem",
    "removeItemFromCharacter",
    "moveItemBetweenCharacters",
    "ListAllItems",
    # Skills
    "createSkill",
    "deleteSkill",
    "assignSkillToCharacter",
    "removeSkillFromCharacter",
    "listAllSkills",
    # SpellEffects
    "createSpellEffect",
    "deleteSpellEffect",
    "assignSpellEffectToCharacter",
    "removeSpellEffectFromCharacter",
    "listAllSpellEffects",
    # Statuseffekts
    "createStatusEffect",
    "deleteStatusEffect",
    "assignStatusEffectToCharacter",
    "removeStatusEffectFromCharacter",
    "listAllStatusEffects",
    # stat_engine
    "load_and_compute",
    "StatSheetEngine",
    "FormulaError",
    "CircularReferenceError",
    "CouldNotReach",
    # validate_data
    "TestUsers",
    "TestForStatSheetTemplate",
    "TestForGlobalDocuments",
    "TestForUserFolder",
    "validate_all",
]
