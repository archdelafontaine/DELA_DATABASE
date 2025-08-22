# ------------------ Hoofdstuk 1: Imports & Basisvariabelen ------------------
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import sqlite3
import difflib
from datetime import datetime

# Basismap
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV bestanden (voor fallback of eerste inlees)
CONTACTS_CSV = os.path.join(BASE_DIR, "contacts.csv")
PROJECTS_CSV = os.path.join(BASE_DIR, "projects.csv")
FLEMISH_CITIES_CSV = os.path.join(BASE_DIR, "flemish_cities.csv")

# Huidige gebruiker (wordt ingesteld na login)
current_user = None

# Standaard landcode
DEFAULT_CC = "+32"

# Aanhef-keuzes
SALUTATIONS = ["Dhr.", "Mevr.", "Familie", "Firma"]

# Vlaamse steden inladen
def load_flemish_cities():
    cities = {}
    if os.path.exists(FLEMISH_CITIES_CSV):
        with open(FLEMISH_CITIES_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stad = row.get("stad")
                postcode = row.get("postcode")
                if stad and postcode:
                    cities[stad] = postcode
    return cities

FLEMISH_CITIES = load_flemish_cities()

# ------------------ Hoofdstuk 2: Bestands- en Database Config ------------------

import os

# Bepaal de basisdirectory waar het script draait
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pad naar SQLite database (wordt aangemaakt indien niet aanwezig)
DB_PATH = os.path.join(BASE_DIR, "dela_database.db")

# Headerdefinities bestaan enkel nog ter referentie,
# want SQLite gebruikt geen CSV headers. Deze blijven handig
# als standaard veldenlijst bij inserts/updates.
CONTACT_HEADERS = [
    "type", "bedrijf", "rechtsvorm", "aanhef", "voornaam", "achternaam",
    "gsm_cc", "gsm_num", "tel_cc", "tel_num", "email", "functie",
    "rijksregisternummer", "straat", "huisnummer", "postcode", "stad",
    "land", "laatst_gewijzigd_door", "laatst_gewijzigd_op"
]

PROJECT_HEADERS = [
    "bureau", "projectnummer", "gekoppeld_nummer", "klant",
    "projectnaam", "adres", "type_project", "status",
    "laatst_gewijzigd_door", "laatst_gewijzigd_op"
]

# Vlaamse steden → wordt gebruikt in dropdowns
FLEMISH_CITIES_CSV = os.path.join(BASE_DIR, "flemish_cities.csv")

def load_flemish_cities():
    """Laad Vlaamse steden en postcodes uit CSV bestand."""
    cities = {}
    if os.path.exists(FLEMISH_CITIES_CSV):
        with open(FLEMISH_CITIES_CSV, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) == 2:
                    stad, postcode = parts
                    cities[stad] = postcode
    return cities

FLEMISH_CITIES = load_flemish_cities()

# Standaard landcode
DEFAULT_CC = "+32"

# standaard collega's 
DEFAULT_USERS = [
    "Felix",
    "Kris",
    "Michael",
    "Pascal",
    "Heidi V.",
    "Heidi D.",
    "Marie-Roos",
    "Jelle",
    "Quinten",
    "Rik"
]

# ------------------ Hoofdstuk 2.B: SQLite Database helpers ------------------
# Dit stuk vervangt de CSV-opslag door SQLite.
# Het definieert connectie, initialisatie en hulpfuncties om queries uit te voeren.

import sqlite3

def db_connect():
    """Open een SQLite connectie (autocommit uit, moet afgesloten worden)."""
    return sqlite3.connect(DB_PATH)

def db_init():
    """Maak tabellen aan indien ze nog niet bestaan en voeg default users toe."""
    conn = db_connect()
    cur = conn.cursor()

    # Tabel voor contacten
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,               -- 'persoon' of 'bedrijf'
        bedrijf TEXT,
        rechtsvorm TEXT,
        aanhef TEXT,
        voornaam TEXT,
        achternaam TEXT,
        gsm_cc TEXT,
        gsm_num TEXT,
        tel_cc TEXT,
        tel_num TEXT,
        email TEXT,
        functie TEXT,
        rijksregisternummer TEXT,
        straat TEXT,
        huisnummer TEXT,
        postcode TEXT,
        stad TEXT,
        land TEXT,
        laatst_gewijzigd_door TEXT,
        laatst_gewijzigd_op TEXT
    );
    """)

    # Tabel voor projecten
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bureau TEXT,
        projectnummer TEXT,
        gekoppeld_nummer TEXT,
        klant TEXT,
        projectnaam TEXT,
        adres TEXT,
        type_project TEXT,
        status TEXT,
        laatst_gewijzigd_door TEXT,
        laatst_gewijzigd_op TEXT
    );
    """)

    # Tabel voor users (collega’s)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naam TEXT UNIQUE
    );
    """)

    # ✅ Voeg de standaard collega’s toe als ze nog niet bestaan
    for user in DEFAULT_USERS:
        cur.execute("INSERT OR IGNORE INTO users (naam) VALUES (?)", (user,))

    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """
    Algemene hulpfunctie om queries uit te voeren.
    - fetchone=True → geeft 1 rij terug
    - fetchall=True → geeft lijst van rijen terug
    - commit=True → voert commit uit (INSERT/UPDATE/DELETE)
    """
    conn = db_connect()
    conn.row_factory = sqlite3.Row  # maakt dict-achtige toegang mogelijk
    cur = conn.cursor()
    cur.execute(query, params)

    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()

    if commit:
        conn.commit()

    conn.close()
    return result

def db_insert(table, data: dict):
    """Insert een dict in de gegeven tabel."""
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())
    query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
    db_query(query, values, commit=True)

def db_update(table, data: dict, where_clause: str, where_params=()):
    """Update records in een tabel met dict data + WHERE clause."""
    sets = ", ".join([f"{k}=?" for k in data.keys()])
    values = list(data.values()) + list(where_params)
    query = f"UPDATE {table} SET {sets} WHERE {where_clause}"
    db_query(query, values, commit=True)

# ------------------ Hoofdstuk 3: Landcodes & Telefoonnummer-formattering ------------------ 
# ------------------ Landcodes & formattering ------------------ 
# Dropdown toont "+32 (België)" etc.; we bewaren enkel de code (bv. "+32") 
COUNTRY_CODES = [ 
    ("+32", "België"), 
    ("+31", "Nederland"), 
    ("+33", "Frankrijk"), 
    ("+34", "Spanje"), 
    ("+352", "Luxemburg"), 
    ("+41", "Zwitserland"), 
    ("+420", "Tsjechië"), 
    ("+48", "Polen"), 
    ("+36", "Hongarije"), 
    ("+351", "Portugal"), 
    ("+44", "Engeland/VK"), 
    ("+353", "Ierland"), 
    ("+45", "Denemarken"), 
    ("+39", "Italië"), 
    ("+30", "Griekenland"), 
    ("+43", "Oostenrijk"), 
    ("+46", "Zweden"), 
    ("+358", "Finland"), 
    ("+47", "Noorwegen"), 
] 

DEFAULT_CC = "+32" 

def code_label_list(): 
    return [f"{cc} ({name})" for cc, name in COUNTRY_CODES] 

def label_to_code(label): 
    # " +32 (België) " -> "+32" 
    return label.split(" ", 1)[0].strip() 

def code_to_label(code): 
    for cc, name in COUNTRY_CODES: 
        if cc == code: 
            return f"{cc} ({name})" 
    return f"{code} (?)" 

def only_digits(s: str) -> str: 
    return "".join(ch for ch in s if ch.isdigit()) 

def format_phone(cc: str, digits: str, mobile_hint=False) -> str: 
    """Grove formattering: BE specifiek, anderen generiek in paren.""" 
    digits = only_digits(digits) 
    if not cc: 
        cc = DEFAULT_CC 
    # België 
    if cc == "+32": 
        if not digits: 
            return "+32 (0)" 
        if (len(digits) >= 8 and digits[0] == "4") or mobile_hint: 
            first = digits[:3] 
            rest = digits[3:] 
        else: 
            first = digits[:2] 
            rest = digits[2:] 
        pairs = [rest[i:i+2] for i in range(0, len(rest), 2)] 
        pairs = [p for p in pairs if p] 
        pieces = " ".join([first] + pairs) if first else " ".join(pairs) 
        return f"+32 (0) {pieces}".strip() 
    # NL grove benadering 
    if cc == "+31": 
        if not digits: 
            return "+31 (0)" 
        first = digits[:2]; rest = digits[2:] 
        pairs = [rest[i:i+2] for i in range(0, len(rest), 2)] 
        pairs = [p for p in pairs if p] 
        return f"+31 (0) {first} " + " ".join(pairs) if pairs else f"+31 (0) {first}" 
    # Generiek 
    pairs = [digits[i:i+2] for i in range(0, len(digits), 2)] 
    pairs = [p for p in pairs if p] 
    return f"{cc} (0) {' '.join(pairs)}".strip() 

# ------------------ Hoofdstuk 4: Vlaamse steden & Postcodes ------------------ 
# ------------------ Dit stuk probeert de CSV vlaamse_gemeenten.csv te laden met kolommen stad en postcode. Als dat bestand er niet is, wordt een kleine ingebouwde lijst gebruikt (enkel een aantal bekende steden). Resultaat wordt opgeslagen in FLEMISH_CITIES. ------------------ 
# ------------------ Vlaamse steden (stad -> postcode) ------------------ 
def load_flemish_cities(): 
    """ 
    Probeert vlaamse_gemeenten.csv te lezen met kolommen: stad, postcode. 
    Als niet aanwezig, gebruikt een kleine ingebouwde lijst. 
    """ 
    data = {} 
    if os.path.exists(FLEMISH_CITIES_CSV): 
        enc = detect_encoding(FLEMISH_CITIES_CSV) 
        with open(FLEMISH_CITIES_CSV, "r", encoding=enc, newline="") as f: 
            reader = csv.DictReader(f) 
            for row in reader: 
                stad = (row.get("stad") or "").strip() 
                pc = (row.get("postcode") or "").strip() 
                if stad and pc: 
                    data[stad] = pc 
    else: 
        # Kleine testlijst — vervang door CSV om ALLES te hebben 
        sample = [ 
            ("Antwerpen", "2000"), ("Gent", "9000"), ("Brugge", "8000"), 
            ("Leuven", "3000"), ("Kortrijk", "8500"), ("Hasselt", "3500"), 
            ("Mechelen", "2800"), ("Oostende", "8400"), ("Aalst", "9300"), 
            ("Roeselare", "8800"), ("Sint-Niklaas", "9100") 
        ] 
        data = {s: p for s, p in sample} 
    return data 

FLEMISH_CITIES = load_flemish_cities() 

# ------------------ Hoofdstuk 5: Basis GUI (startscherm & login) ------------------
# Startscherm met logo's en login van de gebruiker.
# Dit bepaalt wie 'current_user' is voor logging bij wijzigingen.

from PIL import Image, ImageTk

current_user = None

def show_home():
    global current_user
    home = tk.Toplevel(root)
    home.title("DELA Database")
    home.geometry("600x500")

    # Frame voor logo's
    frame = tk.Frame(home)
    frame.pack(expand=True, fill="both")

    # Logo 1
    try:
        logo1_img = Image.open(os.path.join(BASE_DIR, "logo1.png"))
        logo1_img = logo1_img.resize((250, 120), Image.Resampling.LANCZOS)
        logo1 = ImageTk.PhotoImage(logo1_img)
        lbl1 = tk.Label(frame, image=logo1)
        lbl1.image = logo1
        lbl1.pack(pady=10)
    except Exception:
        tk.Label(frame, text="[Logo 1 ontbreekt]").pack()

    # Logo 2
    try:
        logo2_img = Image.open(os.path.join(BASE_DIR, "logo2.png"))
        logo2_img = logo2_img.resize((250, 120), Image.Resampling.LANCZOS)
        logo2 = ImageTk.PhotoImage(logo2_img)
        lbl2 = tk.Label(frame, image=logo2)
        lbl2.image = logo2
        lbl2.pack(pady=10)
    except Exception:
        tk.Label(frame, text="[Logo 2 ontbreekt]").pack()

    # Login sectie
    tk.Label(frame, text="Selecteer uw naam:", font=("Arial", 12)).pack(pady=5)
    users = ["Felix", "Kris", "Michael", "Pascal"]  # uitbreiden indien nodig
    user_var = tk.StringVar(value=users[0])
    login_cb = ttk.Combobox(frame, values=users, textvariable=user_var, state="readonly")
    login_cb.pack(pady=5)

    def do_login():
        global current_user
        current_user = user_var.get()
        messagebox.showinfo("Ingelogd", f"Welkom {current_user}!")
        home.destroy()

    tk.Button(frame, text="Inloggen", command=do_login).pack(pady=15)

    home.grab_set()

# ------------------ Hoofdstuk 6: Projectenmodule (algemeen & menu) ------------------
# - Algemene helpers + entry points voor zoeken/bewerken

from tkinter import simpledialog

def _require_user():
    if not globals().get("current_user"):
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen via het startscherm.")
        return False
    return True

def search_projects():
    """Open zoekvenster voor projecten (geen verplichte parameters)."""
    if not _require_user(): return
    _project_search_window()

def edit_project_entry():
    """Vraag projectnummer en open bewerkvenster."""
    if not _require_user(): return
    pnr = simpledialog.askstring("Project bewerken", "Geef projectnummer in (exact):")
    if not pnr: return
    row = db_query("SELECT * FROM projects WHERE projectnummer = ?", (pnr,), fetchone=True)
    if not row:
        messagebox.showinfo("Niet gevonden", f"Geen project met nummer '{pnr}'.")
        return
    open_project_edit_form(dict(row))

# ------------------ Hoofdstuk 7: Projecten (zoeken & bewerken) ------------------
# Bevat de zoeklijst en functies om projecten te openen of te bewerken.
# SQL-versie: gebruikt de tabel "projects" in plaats van projects.csv.

def search_projects_window():
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen via het startscherm.")
        return

    win = tk.Toplevel(root)
    win.title("Projecten zoeken")
    win.geometry("800x600")

    # Zoekveld
    tk.Label(win, text="Zoekterm:").pack(pady=5)
    keyword_var = tk.StringVar()
    entry = tk.Entry(win, textvariable=keyword_var)
    entry.pack(fill="x", padx=10, pady=5)

    results_box = tk.Listbox(win)
    results_box.pack(fill="both", expand=True, padx=10, pady=5)

    def do_search(*_):
        keyword = f"%{keyword_var.get()}%"
        rows = db_query("""
            SELECT id, bureau, projectnummer, klant, projectnaam, stad, status
            FROM projects
            WHERE projectnummer LIKE ? OR klant LIKE ? OR projectnaam LIKE ? OR stad LIKE ?
            ORDER BY laatst_gewijzigd_op DESC
        """, (keyword, keyword, keyword, keyword), fetchall=True)

        results_box.delete(0, tk.END)
        for r in rows:
            line = f"{r['bureau']} {r['projectnummer']} - {r['klant']} ({r['projectnaam']}, {r['stad']}) [{r['status']}]"
            results_box.insert(tk.END, line)
            results_box.itemconfig(tk.END, {'project_id': r['id']})  # project_id bijhouden

    entry.bind("<Return>", do_search)
    tk.Button(win, text="Zoek", command=do_search).pack(pady=5)

    def on_open_selected():
        selection = results_box.curselection()
        if not selection:
            messagebox.showwarning("Geen selectie", "Selecteer een project om te openen/bewerken.")
            return
        idx = selection[0]
        # project_id terugvinden
        proj_id = results_box.itemcget(idx, 'project_id')
        if proj_id:
            edit_project(int(proj_id))

    tk.Button(win, text="Open geselecteerd project", command=on_open_selected).pack(pady=5)


def edit_project(project_id=None):
    """
    Project bewerken of bekijken.
    Als project_id gegeven is, laad dat project. Anders foutmelding.
    """
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen.")
        return

    if not project_id:
        messagebox.showwarning("Geen project", "Er werd geen geldig project gekozen.")
        return

    row = db_query("SELECT * FROM projects WHERE id=?", (project_id,), fetchone=True)
    if not row:
        messagebox.showerror("Fout", "Project niet gevonden in de database.")
        return

    win = tk.Toplevel(root)
    win.title(f"Project {row['projectnummer']} bewerken")
    win.geometry("600x500")
    win.columnconfigure(1, weight=1)

    def row_entry(label, value, r):
        tk.Label(win, text=label, anchor="w").grid(row=r, column=0, sticky="w", padx=8, pady=6)
        var = tk.StringVar(value=value)
        ent = tk.Entry(win, textvariable=var)
        ent.grid(row=r, column=1, sticky="ew", padx=8, pady=6)
        return var

    klant_var = row_entry("Klant", row["klant"], 0)
    naam_var = row_entry("Projectnaam", row["projectnaam"], 1)
    straat_var = row_entry("Straat", row["adres"], 2)
    stad_var = row_entry("Stad", row["stad"], 3)
    status_var = row_entry("Status", row["status"], 4)

    def save_changes():
        newdata = {
            "klant": klant_var.get(),
            "projectnaam": naam_var.get(),
            "adres": straat_var.get(),
            "stad": stad_var.get(),
            "status": status_var.get(),
            "laatst_gewijzigd_door": current_user,
            "laatst_gewijzigd_op": now_str()
        }
        db_update("projects", newdata, "id=?", (project_id,))
        messagebox.showinfo("Succes", "Project bijgewerkt.")
        win.destroy()

    tk.Button(win, text="Opslaan", command=save_changes).grid(row=99, column=1, sticky="e", padx=8, pady=12)


# ------------------ Hoofdstuk 8: Nieuw project wizard ------------------
# Hiermee kan een gebruiker een nieuw project aanmaken (Delafontaine of Vector).
# Inclusief login-check, klant dropdown (readonly, start leeg), en velden.

def new_project_wizard():
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen.")
        return

    # Stap 1: kies type project (Delafontaine of Vector)
    win = tk.Toplevel(root)
    win.title("Nieuw project - Kies type")
    tk.Label(win, text="Welk type project?").pack(pady=10)

    def open_form(bureau):
        win.destroy()
        open_project_form(bureau)

    tk.Button(win, text="Delafontaine", width=20, command=lambda: open_form("Delafontaine")).pack(pady=5)
    tk.Button(win, text="Vector", width=20, command=lambda: open_form("Vector")).pack(pady=5)


def open_project_form(bureau):
    form_win = tk.Toplevel(root)
    form_win.title(f"Nieuw project ({bureau})")

    entries = {}

    row = 0
    # Projectnummer
    prefix = "V" if bureau == "Vector" else ""
    tk.Label(form_win, text="Projectnummer:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    proj_num_var = tk.StringVar(value=prefix)
    entries["projectnummer"] = tk.Entry(form_win, textvariable=proj_num_var)
    entries["projectnummer"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    # Gekoppeld nummer
    row += 1
    tk.Label(form_win, text="Gekoppeld nummer (optioneel):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    gekoppeld_var = tk.StringVar()
    entries["gekoppeld_nummer"] = tk.Entry(form_win, textvariable=gekoppeld_var)
    entries["gekoppeld_nummer"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    # Klant (dropdown, readonly, leeg)
    row += 1
    tk.Label(form_win, text="Klant:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    klanten_rows = db_query("SELECT bedrijf FROM contacts WHERE type='bedrijf' ORDER BY bedrijf", fetchall=True)
    klanten = [r["bedrijf"] for r in klanten_rows] if klanten_rows else []
    klant_var = tk.StringVar(value="")  # leeg starten
    klant_cb = ttk.Combobox(form_win, textvariable=klant_var, values=klanten, state="readonly")
    klant_cb.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
    entries["klant"] = klant_cb

    # Knop nieuwe klant
    def add_new_client():
        open_company_form(after_save=lambda r: refresh_clients(klant_cb, klant_var))

    tk.Button(form_win, text="Nieuwe klant", command=add_new_client).grid(row=row, column=2, padx=5, pady=5)

    def refresh_clients(combo, var):
        rows = db_query("SELECT bedrijf FROM contacts WHERE type='bedrijf' ORDER BY bedrijf", fetchall=True)
        values = [r["bedrijf"] for r in rows] if rows else []
        combo["values"] = values
        var.set("")

    # Projectnaam
    row += 1
    tk.Label(form_win, text="Projectnaam:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    entries["projectnaam"] = tk.Entry(form_win)
    entries["projectnaam"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    # Straat
    row += 1
    tk.Label(form_win, text="Straat:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    entries["straat"] = tk.Entry(form_win)
    entries["straat"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    # Huisnummer
    row += 1
    tk.Label(form_win, text="Huisnummer:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    entries["huisnummer"] = tk.Entry(form_win)
    entries["huisnummer"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    # Stad (dropdown → auto vul postcode)
    row += 1
    tk.Label(form_win, text="Stad:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    stad_var = tk.StringVar()
    stad_cb = ttk.Combobox(form_win, textvariable=stad_var, values=sorted(FLEMISH_CITIES.keys()), state="readonly")
    stad_cb.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
    entries["stad"] = stad_var

    row += 1
    tk.Label(form_win, text="Postcode:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    postcode_var = tk.StringVar()
    entries["postcode"] = tk.Entry(form_win, textvariable=postcode_var, state="readonly")
    entries["postcode"].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    def on_city_select(event=None):
        city = stad_var.get()
        if city in FLEMISH_CITIES:
            postcode_var.set(FLEMISH_CITIES[city])

    stad_cb.bind("<<ComboboxSelected>>", on_city_select)

    # Type project
    row += 1
    tk.Label(form_win, text="Type project:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    type_var = tk.StringVar()
    type_cb = ttk.Combobox(form_win, textvariable=type_var,
                           values=["Industrie", "School", "Particulier"], state="readonly")
    type_cb.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
    entries["type_project"] = type_var

    # Soort project
    row += 1
    tk.Label(form_win, text="Soort project:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
    soort_var = tk.StringVar()
    soort_cb = ttk.Combobox(form_win, textvariable=soort_var,
                            values=["Nieuwbouw", "Renovatie", "Regularisatie", "Combinatie"], state="readonly")
    soort_cb.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
    entries["soort_project"] = soort_var

    # Opslaan knop
    def save_project():
        data = {
            "bureau": bureau,
            "projectnummer": proj_num_var.get().strip(),
            "gekoppeld_nummer": gekoppeld_var.get().strip(),
            "klant": klant_var.get().strip(),
            "projectnaam": entries["projectnaam"].get().strip(),
            "adres": f"{entries['straat'].get().strip()} {entries['huisnummer'].get().strip()}",
            "type_project": type_var.get().strip(),
            "status": "nieuw",
            "laatst_gewijzigd_door": current_user,
            "laatst_gewijzigd_op": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        db_insert("projects", data)
        messagebox.showinfo("Succes", "Project succesvol aangemaakt.")
        form_win.destroy()

    row += 1
    tk.Button(form_win, text="Project aanmaken", command=save_project).grid(row=row, column=1, pady=15)


def search_projects():
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen via het startscherm.")
        return
    # TODO: zoekscherm voor projecten
    messagebox.showinfo("Zoeken", "Project zoeken functie komt hier.")

# ------------------ Hoofdstuk 9: Contacten zoeken ------------------
# Laat toe om te zoeken in de SQLite tabel 'contacts'.
# Zowel personen als bedrijven kunnen gevonden en geopend worden.

def search_contacts():
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen via het startscherm.")
        return

    search_win = tk.Toplevel(root)
    search_win.title("Contacten zoeken")
    search_win.geometry("600x400")

    tk.Label(search_win, text="Zoekterm:").pack(pady=5)
    keyword_var = tk.StringVar()
    entry = tk.Entry(search_win, textvariable=keyword_var, width=50)
    entry.pack(pady=5)

    results_frame = tk.Frame(search_win)
    results_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(results_frame, columns=("type", "naam", "bedrijf", "email"), show="headings")
    tree.heading("type", text="Type")
    tree.heading("naam", text="Naam")
    tree.heading("bedrijf", text="Bedrijf")
    tree.heading("email", text="E-mail")
    tree.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    def do_search(*args):
        tree.delete(*tree.get_children())
        kw = f"%{keyword_var.get().strip()}%"
        rows = db_query("""
            SELECT * FROM contacts
            WHERE bedrijf LIKE ? OR voornaam LIKE ? OR achternaam LIKE ? OR email LIKE ?
            ORDER BY laatst_gewijzigd_op DESC
        """, (kw, kw, kw, kw), fetchall=True)

        for r in rows:
            naam = f"{r['voornaam']} {r['achternaam']}".strip()
            tree.insert("", "end", values=(r["type"], naam, r["bedrijf"], r["email"]), tags=(r["id"],))

    entry.bind("<Return>", do_search)

    def on_open_detail(event):
        item = tree.focus()
        if not item:
            return
        row_id = tree.item(item, "tags")[0]
        r = db_query("SELECT * FROM contacts WHERE id=?", (row_id,), fetchone=True)
        if not r:
            return

        if r["type"] == "persoon":
            open_person_form(existing=dict(r))
        else:
            open_company_form(existing=dict(r))

    tree.bind("<Double-1>", on_open_detail)

    tk.Button(search_win, text="Zoeken", command=do_search).pack(pady=5)
    do_search()


# ------------------ Hoofdstuk 10: Contact detailpagina ------------------
# Dit venster toont de details van een contact en laat bewerken toe.

def show_contact_page(contact):
    if not contact:
        messagebox.showerror("Fout", "Geen contact geselecteerd.")
        return

    detail_win = tk.Toplevel(root)
    detail_win.title(f"Contact: {contact.get('voornaam','')} {contact.get('achternaam','')}".strip())
    detail_win.geometry("500x500")

    frame = tk.Frame(detail_win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    def row(label, value, r):
        tk.Label(frame, text=label + ":", anchor="w", width=15).grid(row=r, column=0, sticky="w", pady=4)
        tk.Label(frame, text=value or "", anchor="w").grid(row=r, column=1, sticky="w", pady=4)

    # Basisgegevens
    row("Type", contact.get("type", ""), 0)
    if contact.get("type") == "persoon":
        row("Voornaam", contact.get("voornaam", ""), 1)
        row("Achternaam", contact.get("achternaam", ""), 2)
        row("Aanhef", contact.get("aanhef", ""), 3)
        row("Bedrijf", contact.get("bedrijf", ""), 4)
    else:  # bedrijf
        row("Bedrijfsnaam", contact.get("bedrijf", ""), 1)
        row("Rechtsvorm", contact.get("rechtsvorm", ""), 2)

    # Contact info
    r = 6
    row("E-mail", contact.get("email", ""), r); r += 1
    row("Functie", contact.get("functie", ""), r); r += 1
    row("GSM", f"{contact.get('gsm_cc','')} {contact.get('gsm_num','')}", r); r += 1
    row("Tel", f"{contact.get('tel_cc','')} {contact.get('tel_num','')}", r); r += 1

    # Adres info
    row("Straat", contact.get("straat", ""), r); r += 1
    row("Huisnummer", contact.get("huisnummer", ""), r); r += 1
    row("Postcode", contact.get("postcode", ""), r); r += 1
    row("Stad", contact.get("stad", ""), r); r += 1
    row("Land", contact.get("land", ""), r); r += 1

    # Metadata
    row("Laatst gewijzigd door", contact.get("laatst_gewijzigd_door", ""), r); r += 1
    row("Laatst gewijzigd op", contact.get("laatst_gewijzigd_op", ""), r); r += 1

    def edit_contact():
        if contact.get("type") == "persoon":
            open_person_form(existing=contact)
        else:
            open_company_form(existing=contact)
        detail_win.destroy()

    tk.Button(detail_win, text="Bewerken", command=edit_contact).pack(pady=10)
    tk.Button(detail_win, text="Sluiten", command=detail_win.destroy).pack(pady=5)


# ------------------ Hoofdstuk 11: Nieuw contact: keuze ------------------
# Dialoogvenster waarin de gebruiker kiest: bedrijf of persoon

def new_contact_choice():
    win = tk.Toplevel(root)
    win.title("Nieuw contact")
    win.geometry("300x150")

    tk.Label(win, text="Wat wil je toevoegen?", font=("Arial", 12)).pack(pady=10)
    tk.Button(win, text="Bedrijf", width=20, command=lambda:(win.destroy(), open_company_form())).pack(pady=5)
    tk.Button(win, text="Persoon", width=20, command=lambda:(win.destroy(), open_person_form())).pack(pady=5)


# ------------------ Hoofdstuk 12: Nieuw of bestaand bedrijf (formulier) ------------------

# Fallback voor now_str als niet aanwezig
try:
    now_str
except NameError:
    from datetime import datetime
    def now_str():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def open_company_form(existing=None, after_save=None):
    win = tk.Toplevel(root)
    win.title("Bedrijf" + (" bewerken" if existing else " toevoegen"))
    win.geometry("560x520")
    win.columnconfigure(1, weight=1)

    def row(lbl, widget, r):
        tk.Label(win, text=lbl, anchor="w").grid(row=r, column=0, sticky="w", padx=8, pady=6)
        widget.grid(row=r, column=1, sticky="ew", padx=8, pady=6)

    bedrijf_var = tk.StringVar(value=(existing.get("bedrijf","") if existing else ""))
    rechtsvorm_var = tk.StringVar(value=(existing.get("rechtsvorm","") if existing else "BV"))
    email_var = tk.StringVar(value=(existing.get("email","") if existing else ""))
    functie_var = tk.StringVar(value=(existing.get("functie","") if existing else ""))
    gsm_cc_lbl = code_to_label(existing.get("gsm_cc", DEFAULT_CC) if existing else DEFAULT_CC)
    tel_cc_lbl = code_to_label(existing.get("tel_cc", DEFAULT_CC) if existing else DEFAULT_CC)
    gsm_cc_var = tk.StringVar(value=gsm_cc_lbl)
    gsm_num_var = tk.StringVar(value=(existing.get("gsm_num","") if existing else ""))
    tel_cc_var = tk.StringVar(value=tel_cc_lbl)
    tel_num_var = tk.StringVar(value=(existing.get("tel_num","") if existing else ""))
    straat_var = tk.StringVar(value=(existing.get("straat","") if existing else ""))
    huisnr_var = tk.StringVar(value=(existing.get("huisnummer","") if existing else ""))
    stad_var = tk.StringVar(value=(existing.get("stad","") if existing else ""))
    postcode_var = tk.StringVar(value=(existing.get("postcode","") if existing else ""))
    land_var = tk.StringVar(value=(existing.get("land","België") if existing else "België"))

    bedrijf_entry = tk.Entry(win, textvariable=bedrijf_var)
    rechtsvorm_cb = ttk.Combobox(win, values=["BV","NV","VZW","CV","VOF","EP","ASBL","GmbH","SARL"], textvariable=rechtsvorm_var, state="readonly")
    email_entry = tk.Entry(win, textvariable=email_var)
    functie_entry = tk.Entry(win, textvariable=functie_var)

    def make_phone_row(label, cc_var, num_var, r, mobile_hint=False):
        cc_cb = ttk.Combobox(win, values=code_label_list(), textvariable=cc_var, width=20, state="readonly")
        num_entry = tk.Entry(win, textvariable=num_var)
        prev_var = tk.StringVar(); prev_lbl = tk.Label(win, textvariable=prev_var, fg="grey")
        def update_preview(*_):
            prev_var.set(format_phone(label_to_code(cc_var.get()), num_var.get(), mobile_hint))
        cc_var.trace("w", update_preview); num_var.trace("w", update_preview); update_preview()
        tk.Label(win, text=label).grid(row=r, column=0, sticky="w", padx=8, pady=6)
        cc_cb.grid(row=r, column=1, sticky="w", padx=(8,0), pady=6)
        tk.Label(win, text="(0)").grid(row=r, column=1, padx=(170,0), sticky="w")
        num_entry.grid(row=r, column=1, sticky="ew", padx=(195,8), pady=6)
        prev_lbl.grid(row=r, column=1, sticky="w", padx=(8,8), pady=(0,0))
        return num_entry

    row("Bedrijfsnaam", bedrijf_entry, 0)
    row("Rechtsvorm", rechtsvorm_cb, 1)
    row("E-mail", email_entry, 2)
    row("Functie (optioneel)", functie_entry, 3)
    make_phone_row("GSM (bedrijf)", gsm_cc_var, gsm_num_var, 4, mobile_hint=True)
    make_phone_row("Telefoon", tel_cc_var, tel_num_var, 5, mobile_hint=False)

    stad_cb = ttk.Combobox(win, values=sorted(FLEMISH_CITIES.keys()), textvariable=stad_var)
    def on_city_select(event=None):
        city = stad_var.get()
        if city in FLEMISH_CITIES:
            postcode_var.set(FLEMISH_CITIES[city])
    stad_cb.bind("<<ComboboxSelected>>", on_city_select)

    row("Straat", tk.Entry(win, textvariable=straat_var), 6)
    row("Huisnummer", tk.Entry(win, textvariable=huisnr_var), 7)
    row("Stad", stad_cb, 8)
    row("Postcode", tk.Entry(win, textvariable=postcode_var), 9)
    row("Land", tk.Entry(win, textvariable=land_var), 10)

    def save_company():
        stamp = now_str()
        rowdata = {
            "type": "bedrijf",
            "bedrijf": bedrijf_var.get() or "",
            "rechtsvorm": rechtsvorm_var.get() or "",
            "aanhef": "",
            "voornaam": "",
            "achternaam": "",
            "gsm_cc": label_to_code(gsm_cc_var.get()),
            "gsm_num": only_digits(gsm_num_var.get()),
            "tel_cc": label_to_code(tel_cc_var.get()),
            "tel_num": only_digits(tel_num_var.get()),
            "email": email_var.get() or "",
            "functie": functie_var.get() or "",
            "rijksregisternummer": "",
            "straat": straat_var.get() or "",
            "huisnummer": huisnr_var.get() or "",
            "postcode": postcode_var.get() or "",
            "stad": stad_var.get() or "",
            "land": land_var.get() or "",
            "laatst_gewijzigd_door": globals().get("current_user") or "",
            "laatst_gewijzigd_op": stamp
        }
        if existing:
            db_update("contacts", rowdata, "type='bedrijf' AND bedrijf=?", (existing.get("bedrijf",""),))
        else:
            db_insert("contacts", rowdata)

        messagebox.showinfo("Succes", "Bedrijf opgeslagen.")
        win.destroy()
        if after_save:
            after_save(rowdata)
        else:
            show_contact_page(rowdata)

    tk.Button(win, text="Opslaan", command=save_company).grid(row=99, column=1, sticky="e", padx=8, pady=12)

# ------------------ Hoofdstuk 13: Nieuw of bestaand persoon (formulier) ------------------

# Fallbacks
try:
    SALUTATIONS
except NameError:
    SALUTATIONS = ["Dhr.", "Mevr.", "Dr.", "Ir."]

def open_person_form(existing=None):
    from difflib import get_close_matches

    win = tk.Toplevel(root)
    win.title("Persoon" + (" bewerken" if existing else " toevoegen"))
    win.geometry("640x620")
    win.columnconfigure(1, weight=1)

    def row(lbl, widget, r):
        tk.Label(win, text=lbl, anchor="w").grid(row=r, column=0, sticky="w", padx=8, pady=6)
        widget.grid(row=r, column=1, sticky="ew", padx=8, pady=6)

    companies = [r["bedrijf"] for r in db_query("SELECT bedrijf FROM contacts WHERE type='bedrijf' AND bedrijf<>'' ORDER BY bedrijf", fetchall=True)]
    bedrijf_var = tk.StringVar(value=(existing.get("bedrijf","") if existing else ""))
    rechtsvorm_var = tk.StringVar(value=(existing.get("rechtsvorm","") if existing else "BV"))
    aanhef_var = tk.StringVar(value=(existing.get("aanhef","") if existing else SALUTATIONS[0]))
    voornaam_var = tk.StringVar(value=(existing.get("voornaam","") if existing else ""))
    achternaam_var = tk.StringVar(value=(existing.get("achternaam","") if existing else ""))
    email_var = tk.StringVar(value=(existing.get("email","") if existing else ""))
    functie_var = tk.StringVar(value=(existing.get("functie","") if existing else ""))
    gsm_cc_lbl = code_to_label(existing.get("gsm_cc", DEFAULT_CC) if existing else DEFAULT_CC)
    tel_cc_lbl = code_to_label(existing.get("tel_cc", DEFAULT_CC) if existing else DEFAULT_CC)
    gsm_cc_var = tk.StringVar(value=gsm_cc_lbl)
    gsm_num_var = tk.StringVar(value=(existing.get("gsm_num","") if existing else ""))
    tel_cc_var = tk.StringVar(value=tel_cc_lbl)
    tel_num_var = tk.StringVar(value=(existing.get("tel_num","") if existing else ""))
    rrn = existing.get("rijksregisternummer","") if existing else ""

    def parse_rrn(rrn):
        digs = only_digits(rrn)
        a = digs[0:2]; b = digs[2:4]; c = digs[4:6]; d = digs[6:9]; e = digs[9:11]
        return a,b,c,d,e
    rra, rrb, rrc, rrd, rre = parse_rrn(rrn)

    straat_var = tk.StringVar(value=(existing.get("straat","") if existing else ""))
    huisnr_var = tk.StringVar(value=(existing.get("huisnummer","") if existing else ""))
    stad_var = tk.StringVar(value=(existing.get("stad","") if existing else ""))
    postcode_var = tk.StringVar(value=(existing.get("postcode","") if existing else ""))
    land_var = tk.StringVar(value=(existing.get("land","België") if existing else "België"))

    bedrijf_cb = ttk.Combobox(win, values=companies, textvariable=bedrijf_var)
    rechtsvorm_cb = ttk.Combobox(win, values=["BV","NV","VZW","CV","VOF","EP","ASBL","GmbH","SARL"], textvariable=rechtsvorm_var, state="readonly")

    def add_company_then_set(rowdata):
        companies_new = [r["bedrijf"] for r in db_query("SELECT bedrijf FROM contacts WHERE type='bedrijf'", fetchall=True)]
        bedrijf_cb['values'] = companies_new
        bedrijf_var.set(rowdata.get("bedrijf",""))
        rechtsvorm_var.set(rowdata.get("rechtsvorm",""))

    row("Bedrijf (optioneel)", bedrijf_cb, 0)
    tk.Button(win, text="Nieuw bedrijf…", command=lambda: open_company_form(existing=None, after_save=add_company_then_set)).grid(row=0, column=2, padx=(0,8))
    row("Rechtsvorm (indien bedrijf)", rechtsvorm_cb, 1)
    aanhef_cb = ttk.Combobox(win, values=SALUTATIONS, textvariable=aanhef_var, state="readonly")
    row("Aanhef", aanhef_cb, 2)
    row("Voornaam", tk.Entry(win, textvariable=voornaam_var), 3)
    row("Achternaam", tk.Entry(win, textvariable=achternaam_var), 4)

    def make_phone_row(label, cc_var, num_var, r, mobile_hint=False):
        cc_cb = ttk.Combobox(win, values=code_label_list(), textvariable=cc_var, width=20, state="readonly")
        num_entry = tk.Entry(win, textvariable=num_var)
        prev_var = tk.StringVar()
        prev_lbl = tk.Label(win, textvariable=prev_var, fg="grey")
        def update_preview(*_):
            prev_var.set(format_phone(label_to_code(cc_var.get()), num_var.get(), mobile_hint))
        cc_var.trace("w", update_preview); num_var.trace("w", update_preview); update_preview()
        tk.Label(win, text=label).grid(row=r, column=0, sticky="w", padx=8, pady=6)
        cc_cb.grid(row=r, column=1, sticky="w", padx=(8,0), pady=6)
        tk.Label(win, text="(0)").grid(row=r, column=1, padx=(170,0), sticky="w")
        num_entry.grid(row=r, column=1, sticky="ew", padx=(195,8), pady=6)
        prev_lbl.grid(row=r, column=1, sticky="w", padx=(8,8), pady=(0,0))
        return num_entry

    make_phone_row("GSM", gsm_cc_var, gsm_num_var, 5, mobile_hint=True)
    make_phone_row("Telefoon", tel_cc_var, tel_num_var, 6, mobile_hint=False)
    row("E-mail", tk.Entry(win, textvariable=email_var), 7)
    row("Functie", tk.Entry(win, textvariable=functie_var), 8)

    tk.Label(win, text="Rijksregisternummer").grid(row=9, column=0, sticky="w", padx=8, pady=6)
    rra_var = tk.StringVar(value=rra); rrb_var = tk.StringVar(value=rrb); rrc_var = tk.StringVar(value=rrc)
    rrd_var = tk.StringVar(value=rrd); rre_var = tk.StringVar(value=rre)
    rra_entry = tk.Entry(win, textvariable=rra_var, width=4)
    rrb_entry = tk.Entry(win, textvariable=rrb_var, width=4)
    rrc_entry = tk.Entry(win, textvariable=rrc_var, width=4)
    rrd_entry = tk.Entry(win, textvariable=rrd_var, width=5)
    rre_entry = tk.Entry(win, textvariable=rre_var, width=4)
    x = 8
    rra_entry.grid(row=9, column=1, sticky="w", padx=(x,0))
    tk.Label(win, text=".").grid(row=9, column=1, padx=(x+35,0), sticky="w")
    rrb_entry.grid(row=9, column=1, padx=(x+45,0), sticky="w")
    tk.Label(win, text=".").grid(row=9, column=1, padx=(x+80,0), sticky="w")
    rrc_entry.grid(row=9, column=1, padx=(x+90,0), sticky="w")
    tk.Label(win, text="-").grid(row=9, column=1, padx=(x+125,0), sticky="w")
    rrd_entry.grid(row=9, column=1, padx=(x+135,0), sticky="w")
    tk.Label(win, text=".").grid(row=9, column=1, padx=(x+175,0), sticky="w")
    rre_entry.grid(row=9, column=1, padx=(x+185,0), sticky="w")

    stad_cb = ttk.Combobox(win, values=sorted(FLEMISH_CITIES.keys()), textvariable=stad_var)
    def on_city_select(event=None):
        city = stad_var.get()
        if city in FLEMISH_CITIES:
            postcode_var.set(FLEMISH_CITIES[city])
    stad_cb.bind("<<ComboboxSelected>>", on_city_select)

    row("Straat", tk.Entry(win, textvariable=straat_var), 10)
    row("Huisnummer", tk.Entry(win, textvariable=huisnr_var), 11)
    row("Stad", stad_cb, 12)
    row("Postcode", tk.Entry(win, textvariable=postcode_var), 13)
    row("Land", tk.Entry(win, textvariable=land_var), 14)

    def save_person():
        rows = db_query("SELECT voornaam, achternaam FROM contacts WHERE type='persoon'", fetchall=True)
        existing_names = [f"{r['voornaam']} {r['achternaam']}".strip() for r in (rows or [])]

        fname = voornaam_var.get().strip()
        lname = achternaam_var.get().strip()
        full_name = f"{fname} {lname}".strip()
        if not fname or not lname:
            messagebox.showwarning("Fout", "Voornaam en achternaam zijn verplicht.")
            return

        # Duplicate / fuzzy
        if not existing:
            from difflib import get_close_matches
            if full_name in existing_names:
                if not messagebox.askyesno("Opgelet", f"'{full_name}' bestaat al. Toch toevoegen?"):
                    return
            else:
                close = get_close_matches(full_name, existing_names, n=1, cutoff=0.8)
                if close and not messagebox.askyesno("Mogelijke dubbele naam", f"'{full_name}' lijkt op '{close[0]}'. Toch toevoegen?"):
                    return

        # RRN
        a = only_digits(rra_var.get())[:2]
        b = only_digits(rrb_var.get())[:2]
        c = only_digits(rrc_var.get())[:2]
        d = only_digits(rrd_var.get())[:3]
        e = only_digits(rre_var.get())[:2]
        rrn = f"{a}.{b}.{c}-{d}.{e}" if any([a,b,c,d,e]) else ""

        rowdata = {
            "type": "persoon",
            "bedrijf": bedrijf_var.get() or "",
            "rechtsvorm": (rechtsvorm_var.get() if bedrijf_var.get() else ""),
            "aanhef": aanhef_var.get() or "",
            "voornaam": fname,
            "achternaam": lname,
            "gsm_cc": label_to_code(gsm_cc_var.get()),
            "gsm_num": only_digits(gsm_num_var.get()),
            "tel_cc": label_to_code(tel_cc_var.get()),
            "tel_num": only_digits(tel_num_var.get()),
            "email": email_var.get() or "",
            "functie": functie_var.get() or "",
            "rijksregisternummer": rrn,
            "straat": straat_var.get() or "",
            "huisnummer": huisnr_var.get() or "",
            "postcode": postcode_var.get() or "",
            "stad": stad_var.get() or "",
            "land": land_var.get() or "",
            "laatst_gewijzigd_door": globals().get("current_user") or "",
            "laatst_gewijzigd_op": now_str()
        }

        if existing:
            db_update("contacts", rowdata, "type='persoon' AND voornaam=? AND achternaam=?", (existing.get("voornaam",""), existing.get("achternaam","")))
        else:
            db_insert("contacts", rowdata)

        messagebox.showinfo("Succes", "Persoon opgeslagen.")
        win.destroy()
        show_contact_page(rowdata)

    tk.Button(win, text="Opslaan", command=save_person).grid(row=99, column=1, sticky="e", padx=8, pady=12)

# ------------------ Hoofdstuk 14: Zoeken & bewerken contacten ------------------
# SQLite-versie. Lijst + filteren + dubbelklik of knop om te bewerken.

def edit_contacts():
    if not current_user:
        messagebox.showwarning("Login vereist", "Gelieve eerst in te loggen via het startscherm.")
        return

    win = tk.Toplevel(root)
    win.title("Contacten bewerken")
    win.geometry("820x520")

    # Top: zoekbalk + typefilter
    top = tk.Frame(win)
    top.pack(fill="x", padx=10, pady=8)

    tk.Label(top, text="Zoekterm:").pack(side="left")
    kw_var = tk.StringVar()
    tk.Entry(top, textvariable=kw_var, width=40).pack(side="left", padx=6)

    tk.Label(top, text="Type:").pack(side="left", padx=(12,0))
    type_var = tk.StringVar(value="Alle")
    type_cb = ttk.Combobox(top, textvariable=type_var, values=["Alle", "Bedrijf", "Persoon"], state="readonly", width=12)
    type_cb.pack(side="left")

    search_btn = tk.Button(top, text="Zoeken")
    search_btn.pack(side="left", padx=8)

    # Midden: resultaten
    mid = tk.Frame(win)
    mid.pack(fill="both", expand=True, padx=10, pady=(0,8))

    cols = ("type","naam","bedrijf","email","stad")
    tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
    headers = {"type":"Type","naam":"Naam","bedrijf":"Bedrijf","email":"E-mail","stad":"Stad"}
    widths  = {"type":120,"naam":180,"bedrijf":180,"email":220,"stad":120}
    for c in cols:
        tree.heading(c, text=headers[c])
        tree.column(c, width=widths[c], stretch=True)
    tree.pack(side="left", fill="both", expand=True)

    sb = ttk.Scrollbar(mid, orient="vertical", command=tree.yview)
    sb.pack(side="right", fill="y")
    tree.configure(yscroll=sb.set)

    # Onderaan: knoppen
    btns = tk.Frame(win)
    btns.pack(fill="x", padx=10, pady=(0,10))

    edit_btn = tk.Button(btns, text="Bewerken", state="disabled")
    detail_btn = tk.Button(btns, text="Details", state="disabled")
    close_btn = tk.Button(btns, text="Sluiten", command=win.destroy)

    edit_btn.pack(side="left")
    detail_btn.pack(side="left", padx=6)
    close_btn.pack(side="right")

    def do_search(*_):
        tree.delete(*tree.get_children())
        kw = kw_var.get().strip()
        like = f"%{kw}%"
        filters = []
        params = []

        if kw:
            filters.append("(bedrijf LIKE ? OR voornaam LIKE ? OR achternaam LIKE ? OR email LIKE ? OR stad LIKE ?)")
            params += [like, like, like, like, like]

        t = type_var.get()
        if t == "Bedrijf":
            filters.append("type='bedrijf'")
        elif t == "Persoon":
            filters.append("type='persoon'")

        where = " WHERE " + " AND ".join(filters) if filters else ""
        rows = db_query(
            f"SELECT * FROM contacts{where} "
            "ORDER BY CASE WHEN type='persoon' THEN achternaam ELSE bedrijf END COLLATE NOCASE",
            tuple(params),
            fetchall=True
        )

        for r in rows:
            # id gebruiken als iid zodat we hem makkelijk kunnen terugvinden
            iid = str(r["id"])
            naam_vis = (f"{r['voornaam']} {r['achternaam']}".strip() if r["type"]=="persoon" else r["bedrijf"])
            tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    r["type"].capitalize(),
                    f"{r['voornaam']} {r['achternaam']}".strip(),
                    r["bedrijf"] or "",
                    r["email"] or "",
                    r["stad"] or ""
                )
            )

        edit_btn.config(state="disabled")
        detail_btn.config(state="disabled")

    def current_selection_id():
        sel = tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def on_select(event=None):
        has = bool(tree.selection())
        edit_btn.config(state="normal" if has else "disabled")
        detail_btn.config(state="normal" if has else "disabled")

    def do_edit():
        cid = current_selection_id()
        if not cid:
            return
        r = db_query("SELECT * FROM contacts WHERE id=?", (cid,), fetchone=True)
        if not r:
            return
        rec = dict(r)
        if rec["type"] == "persoon":
            open_person_form(existing=rec)
        else:
            open_company_form(existing=rec)

    def do_detail():
        cid = current_selection_id()
        if not cid:
            return
        r = db_query("SELECT * FROM contacts WHERE id=?", (cid,), fetchone=True)
        if not r:
            return
        show_contact_page(dict(r))

    tree.bind("<<TreeviewSelect>>", on_select)
    tree.bind("<Double-1>", lambda e: do_edit())
    search_btn.config(command=do_search)
    type_cb.bind("<<ComboboxSelected>>", do_search)

    # Na terugkeer van een edit-venster automatisch refreshen
    win.bind("<FocusIn>", lambda e: do_search())

    do_search()

# =========================
# Hoofdstuk 15: Applicatie-start
# =========================
import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
from PIL import Image, ImageTk

# --- Database instellingen ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dela_database.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_colleagues():
    """Zorg dat de tabel 'colleagues' bestaat en vul standaard namen in."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS colleagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    # Voeg standaard collega's toe als ze nog niet bestaan
    defaults = ["Felix", "Michael", "Kris", "Pascal", "Annelies"]
    for d in defaults:
        try:
            cur.execute("INSERT OR IGNORE INTO colleagues (name) VALUES (?)", (d,))
        except Exception:
            pass
    conn.commit()
    conn.close()


# --- Hulpfuncties voor logo’s ---
def _safe_open_image(path):
    try:
        return Image.open(path)
    except Exception:
        return None


def _resize_keep_aspect(img, max_w, max_h):
    if not img:
        return None
    iw, ih = img.size
    scale = min(max_w / iw, max_h / ih)
    new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    return img.resize(new_size, Image.LANCZOS)


def _render_logos(parent, max_frac_w=0.6, max_frac_h_each=0.25, smaller_second=True):
    """Plaats twee logo's gecentreerd onder elkaar, proportioneel geschaald."""
    # Verwijder vorige logo-container
    if getattr(root, "_logo_frame", None):
        root._logo_frame.destroy()

    logo_frame = tk.Frame(parent)
    logo_frame.pack(expand=True)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not hasattr(root, "_pil_logo1"):
        root._pil_logo1 = _safe_open_image(os.path.join(base_dir, "Logo_Delafontaine.png"))
    if not hasattr(root, "_pil_logo2"):
        root._pil_logo2 = _safe_open_image(os.path.join(base_dir, "Logo_Vector.png"))

    logo1_label = tk.Label(logo_frame)
    logo1_label.pack(pady=8)
    logo2_label = tk.Label(logo_frame)
    logo2_label.pack(pady=8)

    root._logo_frame = logo_frame
    root._logo1_label = logo1_label
    root._logo2_label = logo2_label

    def _update_logos(event=None):
        if not (logo1_label.winfo_exists() and logo2_label.winfo_exists()):
            return

        W = max(root.winfo_width(), 400)
        H = max(root.winfo_height(), 400)

        max_w = int(W * max_frac_w)
        max_h_each = int(H * max_frac_h_each)

        # Eerste logo
        img1r = _resize_keep_aspect(root._pil_logo1, max_w, max_h_each)
        if img1r:
            tkimg1 = ImageTk.PhotoImage(img1r)
            logo1_label.config(image=tkimg1, text="")
            logo1_label.image = tkimg1

        # Tweede logo
        if smaller_second:
            max_w2, max_h2 = int(max_w * 0.8), int(max_h_each * 0.8)
        else:
            max_w2, max_h2 = max_w, max_h_each

        img2r = _resize_keep_aspect(root._pil_logo2, max_w2, max_h2)
        if img2r:
            tkimg2 = ImageTk.PhotoImage(img2r)
            logo2_label.config(image=tkimg2, text="")
            logo2_label.image = tkimg2

    logo_frame.bind("<Configure>", _update_logos)
    root.after(50, _update_logos)


# --- Login flow ---
current_user = None


def show_start_screen():
    """Toon startscherm met logo’s en login-knop."""
    for w in root.winfo_children():
        w.destroy()

    _render_logos(root)

    btn = tk.Button(root, text="LOGIN", font=("Arial", 12, "bold"),
                    command=show_login_screen, width=15)
    btn.pack(pady=20)


def show_login_screen():
    """Toon het login-scherm met collega's."""
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="LOGIN", font=("Arial", 14, "bold")).pack(pady=10)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM colleagues ORDER BY name")
    names = [r[0] for r in cur.fetchall()]
    conn.close()

    for naam in names:
        frame = tk.Frame(root, relief="groove", borderwidth=1)
        frame.pack(pady=3, padx=20, fill="x")
        btn = tk.Button(frame, text=naam, anchor="w",
                        command=lambda n=naam: do_login(n))
        btn.pack(fill="x")


def do_login(naam):
    """Inloggen en hoofdmenu tonen."""
    global current_user
    current_user = naam
    show_main_menu()


# --- Hoofdmenu ---
def show_main_menu():
    """Toon hoofdmenu (menu’s + logo’s)."""
    for w in root.winfo_children():
        w.destroy()

    menubar = tk.Menu(root)
    projecten_menu = tk.Menu(menubar, tearoff=0)
    projecten_menu.add_command(label="Nieuw project", command=lambda: print("Nieuw project"))
    projecten_menu.add_command(label="Project zoeken", command=lambda: print("Project zoeken"))
    projecten_menu.add_command(label="Project bewerken", command=lambda: print("Project bewerken"))
    menubar.add_cascade(label="Projecten", menu=projecten_menu)

    contacten_menu = tk.Menu(menubar, tearoff=0)
    contacten_menu.add_command(label="Nieuw bedrijf", command=lambda: print("Nieuw bedrijf"))
    contacten_menu.add_command(label="Nieuwe persoon", command=lambda: print("Nieuwe persoon"))
    contacten_menu.add_command(label="Contacten zoeken", command=lambda: print("Contacten zoeken"))
    contacten_menu.add_command(label="Contacten bewerken", command=lambda: print("Contacten bewerken"))
    menubar.add_cascade(label="Contacten", menu=contacten_menu)

    menubar.add_command(label="Afsluiten", command=root.destroy)
    root.config(menu=menubar)

    _render_logos(root)


# --- Main ---
def main():
    init_colleagues()
    show_start_screen()
    root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dela Database")
    root.geometry("800x600")
    main()
