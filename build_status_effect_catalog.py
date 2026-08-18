"""Build the default catalogue of injuries, illnesses, poisons, and lasting buffs."""

from __future__ import annotations

import json
from pathlib import Path

import Statuseffekts


STATUS_PATH = Path(__file__).parent / "data" / "Global" / "StatusEffekts.json"


def empty_bonuses() -> tuple[dict[str, int | float], dict[str, int | float]]:
    return (
        {field: 0 for field in Statuseffekts.EFFECT_STAT_FIELDS},
        {field: 0 for field in Statuseffekts.Skills.TALENT_FIELDS},
    )


def format_hours(hours: int | float) -> str:
    if 0 < hours < 1:
        return f"{round(hours * 60)} Minuten"
    return f"{hours:g} Stunden"


def effect(name: str, description: str, duration: int | float, death_time: int | float = 0, *, stats: dict[str, int | float] | None = None, talents: dict[str, int | float] | None = None) -> dict:
    stat_bonus, talent_bonus = empty_bonuses()
    stat_bonus.update(stats or {})
    talent_bonus.update(talents or {})
    return {
        "name": name,
        "beschreibung": f"{description} Dauer: {format_hours(duration)}." + (f" Ohne Behandlung kann der Zustand nach {format_hours(death_time)} tödlich werden." if death_time else ""),
        "default duration": duration,
        "default time to death": death_time,
        "stat_bonus": stat_bonus,
        "talent_bonus": talent_bonus,
    }


def build() -> dict[str, dict]:
    catalogue = [
        effect("Schnittwunde I - oberflächlich", "Kleine Klingenwunde, schmerzhaft aber sauber versorgt.", 24, stats={"Fingerfertigkeit": -0.5}),
        effect("Schnittwunde II - tief", "Tiefe Klingenwunde mit Blutverlust; Ruhe und Verband sind nötig.", 72, stats={"Fingerfertigkeit": -1, "Konstitution": -0.5}, talents={"Körpertalent": -0.5}),
        effect("Schnittwunde III - zerfetzt", "Schwere Schnittverletzung mit anhaltendem Blutverlust und hohem Infektionsrisiko.", 168, 72, stats={"Fingerfertigkeit": -1.5, "Konstitution": -1, "Körperkraft": -0.5}, talents={"Körpertalent": -1}),
        effect("Stichwunde I - Fleischwunde", "Flache Stichverletzung durch Dolch, Speer oder Pfeil.", 48, stats={"Gewandheit": -0.5}),
        effect("Stichwunde II - tief", "Tiefe Stichverletzung; jede starke Bewegung belastet die Wunde.", 120, 96, stats={"Konstitution": -1, "Körperkraft": -0.5}, talents={"Körpertalent": -0.5}),
        effect("Stichwunde III - kritisch", "Kritische Stichverletzung in Rumpf oder Hals; unverzügliche Behandlung ist nötig.", 240, 24, stats={"Konstitution": -1.5, "Körperkraft": -1, "Mut": -0.5}, talents={"Körpertalent": -1}),
        effect("Pfeilwunde I - streifend", "Pfeil oder Bolzen hat nur Fleisch gestreift.", 48, stats={"Gewandheit": -0.5}),
        effect("Pfeilwunde II - steckend", "Pfeil oder Bolzen steckt noch oder hat eine tiefe Wunde hinterlassen.", 144, 72, stats={"Fingerfertigkeit": -1, "Konstitution": -0.5}),
        effect("Pfeilwunde III - Durchschuss", "Durchschuss mit schwerem Blutverlust; Behandlung und lange Ruhe sind erforderlich.", 240, 36, stats={"Konstitution": -1.5, "Körperkraft": -1}, talents={"Körpertalent": -1}),
        effect("Quetschung I - Prellung", "Prellung durch Keule, Sturz oder Schildstoß.", 36, stats={"Gewandheit": -0.5}),
        effect("Quetschung II - tiefer Bluterguss", "Schwere Prellung; Kraft und Beweglichkeit sind eingeschränkt.", 96, stats={"Körperkraft": -1, "Gewandheit": -0.5}),
        effect("Quetschung III - innere Verletzung", "Mögliche innere Verletzung nach einem harten Treffer oder Sturz.", 168, 72, stats={"Konstitution": -1.5, "Körperkraft": -1}, talents={"Körpertalent": -0.5}),
        effect("Brandwunde I - versengt", "Leichte Verbrennung durch Feuer, Dampf oder Glut.", 48, stats={"Fingerfertigkeit": -0.5}),
        effect("Brandwunde II - blasenbildend", "Schmerzhafte Verbrennung mit Blasen und empfindlicher Haut.", 144, stats={"Fingerfertigkeit": -1, "Konstitution": -0.5}),
        effect("Brandwunde III - tief", "Tiefe Verbrennung; Bewegung und Belastung sind stark eingeschränkt.", 336, 120, stats={"Fingerfertigkeit": -1.5, "Konstitution": -1, "Körperkraft": -0.5}, talents={"Körpertalent": -1}),
        effect("Knochenbruch I - Haarriss", "Kleiner Knochenriss; Schiene und Schonung verhindern eine Verschlimmerung.", 336, stats={"Gewandheit": -1, "Körperkraft": -0.5}),
        effect("Knochenbruch II - Arm", "Gebrochener Arm oder Handgelenk; zweihändige Arbeit und Paraden sind stark erschwert.", 672, stats={"Fingerfertigkeit": -2, "Körperkraft": -1}, talents={"Körpertalent": -1}),
        effect("Knochenbruch III - Bein", "Gebrochenes Bein oder Knöchel; schnelles Gehen, Ausweichen und Reiten sind kaum möglich.", 840, stats={"Gewandheit": -2, "Konstitution": -1}, talents={"Körpertalent": -1.5}),
        effect("Knochenbruch IV - mehrfach", "Mehrfacher oder offener Bruch; fachkundige Versorgung ist dringend notwendig.", 1440, 168, stats={"Körperkraft": -2, "Gewandheit": -2, "Konstitution": -1.5}, talents={"Körpertalent": -2}),
        effect("Wundinfektion I - gereizt", "Gerötete, schmerzende Wunde; Reinigung und Beobachtung sind nötig.", 96, stats={"Konstitution": -0.5}),
        effect("Wundinfektion II - fiebrig", "Entzündete Wunde mit Fieber und Schwäche.", 168, 120, stats={"Konstitution": -1, "Klugheit": -0.5}, talents={"Körpertalent": -0.5}),
        effect("Wundbrand - schwer", "Unbehandelte Infektion mit hohem Risiko für bleibende Schäden oder Tod.", 336, 48, stats={"Konstitution": -2, "Körperkraft": -1, "Mut": -0.5}, talents={"Körpertalent": -1.5}),
        effect("Erkaeltung - leicht", "Husten, Frösteln und schlechter Schlaf.", 120, stats={"Konstitution": -0.5, "Klugheit": -0.5}),
        effect("Sumpffieber - fiebrig", "Wellen aus Fieber, Schüttelfrost und Erschöpfung nach Kontakt mit Sumpfwasser oder Insekten.", 240, stats={"Konstitution": -1, "Klugheit": -1}, talents={"Naturtalent": -0.5}),
        effect("Sumpffieber - schwer", "Starkes Fieber, Orientierungslosigkeit und wiederkehrende Schwäche.", 480, 120, stats={"Konstitution": -1.5, "Klugheit": -1.5, "Intuition": -0.5}, talents={"Körpertalent": -1}),
        effect("Tunnelhusten", "Staub und Pilzsporen reizen die Lunge; lange Belastung verschlimmert den Zustand.", 336, stats={"Konstitution": -1, "Körperkraft": -0.5}),
        effect("Magenfäule", "Verdorbene Nahrung verursacht Krämpfe, Durst und Schwäche.", 72, stats={"Konstitution": -1, "Körperkraft": -0.5}),
        effect("Ruhr", "Anhaltende Darmerkrankung mit Flüssigkeitsverlust; sauberes Wasser und Ruhe helfen.", 168, 96, stats={"Konstitution": -1.5, "Körperkraft": -1}),
        effect("Schlafmohn - benommen", "Leichtes Schlafmittel; Reaktionen und Wahrnehmung sind gedämpft.", 12, stats={"Intuition": -1, "Gewandheit": -0.5}, talents={"Wissenstalent": -0.5}),
        effect("Schlafmohn - tief", "Starkes Schlafmittel; die Person schläft oder kann nur schwer wach bleiben.", 24, stats={"Klugheit": -2, "Intuition": -1.5, "Gewandheit": -1}),
        effect("Nervengift - kribbelnd", "Mildes Kontaktgift verursacht Zittern und taube Finger.", 24, stats={"Fingerfertigkeit": -1, "Gewandheit": -0.5}),
        effect("Nervengift - lähmend", "Starkes Gift schwächt Muskeln und Koordination.", 48, 72, stats={"Fingerfertigkeit": -2, "Gewandheit": -1.5, "Körperkraft": -1}, talents={"Körpertalent": -1}),
        effect("Blutgift - schwach", "Gift im Blut verursacht Schwindel und Kraftverlust.", 48, stats={"Konstitution": -1, "Körperkraft": -0.5}),
        effect("Blutgift - tödlich", "Starkes Blutgift; ohne Gegenmittel oder Heilkunde droht Organversagen.", 96, 24, stats={"Konstitution": -2, "Körperkraft": -1.5, "Klugheit": -0.5}, talents={"Körpertalent": -1}),
        effect("Klingenlähmer - rasend", "Konzentriertes Klingen- oder Insektengift verursacht rasche Lähmung und Atemnot.", 12, 6, stats={"Konstitution": -2, "Fingerfertigkeit": -2, "Gewandheit": -2}, talents={"Körpertalent": -2}),
        effect("Zerquetschter Brustkorb", "Schwerer Treffer durch Keule, Einsturz oder Fall; Atmung ist nur noch mühsam möglich.", 24, 8, stats={"Konstitution": -2, "Körperkraft": -2, "Mut": -1}, talents={"Körpertalent": -2}),
        effect("Lungenblutung", "Kritische Stich-, Pfeil- oder Brandverletzung der Lunge; jeder Atemzug kostet Kraft.", 18, 4, stats={"Konstitution": -2, "Körperkraft": -1.5, "Gewandheit": -1}, talents={"Körpertalent": -1.5}),
        effect("Kritische Halsverletzung", "Durchtrennte Kehle oder vergleichbare schwere Halsverletzung; sofortige Versorgung entscheidet über das Überleben.", 0.1, 0.07, stats={"Konstitution": -2, "Körperkraft": -2, "Mut": -1}, talents={"Körpertalent": -2}),
        effect("Offene Halsschlagader", "Schwere Verletzung einer Halsarterie mit raschem Blutverlust; nur unverzügliche Versorgung kann helfen.", 0.1, 0.05, stats={"Konstitution": -2, "Körperkraft": -2, "Gewandheit": -1}, talents={"Körpertalent": -2}),
        effect("Herzstich", "Kritische Stichverletzung im Brustraum; der Zustand ist unmittelbar lebensbedrohlich.", 0.1, 0.03, stats={"Konstitution": -2, "Körperkraft": -2, "Mut": -1.5}, talents={"Körpertalent": -2}),
        effect("Kritische Hirnverletzung", "Schwere Kopfverletzung durch Sturz, Bolzen oder Keulentreffer; Bewusstsein und Atmung versagen rasch.", 0.1, 0.05, stats={"Klugheit": -2, "Intuition": -2, "Konstitution": -2}, talents={"Wissenstalent": -2, "Körpertalent": -2}),
        effect("Zertrümmerte Halswirbelsäule", "Kritische Verletzung von Nacken und Wirbelsäule; ohne sofortige Stabilisierung droht rasches Atemversagen.", 0.1, 0.07, stats={"Körperkraft": -2, "Gewandheit": -2, "Konstitution": -2}, talents={"Körpertalent": -2}),
        effect("Kraeuterstärkung", "Langanhaltender Kräutersud stärkt Kreislauf und Widerstandskraft.", 168, stats={"Konstitution": 0.5, "Körperkraft": 0.5}, talents={"Körpertalent": 0.5}),
        effect("Wachsalbe", "Langanhaltende Salbe gegen Steifheit und kalte Gelenke.", 120, stats={"Gewandheit": 0.5, "Fingerfertigkeit": 0.5}),
        effect("Bergarbeitertee", "Bitterer Tee hält wach und stabilisiert die Nerven bei langer Arbeit im Dunkeln.", 96, stats={"Klugheit": 0.5, "Intuition": 0.5}, talents={"Wissenstalent": 0.5}),
        effect("Ausgeruhter Körper", "Mehrere Nächte guter Schlaf, warme Mahlzeiten und trockene Kleidung stärken Körper und Zuversicht.", 240, stats={"Mut": 1, "Konstitution": 0.5}, talents={"Körpertalent": 0.5}),
        effect("Jägertrank", "Langanhaltender Kräutertrank schärft Sinne und ruhige Bewegung.", 144, stats={"Intuition": 1, "Gewandheit": 0.5}, talents={"Naturtalent": 0.5}),
        effect("Kampfrausch", "Anhaltende Mischung aus Trommeln, Schmerz und Kräutern; macht stark, aber unvorsichtig.", 72, stats={"Mut": 1.5, "Körperkraft": 1, "Klugheit": -0.5, "Intuition": -0.5}, talents={"Körpertalent": 1}),
        effect("Schattenmantel", "Langanhaltende dunkle Tinktur; dämpft Selbstvertrauen, hilft aber beim ungesehenen Verhalten.", 120, stats={"Charisma": -0.5, "Intuition": 0.5}, talents={"Naturtalent": 0.5}),
        effect("Mineraltrank", "Kräuter- und Mineralsud gegen Erschöpfung; stärkt den Kreislauf, macht aber etwas träge.", 144, stats={"Konstitution": 0.5, "Körperkraft": 0.5, "Gewandheit": -0.5}),
    ]
    return {f"StatusEffekt_{index}": entry for index, entry in enumerate(catalogue, start=1)}


def main() -> None:
    catalogue = build()
    STATUS_PATH.write_text(json.dumps(catalogue, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(catalogue)} status effects to {STATUS_PATH}")


if __name__ == "__main__":
    main()