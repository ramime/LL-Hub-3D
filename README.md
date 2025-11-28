# LL-Hub-3D

Dieses Repository enthält die parametrischen 3D-Modelle für den LightningLines Hub, erstellt mit FreeCAD und Python.

## Überblick

Das Projekt nutzt einen "Code-First" Ansatz, um 3D-Geometrie zu erzeugen.
*   **Input:** Parameter in `config/parameters.json` und globale Maße aus `../LL-Common/GLOBAL_DIMENSIONS.json`.
*   **Logik:** Python-Skripte in `src/models/` definieren die Geometrie.
*   **Output:** STEP (Konstruktion), STL (Druck) und 3MF (Multi-Color Druck) in `output/`.

Detaillierte Dokumentation zum Workflow findest du in [../LL-Common/FREECAD_WORKFLOW.md](../LL-Common/FREECAD_WORKFLOW.md).

## Voraussetzungen

*   **FreeCAD 1.0** (oder neuer) muss installiert sein.
*   Die `freecadcmd.exe` muss bekannt sein (siehe Aufruf unten).

## Ausführung

Das Hauptskript `src/main.py` steuert die Generierung aller Modelle. Es muss über die FreeCAD-Kommandozeile ausgeführt werden, damit die FreeCAD-Python-Module verfügbar sind.

**PowerShell Beispiel:**

```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" .\src\main.py
```

*(Passe den Pfad zu FreeCAD ggf. an, falls du es woanders installiert hast.)*

## Output

Nach erfolgreicher Ausführung findest du die Dateien im `output/` Ordner:
*   `output/step/`: Einzelteile für CAD-Austausch.
*   `output/3mf/`: Baugruppen für den 3D-Druck (optimiert für Bambu Studio, inkl. Farb/Material-Trennung).
