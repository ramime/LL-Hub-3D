# Hub Slot Varianten

Dieses Dokument definiert die verschiedenen Typen von Hub-Slots, die im LightningLines Hub-System verfügbar sind.
Alle Slots teilen sich die gleiche äußere Geometrie (Sechseck mit Schräge) und sind kompatibel mit den Deckeln. Sie unterscheiden sich in ihren internen Befestigungsmöglichkeiten für Elektronik.

## 1. Slot_Basic
Die Grundlage für alle anderen Slots. Er enthält die wesentlichen Funktionen für die mechanische Verbindung und Stromverteilung.

**Features:**
*   **Geometrie:** Standard-Sechseck mit Schräge, Deckel-Falz, Abstandsrand.
*   **Boden-Löcher:** 6x Löcher (Radius 40mm) zur Bodenbefestigung.
*   **Magnet-Halterungen:** 4x Pfeiler (Mitte + 3 Außen) für magnetische Kopplung.
*   **PogoPin-Halterungen:** 4x Pfeiler (Nordseite) für PogoPin-Platine.

**Verwendung:**
*   Wird für Slots verwendet, die nur Strom/Daten durchleiten oder keine spezielle Elektronik enthalten.

## 2. Slot_Controller
Entwickelt für die Aufnahme der Haupt-Hub-Controller-Platine.

**Features:**
*   **Basis:** Enthält alle Features von **Slot_Basic**.
*   **Controller-Halterungen:** 6x Pfeiler spezifisch für die Hub-Controller-Platine.

**Verwendung:**
*   Typischerweise einmal pro Hub-Baugruppe (z.B. Slot 2 bei Typ A, Slot 5 bei Typ B).

## 3. Slot_USB
Entwickelt für die Aufnahme einer USB-Anschluss-Platine (Südseite).

**Features:**
*   **Basis:** Enthält alle Features von **Slot_Basic**.
*   **USB-Halterungen:** 4x Pfeiler (Südseite, 14mm Quadrat) für USB-Platine.
*   **USB-Ausschnitt:** Rechteckiger Ausschnitt (13x7mm) in der Südwand für den USB-Stecker.

**Verwendung:**
*   Wird für Slots verwendet, die eine externe USB-Konnektivität bereitstellen (z.B. Slot 3).
