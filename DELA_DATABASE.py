import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from PIL import Image, ImageTk
import os
import csv
import chardet
from datetime import datetime

# ------------------ Paden ------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_CSV = os.path.join(SCRIPT_DIR, "projects.csv")
CONTACTS_CSV = os.path.join(SCRIPT_DIR, "contacts.csv")
FLEMISH_CITIES_CSV = os.path.join(SCRIPT_DIR, "vlaamse_gemeenten.csv")  # optioneel

current_user = None

# ------------------ CSV & encoding ------------------
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(2048)
    result = chardet.detect(rawdata)
    return result['encoding'] or 'utf-8'

def normalize_key(key) -> str:
    if not isinstance(key, str):
        key = ""
    return key.strip().lower().replace(" ", "_").replace("\ufeff", "")

def safe_read_csv(file_path):
    if not os.path.exists(file_path):
        return []
    encoding = detect_encoding(file_path)
    rows = []
    with open(file_path, "r", newline="", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            norm_row = {}
            for k, v in row.items():
                nk = normalize_key(k)
                nv = v.strip() if isinstance(v, str) else (v if v is not None else "")
                norm_row[nk] = nv
            rows.append(norm_row)
    return rows

def safe_write_csv(file_path, rows, headers):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})

def now_str():
    return datetime.now().strftime("%Y.%m.%d om %H:%M")

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

# ------------------ GUI basis ------------------
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

def show_home():
    clear_window()
    root.title("DELA_DATABASE")

    container = tk.Frame(root)
    container.pack(expand=True)

    # Twee logo’s onder elkaar, gecentreerd
    def load_logo(filename, max_size=(400, 200)):
        try:
            path = os.path.join(SCRIPT_DIR, filename)
            img = Image.open(path)
            img.thumbnail(max_size)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Logo '{filename}' niet geladen: {e}")
            return None

    logo1 = load_logo("Logo_Delafontaine.png")
    logo2 = load_logo("Logo_Vector.png")

    if logo1:
        lbl1 = tk.Label(container, image=logo1)
        lbl1.image = logo1
        lbl1.pack(pady=10)
    else:
        tk.Label(container, text="[Logo Delafontaine ontbreekt]", font=("Arial", 14)).pack(pady=10)

    if logo2:
        lbl2 = tk.Label(container, image=logo2)
        lbl2.image = logo2
        lbl2.pack(pady=10)
    else:
        tk.Label(container, text="[Logo Vector ontbreekt]", font=("Arial", 14)).pack(pady=10)

    tk.Button(root, text="Login", font=("Arial", 14), command=show_users).pack(pady=20)

def show_users():
    clear_window()
    root.title("Selecteer gebruiker")
    users = ["Felix", "Kris", "Michael", "Pascal", "Heidi V.", "Heidi D.", "Marie-Roos", "Jelle", "Quinten", "Rik"]

    tk.Button(root, text="← Terug", command=show_home).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True)
    for u in users:
        tk.Button(frame, text=u, font=("Arial", 14), width=20, command=lambda name=u: select_user(name)).pack(pady=5)

def select_user(name):
    global current_user
    current_user = name
    show_main_menu()

def show_main_menu():
    clear_window()
    root.title(f"Welkom {current_user}")

    tk.Button(root, text="← Terug", command=show_users).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True)

    tk.Button(frame, text="Projecten", font=("Arial", 14), width=20, command=show_project_choice).pack(pady=10)
    tk.Button(frame, text="Contacten", font=("Arial", 14), width=20, command=show_contact_choice).pack(pady=10)

# ------------------ PROJECTEN ------------------
# Uitgebreide headers met bureau & gekoppeld nummer
PROJECT_HEADERS = ["bureau", "projectnummer", "gekoppeld_nummer", "projectnaam", "klant", "laatst_gewijzigd_door", "laatst_gewijzigd_op"]

def show_project_choice():
    clear_window()
    root.title("Projecten")

    tk.Button(root, text="← Terug", command=show_main_menu).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True)

    tk.Button(frame, text="Project zoeken", font=("Arial", 14), width=25, command=search_project_in_list).pack(pady=10)
    tk.Button(frame, text="Nieuw project", font=("Arial", 14), width=25, command=new_project_wizard).pack(pady=10)
    tk.Button(frame, text="Project bewerken", font=("Arial", 14), width=25, command=edit_project).pack(pady=10)

def normalize_project_row(r):
    """Zorgt dat alle velden bestaan, ook als oude CSV nog gebruikt wordt."""
    return {
        "bureau": r.get("bureau",""),
        "projectnummer": r.get("projectnummer",""),
        "gekoppeld_nummer": r.get("gekoppeld_nummer",""),
        "projectnaam": r.get("projectnaam",""),
        "klant": r.get("klant",""),
        "laatst_gewijzigd_door": r.get("laatst_gewijzigd_door",""),
        "laatst_gewijzigd_op": r.get("laatst_gewijzigd_op",""),
    }

def show_project_page(project_row):
    clear_window()
    pr = normalize_project_row(project_row)

    title = pr.get('projectnaam') or pr.get('projectnummer') or "Project"
    root.title(f"Project: {title}")

    tk.Button(root, text="← Terug", command=show_project_choice).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True, pady=10)

    tk.Label(frame, text=f"Bureau: {pr.get('bureau','')}", font=("Arial", 14)).pack(pady=3)
    tk.Label(frame, text=f"Projectnummer: {pr.get('projectnummer','')}", font=("Arial", 14)).pack(pady=3)
    if pr.get('gekoppeld_nummer'):
        tk.Label(frame, text=f"Gekoppeld nummer (tegenpartij): {pr.get('gekoppeld_nummer','')}", font=("Arial", 14)).pack(pady=3)
    tk.Label(frame, text=f"Projectnaam: {pr.get('projectnaam','')}", font=("Arial", 14)).pack(pady=3)
    tk.Label(frame, text=f"Klant (naam/bedrijf): {pr.get('klant','')}", font=("Arial", 14)).pack(pady=3)
    tk.Label(frame, text=f"Laatst gewijzigd door {pr.get('laatst_gewijzigd_door','onbekend')} op {pr.get('laatst_gewijzigd_op','onbekend')}", font=("Arial", 12, "italic")).pack(pady=10)

def project_sort_key(r):
    # Sorteer op type & numeriek deel, DELA (zonder V) eerst
    num = r.get("projectnummer","")
    is_vector = 1 if num.startswith("V") else 0
    digits = only_digits(num)
    val = int(digits) if digits.isdigit() else 0
    return (is_vector, val)

def search_project_in_list(edit_mode=False):
    list_window = tk.Toplevel(root)
    list_window.title("Projectenlijst")
    list_window.geometry("700x480")

    search_var = tk.StringVar()
    tk.Label(list_window, text="Filter:", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(5,0))
    tk.Entry(list_window, textvariable=search_var, font=("Arial", 12)).pack(fill="x", padx=5, pady=5)

    columns = ("bureau", "projectnummer", "gekoppeld_nummer", "projectnaam", "klant")
    tree = ttk.Treeview(list_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.replace("_"," ").capitalize())
    tree.pack(fill="both", expand=True)

    rows = [normalize_project_row(r) for r in safe_read_csv(PROJECTS_CSV)]
    rows.sort(key=project_sort_key)

    def populate(filter_text=""):
        tree.delete(*tree.get_children())
        for r in rows:
            hay = " ".join([r.get("bureau",""), r.get("projectnummer",""), r.get("gekoppeld_nummer",""),
                            r.get("projectnaam",""), r.get("klant","")]).lower()
            if filter_text.lower() in hay:
                tree.insert("", "end", values=(r.get("bureau",""), r.get("projectnummer",""),
                                               r.get("gekoppeld_nummer",""), r.get("projectnaam",""), r.get("klant","")))
    populate()
    search_var.trace("w", lambda *args: populate(search_var.get()))

    def on_select(event):
        item = tree.selection()
        if not item: return
        values = tree.item(item, "values")
        sel_bureau, sel_num = values[0], values[1]
        for r in rows:
            if r.get("projectnummer")==sel_num and r.get("bureau")==sel_bureau:
                if edit_mode:
                    edit_project_form(r)
                else:
                    show_project_page(r)
                list_window.destroy()
                break

    tree.bind("<Double-1>", on_select)

def edit_project():
    search_project_in_list(edit_mode=True)

def edit_project_form(existing):
    # Projectnummer & bureau laten we niet wijzigen (optioneel: kan je toevoegen als je wil)
    project_name = simpledialog.askstring("Projectnaam", "Voer projectnaam in:", initialvalue=existing.get("projectnaam",""))
    klant = simpledialog.askstring("Klant (naam/bedrijf)", "Voer klantnaam/bedrijfsnaam in:", initialvalue=existing.get("klant",""))

    # Gekoppeld nummer afhankelijk van bureau (format afdwingen)
    gekoppeld = existing.get("gekoppeld_nummer","")
    if (existing.get("bureau") or "").lower().startswith("dela"):
        # tegenpartij Vector: V#####
        inp = simpledialog.askstring("Gekoppeld nummer (Vector)", "Optioneel: V + 4 cijfers", initialvalue=gekoppeld)
        if inp is None:
            pass
        else:
            inp = inp.strip().upper()
            if inp == "":
                gekoppeld = ""
            else:
                digits = only_digits(inp)
                if len(digits) == 4:
                    gekoppeld = "V" + digits
                elif inp.startswith("V") and len(only_digits(inp))==4:
                    gekoppeld = "V" + only_digits(inp)
                else:
                    messagebox.showwarning("Formaat", "Gebruik V + 4 cijfers (bijv. V3450). Ongeldige waarde genegeerd.")
    else:
        # tegenpartij Delafontaine: ####
        inp = simpledialog.askstring("Gekoppeld nummer (Delafontaine)", "Optioneel: 4 cijfers", initialvalue=gekoppeld)
        if inp is None:
            pass
        else:
            inp = inp.strip()
            if inp == "":
                gekoppeld = ""
            else:
                digits = only_digits(inp)
                if len(digits) == 4:
                    gekoppeld = digits
                else:
                    messagebox.showwarning("Formaat", "Gebruik 4 cijfers (bijv. 3450). Ongeldige waarde genegeerd.")

    project_name = "" if project_name is None else project_name
    klant = "" if klant is None else klant

    rows = [normalize_project_row(r) for r in safe_read_csv(PROJECTS_CSV)]
    for r in rows:
        if r.get("projectnummer")==existing.get("projectnummer") and r.get("bureau")==existing.get("bureau"):
            r.update({
                "projectnaam": project_name,
                "klant": klant,
                "gekoppeld_nummer": gekoppeld,
                "laatst_gewijzigd_door": current_user,
                "laatst_gewijzigd_op": now_str()
            })
            existing = r
            break
    safe_write_csv(PROJECTS_CSV, rows, PROJECT_HEADERS)
    messagebox.showinfo("Succes", "Project opgeslagen.")
    show_project_page(existing)

def new_project_wizard():
    # Stap 1: kiezen bureau
    choice = {"bureau": None}
    win = tk.Toplevel(root)
    win.title("Nieuw project - bureau")
    win.geometry("300x160")
    tk.Label(win, text="Voor welk bureau is het project?", font=("Arial", 12)).pack(pady=10)
    tk.Button(win, text="Delafontaine", width=20, command=lambda:(choice.update(bureau="Delafontaine"), win.destroy())).pack(pady=5)
    tk.Button(win, text="Vector", width=20, command=lambda:(choice.update(bureau="Vector"), win.destroy())).pack(pady=5)
    win.grab_set(); win.wait_window()

    bureau = choice.get("bureau")
    if not bureau:
        return

    # Stap 2: eigen nummer
    if bureau == "Delafontaine":
        num = simpledialog.askstring("Dossiernummer (DELA)", "Voer 4 cijfers in (bijv. 3450):")
        if num is None:
            return
        digits = only_digits(num)
        if len(digits) != 4:
            messagebox.showwarning("Formaat", "Gebruik exact 4 cijfers.")
            return
        projectnummer = digits
        # Optioneel gekoppeld Vector-nummer
        vnum = simpledialog.askstring("Gekoppeld nummer (Vector)", "Optioneel: V + 4 cijfers (bijv. V3450):")
        gekoppeld = ""
        if vnum is not None and vnum.strip() != "":
            vnum = vnum.strip().upper()
            d = only_digits(vnum)
            if len(d) == 4:
                gekoppeld = "V" + d
            elif vnum.startswith("V") and len(d) == 4:
                gekoppeld = "V" + d
            else:
                messagebox.showwarning("Formaat", "Gekoppeld nummer genegeerd: gebruik V + 4 cijfers.")
    else:
        num = simpledialog.askstring("Dossiernummer (VECTOR)", "Voer 4 cijfers in (we zetten er V voor):")
        if num is None:
            return
        digits = only_digits(num)
        if len(digits) != 4:
            messagebox.showwarning("Formaat", "Gebruik exact 4 cijfers.")
            return
        projectnummer = "V" + digits
        # Optioneel gekoppeld DELA-nummer
        dnum = simpledialog.askstring("Gekoppeld nummer (Delafontaine)", "Optioneel: 4 cijfers (bijv. 3450):")
        gekoppeld = ""
        if dnum is not None and dnum.strip() != "":
            d = only_digits(dnum)
            if len(d) == 4:
                gekoppeld = d
            else:
                messagebox.showwarning("Formaat", "Gekoppeld nummer genegeerd: gebruik 4 cijfers.")

    # Stap 3: overige velden
    project_name = simpledialog.askstring("Projectnaam", "Voer projectnaam in:") or ""
    klant = simpledialog.askstring("Klant (naam/bedrijf)", "Voer klantnaam/bedrijfsnaam in:") or ""

    rows = [normalize_project_row(r) for r in safe_read_csv(PROJECTS_CSV)]
    rowdata = {
        "bureau": bureau,
        "projectnummer": projectnummer,
        "gekoppeld_nummer": gekoppeld,
        "projectnaam": project_name,
        "klant": klant,
        "laatst_gewijzigd_door": current_user,
        "laatst_gewijzigd_op": now_str()
    }
    rows.append(rowdata)
    safe_write_csv(PROJECTS_CSV, rows, PROJECT_HEADERS)
    messagebox.showinfo("Succes", "Project aangemaakt.")
    show_project_page(rowdata)

# ------------------ CONTACTEN ------------------
CONTACT_HEADERS = [
    "type", "bedrijf", "rechtsvorm", "aanhef", "voornaam", "achternaam",
    "gsm_cc", "gsm_num", "tel_cc", "tel_num",
    "email", "functie", "rijksregisternummer",
    "straat", "huisnummer", "postcode", "stad", "land",
    "laatst_gewijzigd_door", "laatst_gewijzigd_op"
]

SALUTATIONS = ["Dhr.", "Mevr.", "Dhr. & Mevr.", "— (geen)"]

def show_contact_choice():
    clear_window()
    root.title("Contacten")

    tk.Button(root, text="← Terug", command=show_main_menu).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True)

    tk.Button(frame, text="Contact zoeken", font=("Arial", 14), width=25, command=search_contact_in_list).pack(pady=10)
    tk.Button(frame, text="Nieuw contact", font=("Arial", 14), width=25, command=new_contact_choice).pack(pady=10)
    tk.Button(frame, text="Contact bewerken", font=("Arial", 14), width=25, command=edit_contact).pack(pady=10)

def show_contact_page(contact_row):
    clear_window()
    r = contact_row
    if r.get("type") == "persoon":
        base = " ".join([r.get("aanhef",""), r.get("voornaam",""), r.get("achternaam","")]).strip()
        title = base or "Contact"
        if r.get("bedrijf"):
            title += f" ({r.get('bedrijf')})"
    else:
        title = r.get("bedrijf") or "Bedrijf"

    root.title(f"Contact: {title}")

    tk.Button(root, text="← Terug", command=show_contact_choice).pack(anchor="nw", padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(expand=True, pady=10)

    lines = []
    lines.append(f"Type: {r.get('type','')}")
    if r.get("bedrijf"): lines.append(f"Bedrijf: {r.get('bedrijf','')}")
    if r.get("rechtsvorm"): lines.append(f"Rechtsvorm: {r.get('rechtsvorm','')}")
    naam = " ".join([r.get("aanhef",""), r.get("voornaam",""), r.get("achternaam","")]).strip()
    if naam: lines.append(f"Naam: {naam}")
    if r.get("functie"): lines.append(f"Functie: {r.get('functie','')}")
    if r.get("email"): lines.append(f"E-mail: {r.get('email','')}")
    if r.get("gsm_cc") or r.get("gsm_num"):
        lines.append(f"GSM: {format_phone(r.get('gsm_cc',''), r.get('gsm_num',''), mobile_hint=True)}")
    if r.get("tel_cc") or r.get("tel_num"):
        lines.append(f"Telefoon: {format_phone(r.get('tel_cc',''), r.get('tel_num',''), mobile_hint=False)}")
    if r.get("rijksregisternummer"):
        lines.append(f"Rijksregisternummer: {r.get('rijksregisternummer','')}")
    adres = []
    if r.get("straat"): adres.append(r.get("straat"))
    if r.get("huisnummer"): adres.append(r.get("huisnummer"))
    if r.get("postcode") or r.get("stad"):
        adres.append(f"{r.get('postcode','')} {r.get('stad','')}".strip())
    if r.get("land"): adres.append(r.get("land"))
    if adres: lines.append("Adres: " + ", ".join([a for a in adres if a]))

    for ln in lines:
        tk.Label(frame, text=ln, font=("Arial", 14)).pack(pady=2)

    tk.Label(frame, text=f"Laatst gewijzigd door {r.get('laatst_gewijzigd_door','onbekend')} op {r.get('laatst_gewijzigd_op','onbekend')}", font=("Arial", 12, "italic")).pack(pady=10)

def new_contact_choice():
    win = tk.Toplevel(root)
    win.title("Nieuw contact: keuze")
    win.geometry("300x160")
    tk.Label(win, text="Wat wil je toevoegen?", font=("Arial", 12)).pack(pady=10)
    tk.Button(win, text="Bedrijf", width=20, command=lambda: (win.destroy(), open_company_form())).pack(pady=5)
    tk.Button(win, text="Persoon", width=20, command=lambda: (win.destroy(), open_person_form())).pack(pady=5)
    win.grab_set()

# ---- Bedrijf form ----
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

    # Telefoonrijen
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

    row("Bedrijfsnaam", bedrijf_entry, 0)
    row("Rechtsvorm", rechtsvorm_cb, 1)
    row("E-mail", email_entry, 2)
    row("Functie (optioneel)", functie_entry, 3)
    make_phone_row("GSM (bedrijf)", gsm_cc_var, gsm_num_var, 4, mobile_hint=True)
    make_phone_row("Telefoon", tel_cc_var, tel_num_var, 5, mobile_hint=False)

    # Stad → postcode automatisch
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
        rows = safe_read_csv(CONTACTS_CSV)
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
            "laatst_gewijzigd_door": current_user,
            "laatst_gewijzigd_op": stamp
        }
        if existing:
            for r in rows:
                if r.get("type")=="bedrijf" and r.get("bedrijf")==existing.get("bedrijf"):
                    r.update(rowdata)
                    break
        else:
            rows.append(rowdata)
        safe_write_csv(CONTACTS_CSV, rows, CONTACT_HEADERS)
        messagebox.showinfo("Succes", "Bedrijf opgeslagen.")
        win.destroy()
        if after_save:
            after_save(rowdata)
        else:
            show_contact_page(rowdata)

    tk.Button(win, text="Opslaan", command=save_company).grid(row=99, column=1, sticky="e", padx=8, pady=12)

# ---- Persoon form ----
def open_person_form(existing=None):
    win = tk.Toplevel(root)
    win.title("Persoon" + (" bewerken" if existing else " toevoegen"))
    win.geometry("640x620")
    win.columnconfigure(1, weight=1)

    def row(lbl, widget, r):
        tk.Label(win, text=lbl, anchor="w").grid(row=r, column=0, sticky="w", padx=8, pady=6)
        widget.grid(row=r, column=1, sticky="ew", padx=8, pady=6)

    companies = sorted({r.get("bedrijf","") for r in safe_read_csv(CONTACTS_CSV) if r.get("type")=="bedrijf" and r.get("bedrijf")})
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
    # Verwacht formaat YY.MM.DD-XXX.XX
    def parse_rrn(rrn):
        # Extract digits in groups 2-2-2-3-2
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
        companies_new = sorted({r.get("bedrijf","") for r in safe_read_csv(CONTACT_FILE)})
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

    # Telefoon & previews
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

    # RRN met vast masker: YY.MM.DD-XXX.XX
    tk.Label(win, text="Rijksregisternummer").grid(row=9, column=0, sticky="w", padx=8, pady=6)
    rra_var = tk.StringVar(value=rra); rrb_var = tk.StringVar(value=rrb); rrc_var = tk.StringVar(value=rrc)
    rrd_var = tk.StringVar(value=rrd); rre_var = tk.StringVar(value=rre)

    rra_entry = tk.Entry(win, textvariable=rra_var, width=4)
    rrb_entry = tk.Entry(win, textvariable=rrb_var, width=4)
    rrc_entry = tk.Entry(win, textvariable=rrc_var, width=4)
    rrd_entry = tk.Entry(win, textvariable=rrd_var, width=5)
    rre_entry = tk.Entry(win, textvariable=rre_var, width=4)

    # Plaatsing met vaste scheidingstekens
    base_col = 1
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

    # Stad → postcode automatisch
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
        rows = safe_read_csv(CONTACTS_CSV)
        stamp = now_str()
        # Combineer RR: YY.MM.DD-XXX.XX (leeg toegestaan)
        a = only_digits(rra_var.get())[:2]
        b = only_digits(rrb_var.get())[:2]
        c = only_digits(rrc_var.get())[:2]
        d = only_digits(rrd_var.get())[:3]
        e = only_digits(rre_var.get())[:2]
        rrn = ""
        if any([a,b,c,d,e]):
            rrn = f"{a}.{b}.{c}-{d}.{e}"

        rowdata = {
            "type": "persoon",
            "bedrijf": bedrijf_var.get() or "",
            "rechtsvorm": (rechtsvorm_var.get() if bedrijf_var.get() else ""),
            "aanhef": aanhef_var.get() or "",
            "voornaam": voornaam_var.get() or "",
            "achternaam": achternaam_var.get() or "",
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
            "laatst_gewijzigd_door": current_user,
            "laatst_gewijzigd_op": stamp
        }

        if existing:
            for r in rows:
                if r.get("type")=="persoon" and r.get("voornaam")==existing.get("voornaam") and r.get("achternaam")==existing.get("achternaam") and r.get("bedrijf")==existing.get("bedrijf"):
                    r.update(rowdata)
                    break
        else:
            rows.append(rowdata)

        safe_write_csv(CONTACTS_CSV, rows, CONTACT_HEADERS)
        messagebox.showinfo("Succes", "Persoon opgeslagen.")
        win.destroy()
        show_contact_page(rowdata)

    tk.Button(win, text="Opslaan", command=save_person).grid(row=99, column=1, sticky="e", padx=8, pady=12)

# ---- Zoeken & bewerken contacten ----
def search_contact_in_list(edit_mode=False):
    list_window = tk.Toplevel(root)
    list_window.title("Contactenlijst")
    list_window.geometry("900x520")

    search_var = tk.StringVar()
    tk.Label(list_window, text="Filter:", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(5,0))
    tk.Entry(list_window, textvariable=search_var, font=("Arial", 12)).pack(fill="x", padx=5, pady=5)

    columns = ("type", "bedrijf", "naam", "email", "gsm", "telefoon", "functie")
    tree = ttk.Treeview(list_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.capitalize())
    tree.pack(fill="both", expand=True)

    rows = safe_read_csv(CONTACTS_CSV)

    def row_to_display(r):
        if r.get("type") == "bedrijf":
            naam = r.get("bedrijf","")
        else:
            naam = " ".join([r.get("aanhef",""), r.get("voornaam",""), r.get("achternaam","")]).strip()
        gsm_fmt = format_phone(r.get("gsm_cc",""), r.get("gsm_num",""), mobile_hint=True) if r.get("gsm_cc") or r.get("gsm_num") else ""
        tel_fmt = format_phone(r.get("tel_cc",""), r.get("tel_num",""), mobile_hint=False) if r.get("tel_cc") or r.get("tel_num") else ""
        return (
            r.get("type",""),
            r.get("bedrijf",""),
            naam,
            r.get("email",""),
            gsm_fmt,
            tel_fmt,
            r.get("functie","")
        )

    def populate(filter_text=""):
        tree.delete(*tree.get_children())
        for r in rows:
            hay = " ".join([
                r.get("type",""), r.get("bedrijf",""),
                r.get("aanhef",""), r.get("voornaam",""), r.get("achternaam",""),
                r.get("email",""), r.get("functie",""),
                r.get("gsm_cc","")+r.get("gsm_num",""),
                r.get("tel_cc","")+r.get("tel_num","")
            ]).lower()
            if filter_text.lower() in hay:
                tree.insert("", "end", values=row_to_display(r))
    populate()
    search_var.trace("w", lambda *args: populate(search_var.get()))

    def on_select(event):
        item = tree.selection()
        if not item: return
        values = tree.item(item, "values")
        sel_type, sel_bedrijf, sel_naam = values[0], values[1], values[2]
        target = None
        for r in rows:
            if sel_type == "bedrijf" and r.get("type")=="bedrijf" and r.get("bedrijf")==sel_bedrijf:
                target = r; break
            if sel_type == "persoon" and r.get("type")=="persoon":
                nm = " ".join([r.get("aanhef",""), r.get("voornaam",""), r.get("achternaam","")]).strip()
                if nm == sel_naam and r.get("bedrijf","") == sel_bedrijf:
                    target = r; break
        if not target:
            return
        if edit_mode:
            if target.get("type") == "bedrijf":
                open_company_form(existing=target, after_save=lambda _: show_contact_page(target))
            else:
                open_person_form(existing=target)
        else:
            show_contact_page(target)
        list_window.destroy()

    tree.bind("<Double-1>", on_select)

def edit_contact():
    search_contact_in_list(edit_mode=True)

# ------------------ Start ------------------
root = tk.Tk()
root.title("DELA_DATABASE")
root.geometry("1000x700")
show_home()
root.mainloop()
