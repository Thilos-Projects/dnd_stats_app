# API-Referenz `dnd_stats_app`

Diese Datei fasst alle Funktionen zusammen, die von außen (z. B. von einer künftigen
Web-App, einem CLI-Tool oder anderen Modulen) aufgerufen werden sollen. Ziel ist,
dass diese Referenz zum Verwenden der Funktionen ausreicht, ohne den Quellcode lesen
zu müssen.

Nicht dokumentiert sind private Hilfsfunktionen (Namen mit `_`-Präfix) und die
`main()`-Funktionen der Module (das sind Selbsttests/Demos, keine öffentliche API).

Der Ordner `ForeLaterUse/` wurde bei dieser Zusammenfassung ignoriert.

---

## Users.py — Benutzerverwaltung

Verwaltet `data/Users.json` und die zugehörigen Benutzerordner unter `data/User/`.
Admin-Operationen erfordern das globale Admin-Passwort (`Users.AdminPassword`, aktuell `"1234"`).

### `createUser(adminpass: str, username: str, password_Hash: str, role: str) -> str`
Legt einen neuen Benutzer an und erstellt seinen Ordner unter `data/User/<id ohne "User_">`.
- **Parameter:**
  - `adminpass` — muss `AdminPassword` entsprechen.
  - `username` — Anzeigename des Benutzers.
  - `password_Hash` — Passwort-Hash (wird 1:1 gespeichert, kein Hashing durch die Funktion).
  - `role` — z. B. `"gm"`, `"admin"`, `"player"`.
- **Rückgabe:** neue Benutzer-ID im Format `"User_<n>"`.
- **Fehler:** `ValueError`, wenn `adminpass` falsch ist.

### `hasUser(userId: str) -> bool`
Prüft, ob eine Benutzer-ID in `Users.json` existiert.
- **Rückgabe:** `True`/`False`.

### `listUsers(adminpass: str) -> list[str]`
Listet alle Benutzer-IDs.
- **Fehler:** `ValueError` bei falschem `adminpass`.

### `getUserRole(userId: str) -> str | None`
Liefert die Rolle (`"gm"`, `"admin"`, `"player"`, …) eines Benutzers oder `None`, wenn er nicht existiert.

### `loginTestUser(userId: str, username: str, password_Hash: str) -> bool`
Prüft Zugangsdaten (Benutzer-ID + Username + Passwort-Hash müssen übereinstimmen).
- **Rückgabe:** `True` bei Erfolg, sonst `False`. Wirft keine Exception bei falschen Daten.

### `deleteUser(adminpass: str, userId: str) -> None`
Entfernt den Benutzer aus `Users.json` und löscht seinen kompletten Ordner samt Inhalt.
- **Fehler:** `ValueError` bei falschem `adminpass`. Kein Fehler, wenn `userId` nicht existiert (No-Op).

---

## Characters.py — Charakterverwaltung

Verwaltet Charaktere unter `data/User/<benutzerordner>/<charakterordner>/`. Jede Funktion
prüft Login-Daten selbst (`user_id`, `username`, `password_hash`) über `Users.loginTestUser`.
Rollen `gm`/`admin` gelten als "Manager" mit erweiterten Rechten.

### `createCharacter(user_id, username, password_hash, folder_name, display_name) -> str`
Legt einen neuen Charakter im **eigenen** Benutzerordner an (jeder validierte Benutzer darf das).
Erstellt `Character.json`, `Inventory.json`, `StatSheet.json` (aus den Templates in `data/`) sowie
einen `documents`-Unterordner.
- **Parameter:**
  - `folder_name` — Ordnername des Charakters (muss im Benutzerordner eindeutig sein).
  - `display_name` — Anzeigename, nicht-leerer String.
- **Rückgabe:** neue Charakter-ID, Format `"Charakter_<folder_name>"`.
- **Fehler:** `PermissionError` bei ungültigem Login; `ValueError` bei fehlendem Benutzerordner,
  bereits existierendem Charakterordner oder leerem `display_name`.

### `deleteCharacter(user_id, username, password_hash, character_id) -> None`
Löscht einen Charakterordner komplett.
- **Rechte:** Eigentümer des Charakters ODER GM/Admin.
- **Fehler:** `PermissionError` bei fehlenden Rechten/ungültigem Login; `ValueError`, wenn
  `character_id` nicht existiert.

### `listOwnCharacters(user_id, username, password_hash) -> list[str]`
Listet alle Charakter-IDs im eigenen Benutzerordner des Aufrufers.

### `listUserCharacters(user_id, username, password_hash, target_user_id) -> list[str]`
Listet Charakter-IDs eines anderen Benutzers.
- **Rechte:** nur wenn `target_user_id == user_id`, oder Aufrufer ist GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn `target_user_id` nicht existiert.

### `listAllCharacters(user_id, username, password_hash) -> list[str]`
Listet alle Charakter-IDs aller Benutzer.
- **Rechte:** nur GM/Admin. Sonst `PermissionError`.

### `getKnownCharacters(user_id, username, password_hash, character_id) -> list[str]`
Liest die Liste `known_Charakters` eines Charakters.
- **Rechte:** Eigentümer des Charakters ODER GM/Admin.
- **Fehler:** `PermissionError` bei fehlenden Rechten/ungültigem Login; `ValueError`, wenn
  `character_id` nicht existiert.

### `getKnownSkills(user_id, username, password_hash, character_id) -> list[str]`
Liest die Liste `known_Skills` eines Charakters.
- **Rechte:** Eigentümer des Charakters ODER GM/Admin.
- **Fehler:** wie bei `getKnownCharacters`.

### `getKnownSpellEffects(user_id, username, password_hash, character_id) -> list[str]`
Liest die Liste `known_SpellEffects` eines Charakters.
- **Rechte:** Eigentümer des Charakters ODER GM/Admin.
- **Fehler:** wie bei `getKnownCharacters`.

### `getKnownStatusEffects(user_id, username, password_hash, character_id) -> list[str]`
Liest die Liste `known_StatusEffects` eines Charakters.
- **Rechte:** Eigentümer des Charakters ODER GM/Admin.
- **Fehler:** wie bei `getKnownCharacters`.

### `editKnownCharacters(user_id, username, password_hash, character_id, known_characters: list[str]) -> None`
Ersetzt die Liste `known_Charakters` eines Charakters (Referenzen auf andere existierende Charaktere).
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError` bei ungültiger Liste oder unbekannter Charakter-ID
  in `known_characters`.

### `editKnownSkills(user_id, username, password_hash, character_id, known_skills: list[str]) -> None`
Ersetzt `known_Skills`. Jede ID muss mit `"Skill_"` beginnen und in `data/Global/Skills.json` existieren.
- **Rechte:** nur GM/Admin.

### `editKnownSpellEffects(user_id, username, password_hash, character_id, known_spell_effects: list[str]) -> None`
Ersetzt `known_SpellEffects`. IDs müssen mit `"SpellEffect_"` beginnen und in
`data/Global/SpellEffects.json` existieren.
- **Rechte:** nur GM/Admin.

### `editKnownStatusEffects(user_id, username, password_hash, character_id, known_status_effects: list[str]) -> None`
Ersetzt `known_StatusEffects`. IDs müssen mit `"StatusEffekt_"` beginnen und in
`data/Global/StatusEffekts.json` existieren.
- **Rechte:** nur GM/Admin.

---

## Items.py — Gegenstandsverwaltung

Verwaltet globale Items in `data/Global/Items.json` und ihre Zuweisung zu Charakter-Inventaren
(`Inventory.json`) sowie Ausrüstung im `StatSheet.json` (`equipped_items.rows`).

### `createItem(user_id, username, password_hash, name, description, stat_bonus=None) -> str`
Erstellt ein neues, noch niemandem zugewiesenes Item.
- **Parameter:**
  - `name` — nicht-leerer String.
  - `description` — String (darf leer sein).
  - `stat_bonus` — optionales Dict mit genau den Feldern `Mut, Klugheit, Intuition, Charisma,
    Fingerfertigkeit, Gewandheit, Konstitution, Körperkraft, MagieSpeicher, MagieRegeneration`,
    jeweils ganzzahlig zwischen -10 und 10. Fehlt es, werden alle Werte auf 0 gesetzt.
- **Rechte:** nur GM/Admin.
- **Rückgabe:** neue Item-ID, Format `"Item_<n>"`.
- **Fehler:** `PermissionError`; `ValueError` bei ungültigem Namen/Beschreibung/`stat_bonus`.

### `deleteItem(user_id, username, password_hash, item_id) -> None`
Löscht ein Item dauerhaft. Nur möglich, wenn das Item **keinem** Charakter zugewiesen ist.
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn Item nicht existiert oder noch zugewiesen ist.

### `assignItemToCharacter(user_id, username, password_hash, item_id, character_id) -> None`
Weist ein noch nicht zugewiesenes Item einem Charakter-Inventar zu.
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn Item bereits zugewiesen ist, Charakter nicht
  existiert oder Item schon im Inventar liegt.

### `equipItem(user_id, username, password_hash, item_id, character_id) -> None`
Markiert ein zugewiesenes Item als ausgerüstet und trägt es in `StatSheet.json` unter
`equipped_items.rows` ein (idempotent — mehrfacher Aufruf ist unschädlich).
- **Rechte:** Charaktereigentümer ODER GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn Item nicht diesem Charakter gehört oder nicht
  im Inventar liegt.

### `unequipItem(user_id, username, password_hash, item_id, character_id) -> None`
Entfernt ein Item aus `equipped_items.rows` und setzt das Flag `equipped` zurück.
- **Rechte:** Charaktereigentümer ODER GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn Item nicht diesem Charakter gehört.

### `removeItemFromCharacter(user_id, username, password_hash, item_id, character_id) -> None`
Entfernt ein **nicht ausgerüstetes** Item aus dem Inventar eines Charakters (Item wird wieder
"herrenlos", nicht gelöscht).
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError`, wenn Item nicht diesem Charakter gehört, noch
  ausgerüstet ist, oder nicht im Inventar liegt.

### `moveItemBetweenCharacters(user_id, username, password_hash, item_id, from_character_id, to_character_id) -> None`
Verschiebt ein nicht ausgerüstetes Item von einem Charakter zu einem anderen — nur wenn der
Quell-Charakter den Ziel-Charakter in seiner `known_Charakters`-Liste kennt.
- **Rechte:** Eigentümer des Quell-Charakters ODER GM/Admin.
- **Fehler:** `ValueError` (gleiche Quelle/Ziel, Item nicht zugewiesen/ausgerüstet, Item fehlt im
  Quell-Inventar, Item bereits im Ziel-Inventar); `PermissionError` (Quelle kennt Ziel nicht /
  ungültiger Login / keine Berechtigung).

### `ListAllItems(user_id, username, password_hash) -> dict[str, dict[str, Any]]`
Listet alle Items, die der Nutzer sehen darf.
- **Rechte:** GM/Admin sieht alle Items; ein Spieler sieht nur Items, deren Besitzer-Charakter
  ihm selbst gehört (unzugewiesene Items sind für Spieler nicht sichtbar).
- **Fehler:** `PermissionError` bei ungültigem Login.

---

## Skills.py — globale Skills

Verwaltet globale Skills in `data/Global/Skills.json` und ihre Zuweisung zu `known_Skills` der
Charaktere.

### `createSkill(user_id, username, password_hash, name, beschreibung, stat_bonus=None, talent_bonus=None, skill_bonus=None, alters_anstieg=0) -> str`
Erstellt einen neuen Skill.
- **Parameter:**
  - `name` — nicht-leerer String.
  - `beschreibung` — String (darf leer sein).
  - `stat_bonus` — optionales Dict mit den Feldern `Mut, Klugheit, Intuition, Charisma,
    Fingerfertigkeit, Gewandheit, Konstitution, Körperkraft`, jeweils ganzzahlig zwischen -10 und 10.
    Fehlt es, werden alle Werte auf 0 gesetzt.
  - `talent_bonus` — optionales Dict mit den Feldern `Körpertalent, Geseltschaftstalent,
    Naturtalent, Wissenstalent, Handwerkstalent`, jeweils ganzzahlig zwischen -10 und 10.
  - `skill_bonus` — optionales Dict über alle bekannten Skill-Namen (z. B. `Klettern`, `Singen`, …),
    jeweils ganzzahlig zwischen -10 und 10.
  - `alters_anstieg` — Ganzzahl, Standard `0`.
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError` bei ungültigem Namen/Bonus-Dict/`alters_anstieg`.

### `deleteSkill(user_id, username, password_hash, skill_id) -> None`
Löscht einen Skill dauerhaft. Nur möglich, wenn kein Charakter ihn kennt.
- **Rechte:** nur GM/Admin.

### `assignSkillToCharacter(user_id, username, password_hash, skill_id, character_id) -> None`
Trägt einen Skill in `known_Skills` eines Charakters ein.
- **Rechte:** nur GM/Admin.

### `removeSkillFromCharacter(user_id, username, password_hash, skill_id, character_id) -> None`
Entfernt einen Skill aus `known_Skills` eines Charakters.
- **Rechte:** nur GM/Admin.

### `listAllSkills(user_id, username, password_hash) -> dict[str, dict]`
Listet alle Skills, die der Nutzer sehen darf.
- **Rechte:** GM/Admin sieht alle Skills; ein Spieler sieht nur Skills aus seiner
  `known_Skills`-Liste.
- **Fehler:** `PermissionError` bei ungültigem Login.

---

## SpellEffects.py — globale Zaubereffekte

Verwaltet globale Zaubereffekte in `data/Global/SpellEffects.json` und ihre Zuweisung zu
`known_SpellEffects` der Charaktere.

### `createSpellEffect(user_id, username, password_hash, name, description, default_duration=0, default_time_to_death=0, stat_bonus=None, talent_bonus=None, skill_bonus=None) -> str`
Erstellt einen neuen Zaubereffekt.
- **Parameter:**
  - `name` — nicht-leerer String.
  - `description` — String (darf leer sein).
  - `default_duration`, `default_time_to_death` — nicht-negative Ganzzahlen, Standard `0`.
  - `stat_bonus` — optionales Dict mit den Skill-Stat-Feldern plus `MagieSpeicher, MagieRegeneration`,
    jeweils ganzzahlig zwischen -10 und 10.
  - `talent_bonus` — optionales Dict wie bei `createSkill`.
  - `skill_bonus` — optionales Dict wie bei `createSkill`.
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError` bei ungültigem Namen/Bonus-Dict/Dauerwerten.

### `deleteSpellEffect(user_id, username, password_hash, spell_effect_id) -> None`
Löscht einen Zaubereffekt dauerhaft. Nur möglich, wenn kein Charakter ihn kennt.
- **Rechte:** nur GM/Admin.

### `assignSpellEffectToCharacter(user_id, username, password_hash, spell_effect_id, character_id) -> None`
Trägt einen Zaubereffekt in `known_SpellEffects` eines Charakters ein.
- **Rechte:** nur GM/Admin.

### `removeSpellEffectFromCharacter(user_id, username, password_hash, spell_effect_id, character_id) -> None`
Entfernt einen Zaubereffekt aus `known_SpellEffects` eines Charakters.
- **Rechte:** nur GM/Admin.

### `listAllSpellEffects(user_id, username, password_hash) -> dict[str, dict]`
Listet alle Zaubereffekte, die der Nutzer sehen darf.
- **Rechte:** GM/Admin sieht alle Zaubereffekte; ein Spieler sieht nur Effekte aus seiner
  `known_SpellEffects`-Liste.
- **Fehler:** `PermissionError` bei ungültigem Login.

---

## Statuseffekts.py — globale Statuseffekte

Verwaltet globale Statuseffekte in `data/Global/StatusEffekts.json` und ihre Zuweisung zu
`known_StatusEffects` der Charaktere.

### `createStatusEffect(user_id, username, password_hash, name, beschreibung, default_duration=0, default_time_to_death=0, stat_bonus=None, talent_bonus=None) -> str`
Erstellt einen neuen Statuseffekt.
- **Parameter:**
  - `name` — nicht-leerer String.
  - `beschreibung` — String (darf leer sein).
  - `default_duration`, `default_time_to_death` — nicht-negative Ganzzahlen, Standard `0`.
  - `stat_bonus` — optionales Dict mit den Skill-Stat-Feldern plus `MagieSpeicher, MagieRegeneration`,
    jeweils ganzzahlig zwischen -10 und 10.
  - `talent_bonus` — optionales Dict wie bei `createSkill`.
- **Rechte:** nur GM/Admin.
- **Fehler:** `PermissionError`; `ValueError` bei ungültigem Namen/Bonus-Dict/Dauerwerten.

### `deleteStatusEffect(user_id, username, password_hash, status_effect_id) -> None`
Löscht einen Statuseffekt dauerhaft. Nur möglich, wenn kein Charakter ihn kennt.
- **Rechte:** nur GM/Admin.

### `assignStatusEffectToCharacter(user_id, username, password_hash, status_effect_id, character_id) -> None`
Trägt einen Statuseffekt in `known_StatusEffects` eines Charakters ein.
- **Rechte:** nur GM/Admin.

### `removeStatusEffectFromCharacter(user_id, username, password_hash, status_effect_id, character_id) -> None`
Entfernt einen Statuseffekt aus `known_StatusEffects` eines Charakters.
- **Rechte:** nur GM/Admin.

### `listAllStatusEffects(user_id, username, password_hash) -> dict[str, dict]`
Listet alle Statuseffekte, die der Nutzer sehen darf.
- **Rechte:** GM/Admin sieht alle Statuseffekte; ein Spieler sieht nur Effekte aus seiner
  `known_StatusEffects`-Liste.
- **Fehler:** `PermissionError` bei ungültigem Login.

---

## stat_engine.py — Formel-Engine für StatSheet.json

Wertet die Formel-Felder (`{"formula": "...", "value": ...}`) einer `StatSheet.json` aus.
Unterstützte Operatoren: `+ - * /`, Klammern, sowie Funktionen `MIN, MAX, ABS, MEDIAN, SUM`.
Pfade können mit `[]` auf Listen-Zeilen verweisen (z. B. `equipped_items.rows[].stat_bonus.Mut`),
was intern über `AggregateList` aggregiert wird.

### `load_and_compute(path: str | Path) -> dict`
Lädt eine `StatSheet.json`-Datei, berechnet **alle** Formel-Felder und gibt das aktualisierte
Dokument (als Dict) zurück. Schreibt die Datei **nicht** automatisch zurück auf die Platte —
das muss der Aufrufer selbst tun (siehe `validate_data.main()`/`stat_engine.main()` als Beispiel).
- **Fehler:** `FormulaError` (inkl. Unterklasse `CircularReferenceError`) bei fehlerhaften Formeln
  oder zirkulären Referenzen; `CouldNotReach`, wenn ein referenzierter Pfad (z. B. auf ein Item,
  einen Skill, einen Spell-/StatusEffekt) nicht auflösbar ist.

### Klasse `StatSheetEngine(doc: dict)`
Für Fälle, in denen man mehr Kontrolle braucht als `load_and_compute` bietet (z. B. gezieltes
Nachschlagen einzelner Felder statt des gesamten Dokuments).
- `engine.get(path: str)` — löst einen einzelnen Punkt-Pfad auf (z. B. `"stats.Mut.wert"`) und
  gibt den berechneten Wert zurück. Formel-Ergebnisse werden gecached.
- `engine.compute_all() -> dict` — berechnet alle Formel-Felder unter `meta`, `stats`, `talents`,
  `skills` und gibt `engine.doc` zurück (identisch zum Verhalten von `load_and_compute`).
- Wirft dieselben Fehler wie oben (`FormulaError`, `CircularReferenceError`, `CouldNotReach`).

### Fehlerklassen (zum Abfangen)
- `FormulaError` — Basisklasse für Formel-/Parserfehler.
- `CircularReferenceError(FormulaError)` — ein Feld hängt (direkt/indirekt) von sich selbst ab.
- `CouldNotReach` — ein referenzierter Objektpfad existiert nicht oder ist kein Zahlenwert.

---

## validate_data.py — Datenintegritätsprüfung

Prüft die gesamte Datenstruktur unter `dnd_stats_app/data/` auf Konsistenz. Alle Funktionen
werfen bei einem Problem eine Exception (`FileNotFoundError` oder `ValueError`) mit einer
sprechenden Fehlermeldung; geben bei Erfolg nichts zurück (`None`).

### `TestUsers(executable_path: Path) -> None`
Prüft `Users.json`: jede ID beginnt mit `"User_"`, hat `username`, `password_hash` und eine
gültige `role` (`"gm"` oder `"player"`).

### `TestForStatSheetTemplate(executable_path: Path) -> None`
Prüft, dass `stat_sheet_template.json` existiert und gültiges JSON ist.

### `TestForGlobalDocuments(executable_path: Path) -> None`
Prüft, dass der `Global`-Ordner sowie `Items.json`, `Skills.json`, `SpellEffects.json`,
`StatusEffekts.json` existieren, gültiges JSON sind und ihre erwarteten Felder/Wertebereiche
(Stat-/Talent-/Skill-Boni jeweils zwischen -10 und 10) einhalten.

### `TestForUserFolder(executable_path: Path) -> None`
Prüft für jeden Benutzer aus `Users.json`, dass ein Ordner existiert, und für jeden
Charakterordner darin: vorhandene/valide `StatSheet.json`, `Inventory.json`, `Character.json`
und `documents`-Ordner, korrekte Verknüpfung von Item-Besitz/Ausrüstung zwischen `Inventory.json`,
`Items.json` und `StatSheet.json`, sowie dass alle `known_Charakters`-Referenzen tatsächlich
existierende Charaktere sind.

### `main() -> None`
Führt alle obigen Prüfungen in der Reihenfolge `TestUsers → TestForStatSheetTemplate →
TestForGlobalDocuments → TestForUserFolder` gegen `dnd_stats_app/data` aus. Nützlich als einziger
Einstiegspunkt, um "ist mein Datenordner konsistent?" zu beantworten — wirft bei jedem gefundenen
Problem sofort eine Exception ab.

---

## Modul-Abhängigkeiten (Aufrufreihenfolge beim Import)

```mermaid
graph LR
    Users --> Characters
    Users --> Items
    Characters --> Items
    validate_data -.eigenständig.-> validate_data
    stat_engine -.eigenständig.-> stat_engine
```

`Characters.py` und `Items.py` importieren `Users.py` für Login-/Rollenprüfung.
`Items.py` importiert zusätzlich `Characters.py` (nur für dessen `main()`-Test) und `validate_data.py`.
`stat_engine.py` und `validate_data.py` sind unabhängig lauffähig.

---

## rest_api.py — minimale REST-Schnittstelle

Setzt jede oben dokumentierte Funktion 1:1 als HTTP-Route um (`python rest_api.py` startet den
Entwicklungsserver; produktiv über einen WSGI-Server auf `rest_api:app` verweisen).

- **Route:** `POST /api/<Funktionsname>` (z. B. `POST /api/createUser`, `POST /api/listAllItems`).
  `POST` wird einheitlich für **alle** Aufrufe verwendet (auch lesende), weil praktisch jede
  Funktion ein `password_hash`-Credential entgegennimmt — das gehört nicht in eine URL/Query
  (Server-/Proxy-Logs, Browser-Verlauf).
- **Request-Body:** JSON-Objekt, dessen Schlüssel exakt den Parameternamen der Funktion
  entsprechen (siehe Dokumentation oben). Parameter mit Default-Wert sind optional.
- **Response:** der Rückgabewert der Funktion als JSON (`None` → `null`).
- **Fehlerantworten:** `{"error": "<Meldung>"}` mit Statuscode
  `403` (`PermissionError`), `400` (`ValueError`/`TypeError`/fehlender Pflichtparameter),
  `404` (`FileNotFoundError`), `500` (alle anderen Fehler).

### Abweichungen vom automatischen 1:1-Mapping (aus Sicherheitsgründen)

- **`POST /api/load_and_compute`** — nimmt `{"character_id": "..."}` statt eines rohen
  Dateipfads entgegen. Die Funktion `stat_engine.load_and_compute(path)` einen beliebigen,
  clientseitig übergebenen Pfad einlesen zu lassen, wäre ein Path-Traversal-/Arbitrary-File-Read-
  Risiko; die Route löst den `StatSheet.json`-Pfad stattdessen intern und sicher über die
  Charakter-ID auf.
- **`POST /api/validate_all`** — ruft `api.validate_all()` (= `validate_data.main()`) auf und
  liefert `{"status": "ok"}` bei Erfolg. Die einzelnen `validate_data.TestX`-Funktionen werden
  nicht als eigene Routen freigegeben, da sie intern verkettet sind (`TestForUserFolder` benötigt
  z. B. die Rückgabewerte der anderen Prüfungen) und laut API.md ohnehin nur über den
  gemeinsamen Einstiegspunkt aufgerufen werden sollen.
- **`StatSheetEngine`, `FormulaError`, `CircularReferenceError`, `CouldNotReach`** — Klassen/
  Exceptions, keine aufrufbaren Endpunkte.
