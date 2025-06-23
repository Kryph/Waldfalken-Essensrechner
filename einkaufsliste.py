import json
from collections import defaultdict
from fpdf import FPDF
import os


# Daten laden
with open("rezepte.json", "r", encoding="utf-8") as f:
    rezepte = json.load(f)

# Terminal-Eingaben
personen = int(input("Wie viele Personen fahren auf das Con? "))
tage = int(input("Wie viele Tage geht das Con? "))

# Automatische Vorauswahl von Frühstück und Mittagessen
anzahl_fruehstueck = max(0, tage - 1)
anzahl_mittagessen = max(0, tage - 2)

# Hauptgerichte filtern
hauptgerichte = [r for r in rezepte if r["rezeptname"].strip().lower() not in ["frühstück", "mittagessen"]]

# Gerichtsliste anzeigen
print("\nListe der Hauptgerichte:")
for i, rezept in enumerate(hauptgerichte, start=1):
    print(f"{i}: {rezept['rezeptname']}")

auswahl = input("\nGib die Nummern der gewünschten Hauptgerichte ein (z.B. '1 3 5'): ")
auswahl_indizes = [int(i.strip()) - 1 for i in auswahl.split()]

# Datenstrukturen
einkaufsliste = defaultdict(lambda: {"menge": 0, "einheit": "", "detail": None, "originalname": None})
verwendete_rezepte = defaultdict(int)

def zutaten_aufsummieren(rezept, faktor=1):
    portionen = rezept.get("portionen", 10)
    for z in rezept["zutaten"]:
        key = z["zutat"].strip().lower()
        menge_pro_person = z["menge"] / portionen
        gesamtmenge = menge_pro_person * personen * faktor
        einheit = z["einheit"]
        detail = z.get("detail", None)
        originalname = z["zutat"].strip()

        if not einkaufsliste[key]["originalname"]:
            einkaufsliste[key]["originalname"] = originalname

        # Speichere Originalnamen, aber nur wenn noch keiner vorhanden ist
        if not einkaufsliste[key]["originalname"]:
            einkaufsliste[key]["originalname"] = originalname


        if einkaufsliste[key]["einheit"] and einkaufsliste[key]["einheit"] != einheit:
            print(f"⚠️ Achtung: unterschiedliche Einheiten für {key}! Passe diese an und starte das Skript erneut.")

        einkaufsliste[key]["menge"] += gesamtmenge
        einkaufsliste[key]["einheit"] = einheit

        if detail is not None:
            vorhandenes_detail = einkaufsliste[key]["detail"]
            if vorhandenes_detail is None:
                einkaufsliste[key]["detail"] = detail
            else:
                vorhandene_details_liste = vorhandenes_detail.split(", ")
                if detail not in vorhandene_details_liste:
                    einkaufsliste[key]["detail"] = vorhandenes_detail + ", " + detail

def rezept_name_key(rezept):
    """Gibt den normalisierten Namen des Rezepts zurück"""
    return rezept["rezeptname"].strip()

# Frühstück & Mittagessen berechnen
for rezept in rezepte:
    name = rezept["rezeptname"].strip()
    if name.lower() == "frühstück" and anzahl_fruehstueck > 0:
        zutaten_aufsummieren(rezept, anzahl_fruehstueck)
        verwendete_rezepte[name] += anzahl_fruehstueck
    elif name.lower() == "mittagessen" and anzahl_mittagessen > 0:
        zutaten_aufsummieren(rezept, anzahl_mittagessen)
        verwendete_rezepte[name] += anzahl_mittagessen

# Hauptgerichte berechnen
for idx in auswahl_indizes:
    rezept = hauptgerichte[idx]
    name = rezept_name_key(rezept)
    zutaten_aufsummieren(rezept, 1)
    verwendete_rezepte[name] += 1

# Übersicht im Terminal
print("\n📋 Verwendete Rezepte und deren Anzahl:")
for name, anzahl in verwendete_rezepte.items():
    print(f"  - {name}: {anzahl}x")
print()

# PDF-Klasse
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 16)
        self.cell(0, 10, "Einkaufsliste für das Con", border=0, ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'R')

def create_pdf(dateiname, zutaten_liste):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 10, "Menge", 1, 0, 'C', fill=True)
    pdf.cell(80, 10, "Zutat", 1, 0, 'C', fill=True)
    pdf.cell(25, 10, "Einheit", 1, 0, 'C', fill=True)
    pdf.cell(60, 10, "Details", 1, 1, 'C', fill=True)

    pdf.set_font("Arial", size=12)
    fill = False
    for menge, name, einheit, detail in zutaten_liste:
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(25, 10, str(menge), 1, 0, 'C', fill=fill)
        pdf.cell(80, 10, name, 1, 0, 'L', fill=fill)
        pdf.cell(25, 10, einheit, 1, 0, 'C', fill=fill)
        pdf.cell(60, 10, detail or "", 1, 1, 'L', fill=fill)
        fill = not fill

    pdf.output(dateiname)

# Zutatenliste für PDF erstellen
zutaten_pdf = []
for zutat, daten in einkaufsliste.items():
    menge = round(daten["menge"], 2)
    einheit = daten["einheit"] or ""
    name = name = daten["originalname"] or zutat
    detail = daten["detail"] or ""
    zutaten_pdf.append((menge, name, einheit, detail))
zutaten_pdf.sort(key=lambda x: x[1].lower())  # Sortiert nach Zutat (Feld x[1])

create_pdf("einkaufsliste.pdf", zutaten_pdf)
print("✅ PDF 'einkaufsliste.pdf' wurde erstellt.\n")

def create_rezept_pdfs(verwendete_rezepte, rezepte, personen):
    import os
    from fpdf import FPDF

    ordner = "rezepte"
    if os.path.exists(ordner):
        for datei in os.listdir(ordner):
            pfad = os.path.join(ordner, datei)
            if os.path.isfile(pfad):
                os.remove(pfad)
        print("\n🧹 Alte Rezepte wurden gelöscht.\n")
    else:
        os.makedirs(ordner)

    class RezeptPDF(FPDF):
        def header(self):
            self.set_font("Arial", 'B', 16)
            self.multi_cell(0, 10, self.title, align='L')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", 'I', 8)
            self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'R')

    def rezept_by_name(name):
        for r in rezepte:
            if r["rezeptname"].strip().lower() == name.strip().lower():
                return r
        return None

    for rezeptname, anzahl in verwendete_rezepte.items():
        rezept = rezept_by_name(rezeptname)
        if not rezept:
            print(f"❌ Rezept nicht gefunden: {rezeptname}")
            continue

        pdf = RezeptPDF()
        pdf.title = rezept["rezeptname"]
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Optionaler Hinweis
        hinweis = rezept.get("hinweis") or rezept.get("anmerkung") or ""
        if hinweis:
            pdf.set_font("Arial", 'I', 12)
            pdf.multi_cell(0, 8, f"Achtung: {hinweis}")
            pdf.ln(3)

        # Zutaten als Tabelle
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Zutaten", ln=1)
        pdf.set_font("Arial", '', 12)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(25, 8, "Menge", 1, 0, 'C', fill=True)
        pdf.cell(25, 8, "Einheit", 1, 0, 'C', fill=True)
        pdf.cell(80, 8, "Zutat", 1, 0, 'C', fill=True)
        pdf.cell(60, 8, "Detail", 1, 1, 'C', fill=True)

        portionen = rezept.get("portionen", 10)
        faktor = personen / portionen
        for z in rezept["zutaten"]:
            menge = round(z["menge"] * faktor, 2)
            einheit = z["einheit"]
            name = z["zutat"]
            detail = z.get("detail", "") or ""
            pdf.cell(25, 8, str(menge), 1)
            pdf.cell(25, 8, einheit, 1)
            pdf.cell(80, 8, name, 1)
            pdf.cell(60, 8, detail, 1)
            pdf.ln()

        pdf.ln(5)

        # Zubereitung als nummerierte Liste
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Zubereitung", ln=1)
        pdf.set_font("Arial", '', 12)
        for i, schritt in enumerate(rezept.get("zubereitung", []), start=1):
            pdf.multi_cell(0, 8, f"{i}. {schritt}")
        pdf.ln(5)

        # Platz für Anmerkungen mit Rahmen (auf neuer Seite)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Anmerkungen für nächste Planung", ln=1)
        pdf.set_font("Arial", '', 12)
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        zeilenhoehe = 10
        box_hoehe = zeilenhoehe * 8
        box_breite = 190
        pdf.rect(start_x, start_y, box_breite, box_hoehe)
        for _ in range(8):
            pdf.cell(box_breite, zeilenhoehe, "", ln=1)

        # Speichern
        filename = os.path.join(ordner, f"{rezept['rezeptname'].replace(' ', '_')}.pdf")
        pdf.output(filename)
        print(f"📄 Rezept-PDF erstellt: {filename}")

# ✅ Aufrufen nach der Einkaufsliste
create_rezept_pdfs(verwendete_rezepte, rezepte, personen)
