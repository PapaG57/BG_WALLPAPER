# ==============================================================================
# LOGICIEL : BG WALLPAPER
# CONCEPTION : FG DEVELOPPEMENT & GEMINI
# VERSION : 2.6
# DATE : 15 mai 2026
# (c) Tous droits réservés.
# ==============================================================================

import sys
import os
import requests
import ctypes
import datetime
import threading
import time
import webbrowser
import tkinter as tk
import subprocess
import winreg
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# --- CONFIGURATION ---
VERSION = "2.6"
ANNEE_CREATION = "2026"
URL_SITE = "https://www.fgdeveloppement.com"

if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
    if os.path.basename(BASE_PATH).lower() == "dist":
        BASE_PATH = os.path.dirname(BASE_PATH)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_PATH, "img", "logo", "bg-wallpaper.jpg")

# Infos globales
infos_actuelles = {
    "titre": "Chargement...",
    "localisation": "En attente...",
    "date": "Non définie",
    "chemin_local": ""
}

def gerer_demarrage_automatique():
    """Ajoute l'application au démarrage de Windows via le registre."""
    try:
        if getattr(sys, 'frozen', False):
            chemin = f'"{sys.executable}"'
        else:
            chemin = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "BG_WALLPAPER", 0, winreg.REG_SZ, chemin)
    except: pass

def appliquer_fond_ecran(chemin_img):
    """Applique le fond d'écran de manière précise sur le moniteur principal."""
    if not chemin_img or not os.path.exists(chemin_img):
        return
    
    ps_cmd = f"& {{ $w = New-Object -ComObject DesktopWallpaper; $m = $w.GetMonitorDevicePathAt(0); $w.SetWallpaper($m, '{chemin_img}') }}"
    
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], 
                       creationflags=0x08000000, capture_output=True)
    except:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)

def obtenir_nom_mois_fr(num_mois):
    mois = ["janvier", "fevrier", "mars", "avril", "mai", "juin", 
            "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
    return f"{num_mois:02d}_{mois[num_mois-1]}"

def obtenir_dossier_du_mois(dt=None):
    if dt is None: dt = datetime.datetime.now()
    annee = dt.strftime("%Y")
    nom_mois = obtenir_nom_mois_fr(dt.month)
    dossier = os.path.join(BASE_PATH, "images", annee, nom_mois)
    if not os.path.exists(dossier):
        os.makedirs(dossier, exist_ok=True)
    return dossier

def ajuster_date_bing(date_brute):
    dt = datetime.datetime.strptime(date_brute, "%Y%m%d")
    return dt + datetime.timedelta(days=1)

def ajouter_log_trie(dossier, message):
    try:
        log_path = os.path.join(dossier, "bg_wallpaper_log.txt")
        maintenant = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        nouvelle_ligne = f"{maintenant} - {message}\n"
        
        lignes = []
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lignes = f.readlines()
        
        lignes.append(nouvelle_ligne)
        
        try:
            lignes.sort(key=lambda x: datetime.datetime.strptime(x[:19], "%d-%m-%Y %H:%M:%S"))
        except: pass
            
        with open(log_path, 'w', encoding='utf-8') as f:
            f.writelines(lignes)
    except: pass

def attendre_internet(tentatives=10, delai=5):
    """Attend que la connexion internet soit disponible."""
    for _ in range(tentatives):
        try:
            requests.get("https://www.bing.com", timeout=3)
            return True
        except:
            time.sleep(delai)
    return False

def telecharger_bing(forcer=False, icon=None):
    global infos_actuelles
    try:
        api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=-1&n=1&mkt=fr-FR&ts={int(time.time())}"
        res = requests.get(api_url, timeout=10).json()
        img_data = res['images'][0]
        
        dt_reel = ajuster_date_bing(img_data['startdate'])
        date_str = dt_reel.strftime("%d-%m-%Y")
        titre = img_data.get('title', 'Sans titre')
        
        dossier = obtenir_dossier_du_mois(dt_reel)
        chemin_img = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.jpg"))
        chemin_txt = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.txt"))

        image_existe = os.path.exists(chemin_img)

        if not image_existe or forcer:
            url_base = "https://www.bing.com" + img_data['urlbase']
            url_4k = f"{url_base}_3840x2160.jpg&uhd=1"
            r = requests.get(url_4k, timeout=15)
            if r.status_code != 200:
                r = requests.get(f"https://www.bing.com{img_data['url']}", timeout=15)
            
            if r.status_code == 200:
                with open(chemin_img, 'wb') as f: f.write(r.content)
                with open(chemin_txt, 'w', encoding='utf-8') as f:
                    f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {img_data.get('copyright')}")
                ajouter_log_trie(dossier, "MAJ auto - Succès")
                image_existe = True

        # Mise à jour des infos globales AVANT l'application pour comparaison
        deja_en_place = (infos_actuelles["chemin_local"] == chemin_img)

        infos_actuelles.update({
            "titre": titre, "localisation": img_data.get('copyright', 'Inconnu'),
            "date": date_str, "chemin_local": chemin_img
        })

        if image_existe:
            # On n'applique que si l'image n'est pas déjà celle en place, ou si on force
            if not deja_en_place or forcer:
                appliquer_fond_ecran(chemin_img)
                if forcer and icon: icon.notify(f"Image appliquée : {titre}", "BG WALLPAPER")
        return True
    except: return False

def charger_image_specifique(img_data):
    try:
        dt_reel = ajuster_date_bing(img_data['startdate'])
        date_str = dt_reel.strftime("%d-%m-%Y")
        dossier = obtenir_dossier_du_mois(dt_reel)
        chemin_img = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.jpg"))
        
        if os.path.exists(chemin_img):
            return False, "Cette image a déjà été chargée, veuillez charger une autre image."

        url_base = "https://www.bing.com" + img_data['urlbase']
        url_4k = f"{url_base}_3840x2160.jpg&uhd=1"
        r = requests.get(url_4k, timeout=15)
        if r.status_code != 200:
            r = requests.get(f"https://www.bing.com{img_data['url']}", timeout=15)
        
        if r.status_code == 200:
            with open(chemin_img, 'wb') as f: f.write(r.content)
            txt_path = chemin_img.replace(".jpg", ".txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"TITRE : {img_data.get('title')}\nDATE : {date_str}\nLOCALISATION : {img_data.get('copyright')}")
            
            ajouter_log_trie(dossier, "IMG Manquée - Succès")
            appliquer_fond_ecran(chemin_img)
            # On met à jour infos_actuelles pour refléter le changement manuel
            infos_actuelles.update({"titre": img_data.get('title'), "date": date_str, "chemin_local": chemin_img})
            return True, "Image chargée avec succès !"
        return False, "Erreur réseau."
    except: return False, "Erreur imprévue."

def ouvrir_charger_image(icon=None):
    def create_window():
        root = tk.Tk(); root.title("BG WALLPAPER - Charger une image manquée"); centrer_fenetre(root, 500, 400)
        root.attributes("-topmost", True)
        tk.Label(root, text="Choisir une image parmi les 16 derniers jours :", font=("Arial", 10, "bold")).pack(pady=20)
        options = []; map_data = {}
        try:
            for idx in [0, 8]:
                res = requests.get(f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={idx}&n=8&mkt=fr-FR", timeout=5).json()
                for img in res.get('images', []):
                    d_str = ajuster_date_bing(img['startdate']).strftime("%d-%m-%Y")
                    lib = f"{d_str} : {img.get('title', 'Sans titre')}"
                    if lib not in options: options.append(lib); map_data[lib] = img
        except: pass
        if not options: return
        var = tk.StringVar(root); var.set(options[0]); tk.OptionMenu(root, var, *options).pack(pady=10, padx=20, fill=tk.X)
        def action():
            success, msg = charger_image_specifique(map_data[var.get()])
            res_win = tk.Toplevel(root); res_win.title("Résultat"); centrer_fenetre(res_win, 400, 180); res_win.attributes("-topmost", True)
            color = "#28a745" if success else "#dc3545"
            tk.Label(res_win, text=msg, font=("Arial", 10), wraplength=350, fg=color).pack(pady=25)
            tk.Button(res_win, text="Fermer", command=lambda: [res_win.destroy(), root.destroy() if success else None], width=15).pack()
        tk.Button(root, text="Charger l'image", command=action, bg="#0078d7", fg="white", font=("Arial", 10, "bold"), pady=8).pack(pady=20, padx=50, fill=tk.X)
        tk.Button(root, text="Annuler et Fermer", command=root.destroy, bg="#6c757d", fg="white").pack(pady=10)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def lister_images_archivees():
    images = []
    base_images = os.path.join(BASE_PATH, "images")
    if not os.path.exists(base_images): return images
    for root, dirs, files in os.walk(base_images):
        for file in files:
            if file.endswith(".jpg") and file.startswith("bing_"):
                date_str = file.replace("bing_", "").replace(".jpg", "")
                try:
                    dt = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    titre = "Sans titre"
                    txt_path = os.path.join(root, file.replace(".jpg", ".txt"))
                    if os.path.exists(txt_path):
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if "TITRE :" in line: titre = line.replace("TITRE :", "").strip(); break
                    images.append({"date": date_str, "dt": dt, "titre": titre, "chemin": os.path.abspath(os.path.join(root, file))})
                except: continue
    images.sort(key=lambda x: x["dt"], reverse=True)
    return images

def afficher_historique(icon):
    def create_window():
        root = tk.Tk(); root.title("BG WALLPAPER - Historique"); centrer_fenetre(root, 600, 480)
        lb = tk.Listbox(root, font=("Arial", 9)); lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        imgs = lister_images_archivees()
        for i in imgs: lb.insert(tk.END, f"{i['date']} - {i['titre']}")
        def apply():
            sel = lb.curselection()
            if sel:
                chemin = imgs[sel[0]]["chemin"]
                appliquer_fond_ecran(chemin)
                infos_actuelles.update({"titre": imgs[sel[0]]["titre"], "date": imgs[sel[0]]["date"], "chemin_local": chemin})
        tk.Button(root, text="Appliquer", command=apply, bg="#0078d7", fg="white", pady=8).pack(fill=tk.X, padx=10, pady=5)
        tk.Button(root, text="Fermer", command=root.destroy, bg="#6c757d", fg="white").pack(fill=tk.X, padx=10, pady=5)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def afficher_infos_custom(icon):
    def create_window():
        root = tk.Tk(); root.title("BG WALLPAPER - Infos"); centrer_fenetre(root, 450, 580); root.attributes("-topmost", True)
        path = infos_actuelles["chemin_local"]
        if path and os.path.exists(path):
            try:
                img = Image.open(path); img.thumbnail((400, 300))
                tk_img = ImageTk.PhotoImage(img); l = tk.Label(root, image=tk_img); l.image = tk_img; l.pack(pady=10)
            except: pass
        tk.Label(root, text=infos_actuelles["titre"], font=("Arial", 11, "bold"), wraplength=400).pack(pady=5)
        tk.Label(root, text=infos_actuelles["localisation"], font=("Arial", 9), wraplength=400).pack(pady=5)
        tk.Label(root, text=f"Fichier : {infos_actuelles['date']}", fg="gray").pack(pady=5)
        tk.Button(root, text="Fermer", command=root.destroy, width=15).pack(pady=20)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def afficher_a_propos(icon):
    def create_window():
        root = tk.Tk(); root.title("À propos"); centrer_fenetre(root, 300, 220); root.attributes("-topmost", True)
        tk.Label(root, text="BG WALLPAPER", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        lbl_link = tk.Label(root, text="By FG Developpement", font=("Arial", 10, "underline"), fg="blue", cursor="hand2")
        lbl_link.pack(pady=2)
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open(URL_SITE))
        
        tk.Label(root, text=f"(c) {ANNEE_CREATION}", font=("Arial", 9)).pack(pady=2)
        tk.Label(root, text=f"Version : {VERSION}", font=("Arial", 10, "bold")).pack(pady=5)
        tk.Label(root, text="GEMINI & FG DÉVELOPPEMENT", font=("Arial", 7), fg="gray").pack(pady=5)
        tk.Button(root, text="Fermer", command=root.destroy, width=10).pack(pady=15)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def centrer_fenetre(f, l, h):
    sw = f.winfo_screenwidth(); sh = f.winfo_screenheight()
    f.geometry(f"{l}x{h}+{(sw-l)//2}+{(sh-h)//2}")

def quitter_app(icon): icon.stop(); os._exit(0)

def boucle_temporelle(icon):
    derniere_verif = time.time()
    dernier_jour = datetime.date.today()
    while True:
        time.sleep(10)
        maintenant = time.time()
        jour_actuel = datetime.date.today()
        
        if (maintenant - derniere_verif) > 30:
            time.sleep(5) 
            if attendre_internet(tentatives=5, delai=2):
                telecharger_bing(icon=icon)
            
        elif jour_actuel != dernier_jour:
            if attendre_internet(tentatives=5, delai=2):
                telecharger_bing(icon=icon)
                dernier_jour = jour_actuel
            
        derniere_verif = maintenant

def lancer_app():
    gerer_demarrage_automatique()
    try: logo = Image.open(LOGO_PATH)
    except: logo = Image.new('RGB', (64, 64), color='blue')
    menu = pystray.Menu(
        item('Voir l\'image du jour', afficher_infos_custom),
        item('Historique des archives', afficher_historique),
        item('Charger une image manquée', ouvrir_charger_image),
        item('Ouvrir le dossier images', lambda i: os.startfile(os.path.join(BASE_PATH, "images"))),
        pystray.Menu.SEPARATOR,
        item('Actualiser maintenant', lambda i: telecharger_bing(forcer=True, icon=i)),
        item('À propos', afficher_a_propos),
        item('Quitter', quitter_app)
    )
    icon = pystray.Icon("BG_Wallpaper", logo, "BG WALLPAPER", menu)
    
    def initialisation():
        if attendre_internet(tentatives=12, delai=5):
            telecharger_bing()
        threading.Thread(target=boucle_temporelle, args=(icon,), daemon=True).start()
    
    threading.Thread(target=initialisation, daemon=True).start()
    icon.run()

if __name__ == "__main__": lancer_app()
