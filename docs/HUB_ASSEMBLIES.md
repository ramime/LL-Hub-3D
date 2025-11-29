# Hub Baugruppen (Assemblies)

Dieses Dokument definiert die zusammengesetzten Hub-Varianten, die aus mehreren Slots bestehen.

## Übersicht
Das Hub-System ist modular und besteht aus einem Gitter von 6 Slots (2 Reihen x 3 Spalten).
Es gibt zwei definierte Standard-Konfigurationen: **Typ A** und **Typ B**.

> **Hinweis:** Zwischen benachbarten Slots werden automatisch Kabelkanäle (Durchbrüche) generiert, um die interne Verkabelung zu ermöglichen.

## Grid Layout
Die Slots sind in einem hexagonalen Muster angeordnet:
*   **Reihe 0 (Oben):** Slots 4, 5, 6
*   **Reihe 1 (Unten):** Slots 1, 2, 3

Die Nummerierung erfolgt von Links nach Rechts.

## Hub_Type_A
Dieser Typ ist für eine Konfiguration ausgelegt, bei der die mittlere Spalte nach **OBEN** versetzt ist.

**Slot-Belegung:**
*   **Slot 1 (Unten Links):** Basic
*   **Slot 2 (Unten Mitte):** **Controller** (Enthält Hub-Controller-Platine)
*   **Slot 3 (Unten Rechts):** **USB** (Enthält USB-Anschluss)
*   **Slot 4 (Oben Links):** Basic
*   **Slot 5 (Oben Mitte):** Basic
*   **Slot 6 (Oben Rechts):** Basic

## Hub_Type_B
Dieser Typ ist für eine Konfiguration ausgelegt, bei der die mittlere Spalte nach **UNTEN** versetzt ist.

**Slot-Belegung:**
*   **Slot 1 (Unten Links):** Basic
*   **Slot 2 (Unten Mitte):** Basic
*   **Slot 3 (Unten Rechts):** **USB** (Enthält USB-Anschluss)
*   **Slot 4 (Oben Links):** Basic
*   **Slot 5 (Oben Mitte):** **Controller** (Enthält Hub-Controller-Platine)
*   **Slot 6 (Oben Rechts):** Basic

## Feature-Matrix

| Feature | Slot_Basic | Slot_Controller | Slot_USB |
| :--- | :---: | :---: | :---: |
| Geometrie & Deckel-Falz | Ja | Ja | Ja |
| Boden-Löcher (6x) | Ja | Ja | Ja |
| Magnet-Pfeiler (4x) | Ja | Ja | Ja |
| PogoPin-Pfeiler (4x) | Ja | Ja | Ja |
| **Controller-Mounts (6x)** | Nein | **Ja** | Nein |
| **USB-Mounts (4x)** | Nein | Nein | **Ja** |
| **USB-Wand-Ausschnitt** | Nein | Nein | **Ja** |
