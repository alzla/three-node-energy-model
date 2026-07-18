# Drei-Städte Energiemodell (PyPSA) — 2019

## Was macht dieses Projekt?

Dieses Skript simuliert ein einfaches Stromnetz mit drei Städten in Deutschland:
**Hamburg**, **Darmstadt** und **Dresden**. Jede Stadt hat eigene erneuerbare
Energie (Wind oder PV) und einen eigenen Stromverbrauch (Load). Zusätzlich
gibt es ein Gaskraftwerk und einen Import-Knoten (Strom vom Markt, zum
EPEX-Spotpreis). Alle Knoten sind über Leitungen (Links) miteinander
verbunden, sodass Strom zwischen den Städten fließen kann.

Das Modell rechnet für **jede Stunde des Jahres 2019** (8760 Stunden) aus,
wie der Strombedarf am günstigsten gedeckt wird — mit dem Solver `highs`
über die Bibliothek **PyPSA**.

## Verwendete Daten

Alle Wetter- und Preisdaten kommen aus 2019 und liegen als CSV-Dateien vor:

| Datei | Inhalt |
|---|---|
| `wind_hamburg_80m.csv` | Windleistung Hamburg, 80m Nabenhöhe (renewables.ninja) |
| `pv_da.csv` | PV-Leistung Darmstadt (renewables.ninja) |
| `pv_dd.csv` | PV-Leistung Dresden (renewables.ninja) |
| `wind_dd.csv` | Windleistung Dresden (renewables.ninja) |
| `epex_de_2019_hourly.csv` | Stündliche Strompreise EPEX Deutschland (€/MWh) |

Die Rohdaten (in kW) werden im Skript normiert (`p_max_pu`, Wert zwischen 0
und 1), damit sie zur installierten Leistung (`p_nom`) jedes Generators
passen.

## Aufbau des Modells

- **Hamburg**: Wind-Generator (2 MW) + Load (1.2 MW)
- **Darmstadt**: PV-Generator (2 MW) + Batterie (5 MW / 4h) + Load (0.6 MW)
- **Dresden**: PV-Generator (1 MW) + Wind-Generator (1 MW) + Load (0.9 MW)
- **GasPlant**: Gas-Generator (3 MW, Grenzkosten 50 €/MWh)
- **GridImport**: Import-Generator (3 MW, Kosten = stündlicher EPEX-Preis)

Alle Knoten sind über **Links** verbunden (Wirkungsgrad 98%):
- Stadt ↔ Stadt: HA-DA, HA-DD, DA-DD (bidirektional, je 0.5 MW)
- Gas → Stadt: Gas-HA, Gas-DA, Gas-DD (nur Einspeisung, je 1.0 MW)
- Import → Stadt: Import-HA, Import-DA, Import-DD (nur Einspeisung, je 1.0 MW)

Der Solver optimiert alle 8760 Stunden gleichzeitig und minimiert die
Gesamtkosten (Gas + Import), unter Einhaltung von Lastdeckung und
Leitungskapazitäten.

## Skript ausführen

```bash
pip install pypsa highspy pandas matplotlib --break-system-packages
python three_node_epex.py
```

Das Skript erzeugt automatisch:
- `battery_soc.png` — Ladezustand der Batterie (Winter- und Sommerwoche)
- `network_flow_diagram.png` — mittlere Leistungsflüsse im Netzwerk
- `link_utilization.png` — durchschnittliche Auslastung jeder Leitung
- `summary_results.csv` — Zusammenfassung der wichtigsten Kennzahlen

## Ergebnisse (Jahr 2019)

| Kennzahl | Wert | Einheit |
|---|---|---|
| Wind Hamburg — gesamt | 4724,8 | MWh |
| PV Darmstadt — gesamt | 2406,6 | MWh |
| PV + Wind Dresden — gesamt | 6828,6 | MWh |
| Gas — gesamt | 685,4 | MWh |
| Gesamtverbrauch (alle Städte) | 23652,0 | MWh |
| Gesamtkosten Gas | 34,3 | K€ |

Erneuerbare Energie (Wind + PV) deckt zusammen etwa **60%** des
Gesamtverbrauchs. Der Rest kommt größtenteils über den Import-Knoten
(zum Marktpreis), das Gaskraftwerk wird kaum genutzt.

### Monatliche Erzeugung

![Monatliche Erzeugung](month_gen.png)

Wind Hamburg liefert das ganze Jahr über relativ konstant Strom. Dresden
(PV + Wind kombiniert) hat die höchste Erzeugung, besonders im Frühjahr
(März: 727 MWh). Das Gaskraftwerk wird fast nur im Januar (356 MWh) und
November (110 MWh) gebraucht — den Monaten mit der geringsten
PV-Erzeugung.

### Leitungsauslastung

![Leitungsauslastung](link_utilization.png)

Die Stadt-zu-Stadt-Leitungen sind stark ausgelastet: **DA↔DD mit 85,5%**
und **HA↔DA mit 83,2%** — der Strom aus Hamburg und Dresden wird also
regelmäßig zwischen den Städten verschoben. Die Gas-Leitungen sind kaum
ausgelastet (unter 7%), was zeigt, dass Gas nur als letzte Reserve dient.
Die Import-Leitungen liegen bei 26–42%.

### Leistungsflüsse im Netzwerk

![Netzwerk Flüsse](network_flow_diagram.png)

Der größte durchschnittliche Fluss ist **Import → Dresden (0,42 MW)**,
gefolgt von **Darmstadt → Hamburg (0,36 MW)**. Das zeigt: Dresden braucht
trotz eigener Erzeugung zusätzlich Import-Strom, während Darmstadt (dank
PV und Batterie) Überschuss nach Hamburg exportiert.

## Kurzes Fazit

Das Modell zeigt, dass ein Verbund aus Wind, PV und einer Batterie den
Großteil des Bedarfs decken kann, wenn Strom zwischen den Städten
ausgetauscht wird. Gas wird nur in den erzeugungsschwachen Wintermonaten
gebraucht. Der Marktpreis-Import bleibt aber eine wichtige Ergänzung,
besonders für Dresden.
