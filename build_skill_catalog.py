"""Build the default job, weapon, and tool skill catalogue."""

from __future__ import annotations

import json
from pathlib import Path

import Skills


SKILLS_PATH = Path(__file__).parent / "data" / "Global" / "Skills.json"
BASE_TRAINING = 0.17
INTERMEDIATE_TRAINING = 0.5
ADVANCED_TRAINING = 1.0

JOBS = (
    ("Schmied", "Metallbearbeitung", "Gildenmeister", "Freischmied", "Kettenschmied"),
    ("Zimmermann", "Holzbearbeitung", "Bauvorsteher", "Wanderhandwerker", "Einbrecherbauer"),
    ("Steinmetz", "Steinbearbeitung", "Baumeister", "Grabsteinarbeiter", "Gruftpluenderer"),
    ("Gerber", "Lederbearbeitung", "Zunftgerber", "Fellwanderer", "Hautsammler"),
    ("Weber", "Stoffbearbeitung", "Tuchmeister", "Marktweber", "Falschweber"),
    ("Baecker", "Lebensmittelbearbeitung", "Hofbaecker", "Reisebaecker", "Giftbaecker"),
    ("Koch", "Lebensmittelbearbeitung", "Kuechenmeister", "Lagerkoch", "Kuecheninformant"),
    ("Bauer", "Pflanzenkunde", "Hofverwalter", "Feldkundiger", "Pachtbrecher"),
    ("Fischer", "Fischen/Angeln", "Flussmeister", "Kuestenfahrer", "Netzraeuber"),
    ("Jaeger", "Tierkunde", "Wildhueter", "Faehrtenleser", "Wilddieb"),
    ("Heiler", "HeilkundeWunden", "Klosterheiler", "Wanderheiler", "Leichenheiler"),
    ("Kraeuterkundiger", "Alchemie", "Apotheker", "Sammler", "Giftmischer"),
    ("Schreiber", "Rechnen", "Archivschreiber", "Briefschreiber", "Urkundenfaelscher"),
    ("Haendler", "Handel", "Gildenhaendler", "Kraemer", "Schwarzhaendler"),
    ("Wirt", "Menschenkenntniss", "Schankmeister", "Wanderwirt", "Schieber"),
    ("Bote", "Bote/Schiffe", "Hofbote", "Weglaeufer", "Schmugglerbote"),
    ("Kutscher", "Fahrzäuge", "Stallmeister", "Frachtfahrer", "Fluchtfahrer"),
    ("Seemann", "Bote/Schiffe", "Deckoffizier", "Flussfahrer", "Freibeuter"),
    ("Soldat", "Kriegstkunst", "Wachhauptmann", "Söldner", "Pluenderer"),
    ("Wachmann", "Sinnesschärfe", "Torwaechter", "Streifengaenger", "Erpresser"),
    ("Geistlicher", "Götter/Kulte", "Tempeldiener", "Pilgerprediger", "Kultwerber"),
    ("Musiker", "Musizieren", "Hofmusiker", "Gaukler", "Spottsaenger"),
    ("Maler", "Malen/Zeichnen", "Zunftmaler", "Landschaftsmaler", "Faelscher"),
    ("Mechaniker", "Mechanik", "Werkmeister", "Tueftler", "Saboteur"),
    ("Bergmann", "Kraftakt", "Stollenmeister", "Erzsucher", "Grabräuber"),
)

WEAPON_FAMILIES = (
    ("Schwert", "ein Schwert", "Schwert-Skills", ("Zustechen", "Zuschlagen", "Parieren", "Ausweichen")),
    ("Dolch", "einen Dolch oder ein Messer", "Dolch-Skills", ("Zustechen", "Schneiden", "Parieren", "Ausweichen")),
    ("Axt", "eine Axt", "Axt-Skills", ("Spalten", "Haken", "Parieren", "Ausweichen")),
    ("Keule", "eine Keule oder einen Hammer", "Keulen-Skills", ("Zuschlagen", "Stoßen", "Blocken", "Ausweichen")),
    ("Speer", "einen Speer", "Speer-Skills", ("Zustechen", "Abstand halten", "Parieren", "Ausweichen")),
    ("Stangenwaffe", "eine Hellebarde, Glefe oder Kampfsense", "Stangenwaffen-Skills", ("Zustechen", "Hauen", "Sperren", "Ausweichen")),
    ("Bogen", "einen Bogen und passende Pfeile", "Pfeilwaffen-Skills", ("Zielen", "Schnellschuss", "Deckungswechsel", "Ausweichen")),
    ("Armbrust", "eine Armbrust und passende Bolzen", "Pfeilwaffen-Skills", ("Zielen", "Laden", "Deckungswechsel", "Ausweichen")),
    ("Wurfwaffe", "Wurfmesser, Wurfaxt oder Wurfspeer", "Wurfwaffen-Skills", ("Zielen", "Schnellwurf", "Entwaffnen", "Ausweichen")),
    ("Schleuder", "eine Schleuder und passende Kugeln", "Wurfwaffen-Skills", ("Zielen", "Schnellschuss", "Deckungswechsel", "Ausweichen")),
    ("Peitsche", "eine Peitsche", "Peitschen-Skills", ("Schlagen", "Haken", "Abstand halten", "Ausweichen")),
    ("Unbewaffnet", "freie Haende", "unbewaffnete Kampf-Skills", ("Stoßen", "Greifen", "Blocken", "Ausweichen")),
)

TOOLS = (
    ("Schmiedewerkzeug", "Hammer, Zange und Schmiedefeuer", "Schmied"),
    ("Holzbearbeitung", "Saege, Beil oder Hobel", "Zimmermann"),
    ("Steinbearbeitung", "Meissel und Hammer", "Steinmetz"),
    ("Lederwerkzeug", "Ahle, Messer und Nadel", "Gerber"),
    ("Webwerkzeug", "Webstuhl, Nadel oder Spindel", "Weber"),
    ("Kuechenwerkzeug", "Messer, Topf und Feuerstelle", "Koch"),
    ("Heilerbesteck", "saubere Binden, Nadel und Kraeuter", "Heiler"),
    ("Dietrichwerkzeug", "ein Dietrichset oder eine Miniaturfeile", "Mechaniker"),
    ("Bergbauwerkzeug", "Spitzhacke, Schaufel oder Stemmeisen", "Bergmann"),
    ("Alchemiewerkzeug", "Mörser, Stößel und Fläschchen", "Kraeuterkundiger"),
)


def empty_bonuses() -> tuple[dict[str, int | float], dict[str, int | float], dict[str, int | float]]:
    return (
        {field: 0 for field in Skills.STAT_FIELDS},
        {field: 0 for field in Skills.TALENT_FIELDS},
        {field: 0 for field in Skills.SKILL_FIELDS},
    )


def skill(name: str, beschreibung: str, condition: str, roll: str, effect: str, years: float, *, skill_field: str | None = None, talent_field: str | None = None, skill_value: float = 1, stat_values: dict[str, float] | None = None, talent_values: dict[str, float] | None = None, related_skill_values: dict[str, float] | None = None) -> dict:
    stat_bonus, talent_bonus, skill_bonus = empty_bonuses()
    if skill_field:
        skill_bonus[skill_field] = skill_value
    if talent_field:
        talent_bonus[talent_field] = 1
    stat_bonus.update(stat_values or {})
    talent_bonus.update(talent_values or {})
    skill_bonus.update(related_skill_values or {})
    return {
        "name": name,
        "beschreibung": beschreibung,
        "bedingung_zum_einsetzen": condition,
        "wuerfe_zum_einsetzen": roll,
        "effekt": effect,
        "stat_bonus": stat_bonus,
        "talent_bonus": talent_bonus,
        "skill_bonus": skill_bonus,
        "alters_anstieg": years,
    }


def add_job_skills(catalogue: list[dict]) -> None:
    job_profiles = (
        ({"Körperkraft": 0.5, "Konstitution": 0.5}, {"Kraftakt": 0.5}),
        ({"Fingerfertigkeit": 0.5, "Klugheit": 0.5}, {"Mechanik": 0.5}),
        ({"Intuition": 0.5, "Gewandheit": 0.5}, {"Sinnesschärfe": 0.5}),
        ({"Charisma": 0.5, "Klugheit": 0.5}, {"Überreden": 0.5}),
        ({"Konstitution": 0.5, "Mut": 0.5}, {"Selbstbeherschung": 0.5}),
    )
    for index, (job, field, lawful, neutral, evil) in enumerate(JOBS):
        base_stats, base_related = job_profiles[index % len(job_profiles)]
        catalogue.append(skill(
            f"{job}: Grundausbildung",
            f"Basiswissen des Berufs {job}; ermöglicht gewöhnliche Arbeiten unter Aufsicht oder mit üblichen Werkzeugen.",
            "Keine Voraussetzung; passende Arbeitsumgebung und Werkzeuge.",
            f"Probe auf {field}.",
            "Einfache Berufsarbeit kann regelgerecht ausgeführt werden.",
            1.0,
            skill_field=field,
            talent_field="Handwerkstalent" if field in {"Metallbearbeitung", "Holzbearbeitung", "Steinbearbeitung", "Lederbearbeitung", "Stoffbearbeitung", "Lebensmittelbearbeitung", "Mechanik", "Malen/Zeichnen"} else None,
            stat_values=base_stats,
            related_skill_values=base_related,
        ))
        for alignment, title, effect, stats, talents, related in (
            ("lawful", lawful, "Arbeit ist nachvollziehbar dokumentiert; Qualität und Sicherheitsregeln stehen im Vordergrund.", {"Klugheit": 0.5, "Charisma": 0.5}, {"Wissenstalent": 0.5}, {"Rechtskunde": 0.5, "Etikette": 0.5}),
            ("neutral", neutral, "Arbeit wird pragmatisch mit den verfügbaren Mitteln erledigt; Improvisation ist erlaubt.", {"Intuition": 0.5, "Gewandheit": 0.5}, {"Naturtalent": 0.5}, {"Wildnisleben": 0.5, "Orrientierung": 0.5}),
            ("evil", evil, "Arbeit darf andere ausnutzen, täuschen oder schädigen; die Folgen liegen bei der Spielleitung.", {"Fingerfertigkeit": 0.5, "Charisma": -0.5}, {"Geseltschaftstalent": -0.5}, {"Gassenwissen": 0.5, "Verbergen": 0.5, "Etikette": -0.5}),
        ):
            catalogue.append(skill(
                f"{job}: {title}",
                f"{alignment.capitalize()}e Verfeinerung der Ausbildung {job}.",
                f"Voraussetzung: {job}: Grundausbildung; passende Arbeitsumgebung und Werkzeuge.",
                f"Probe auf {field}.",
                effect,
                2.0,
                skill_field=field,
                skill_value=1.5,
                stat_values=stats,
                talent_values=talents,
                related_skill_values=related,
            ))


def add_weapon_skills(catalogue: list[dict]) -> None:
    for family, item, family_skills, actions in WEAPON_FAMILIES:
        base_names: list[str] = []
        for action_index, action in enumerate(actions):
            name = f"{family}: {action}"
            base_names.append(name)
            catalogue.append(skill(
                name,
                f"Grundtechnik {action.lower()} mit {family.lower()}-artigen Waffen.",
                f"Benötigt {item}; keine weitere Voraussetzung.",
                "Passende Kampfprobe nach Spielregeln.",
                f"Ermöglicht die Basisaktion {action.lower()} mit {family_skills}.",
                BASE_TRAINING,
                talent_field="Körpertalent",
                stat_values=({"Mut": 0.5, "Körperkraft": 0.5} if action_index < 2 else {"Intuition": 0.5, "Gewandheit": 0.5}),
                related_skill_values=({"Körperbeherschung": 0.5} if action == "Ausweichen" else {"Selbstbeherschung": 0.5}),
            ))
        for advanced, prerequisite, effect, stats, related in (
            ("Finte", base_names[0], "Täusche einen Angriff an und zwinge das Ziel zu einer Reaktion.", {"Fingerfertigkeit": 1, "Charisma": 0.5}, {"Betöhren": 0.5}),
            ("Winkelangriff", base_names[1], "Nutze eine Öffnung oder ungünstige Deckung des Ziels aus.", {"Intuition": 1, "Gewandheit": 0.5}, {"Sinnesschärfe": 0.5}),
            ("Kontrollierter Rueckzug", base_names[3], "Löse dich geordnet aus dem Nahkampf oder wechsle Deckung.", {"Gewandheit": 1, "Körperkraft": -0.5}, {"Körperbeherschung": 0.5}),
        ):
            name = f"{family}: {advanced}"
            catalogue.append(skill(
                name,
                f"Fortgeschrittene {family.lower()}-Technik.",
                f"Voraussetzung: {prerequisite}; benötigt {item}.",
                "Erschwerte passende Kampfprobe.",
                effect,
                INTERMEDIATE_TRAINING,
                talent_field="Körpertalent",
                stat_values=stats,
                related_skill_values=related,
            ))
        for master, prerequisite, effect, stats, related in (
            ("Meisterfinte", f"{family}: Finte", "Verbinde Täuschung und Stellungsspiel, um einen klaren Vorteil zu schaffen.", {"Fingerfertigkeit": 1.5, "Charisma": 0.5}, {"Betöhren": 1}),
            ("Wundenutzen", f"{family}: Winkelangriff", "Triff eine bereits verletzte oder ungeschützte Stelle für einen stärkeren erzählerischen Effekt.", {"Intuition": 1.5, "Mut": 0.5}, {"Sinnesschärfe": 1, "HeilkundeWunden": 0.5}),
        ):
            catalogue.append(skill(
                f"{family}: {master}",
                f"Anspruchsvolle {family.lower()}-Technik mit hohem Trainingsaufwand.",
                f"Voraussetzung: {prerequisite}; benötigt {item}.",
                "Schwere passende Kampfprobe.",
                effect,
                ADVANCED_TRAINING,
                talent_field="Körpertalent",
                talent_values={"Körpertalent": 1.5},
                stat_values=stats,
                related_skill_values=related,
            ))


def add_tool_skills(catalogue: list[dict]) -> None:
    for tool, item, job in TOOLS:
        basics = ("Sicherer Griff", "Grundarbeit", "Pflege")
        for action_index, action in enumerate(basics):
            catalogue.append(skill(
                f"{tool}: {action}",
                f"Grundtechnik für {tool.lower()}.",
                f"Benötigt {item}; keine weitere Voraussetzung.",
                "Passende Handwerksprobe.",
                f"Ermöglicht {action.lower()} ohne vermeidbare Materialverschwendung.",
                BASE_TRAINING,
                talent_field="Handwerkstalent",
                stat_values=({"Fingerfertigkeit": 0.5, "Intuition": 0.5} if action_index < 2 else {"Klugheit": 0.5, "Konstitution": 0.5}),
                related_skill_values={"Mechanik": 0.5},
            ))
        for advanced, prerequisite, effect, stats, related in (
            ("Praezisionsarbeit", f"{tool}: Grundarbeit", "Bearbeite kleine Teile, enge Stellen oder empfindliches Material.", {"Fingerfertigkeit": 1, "Intuition": 0.5}, {"Mechanik": 0.5}),
            ("Feldreparatur", f"{tool}: Pflege", "Repariere ein einfaches Werkzeug oder Arbeitsobjekt mit begrenzten Mitteln.", {"Klugheit": 0.5, "Körperkraft": 0.5}, {"Mechanik": 0.5, "Wildnisleben": 0.5}),
        ):
            catalogue.append(skill(
                f"{tool}: {advanced}",
                f"Fortgeschrittene Technik für {tool.lower()}.",
                f"Voraussetzung: {prerequisite}; benötigt {item} und Grundausbildung {job}.",
                "Erschwerte Handwerksprobe.",
                effect,
                INTERMEDIATE_TRAINING,
                talent_field="Handwerkstalent",
                stat_values=stats,
                related_skill_values=related,
            ))
        catalogue.append(skill(
            f"{tool}: Meisterarbeit",
            f"Anspruchsvolle, mehrstufige Arbeit mit {tool.lower()}.",
            f"Voraussetzung: {tool}: Praezisionsarbeit und {tool}: Feldreparatur; benötigt {item} und Grundausbildung {job}.",
            "Schwere Handwerksprobe über mehrere Arbeitsschritte.",
            "Ermöglicht eine besonders saubere, haltbare oder unauffällige Ausführung nach Entscheidung der Spielleitung.",
            ADVANCED_TRAINING,
            talent_field="Handwerkstalent",
            talent_values={"Handwerkstalent": 1.5},
            stat_values={"Fingerfertigkeit": 1.5, "Klugheit": 0.5},
            related_skill_values={"Mechanik": 1, "Selbstbeherschung": 0.5},
        ))


def normalise_seed_skill(entry: dict) -> dict:
    """Keep the legacy seed skills compatible with the catalogue-wide bonus limit."""
    entry = json.loads(json.dumps(entry))
    for field_name in ("stat_bonus", "talent_bonus", "skill_bonus"):
        entry[field_name] = {
            field: max(-2, min(2, value))
            for field, value in entry[field_name].items()
        }
    return entry


def build() -> dict[str, dict]:
    existing = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
    catalogue = [normalise_seed_skill(existing[f"Skill_{index}"]) for index in (1, 2)]
    add_job_skills(catalogue)
    add_weapon_skills(catalogue)
    add_tool_skills(catalogue)
    return {f"Skill_{index}": entry for index, entry in enumerate(catalogue, start=1)}


def main() -> None:
    catalogue = build()
    SKILLS_PATH.write_text(json.dumps(catalogue, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(catalogue)} skills to {SKILLS_PATH}")


if __name__ == "__main__":
    main()