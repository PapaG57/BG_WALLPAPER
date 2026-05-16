# ==============================================================================
# LOGICIEL : BG WALLPAPER
# CONCEPTION : FG DEVELOPPEMENT & GEMINI
# VERSION : 2.8
# DATE : 16 mai 2026
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
from tkinter import messagebox
import subprocess
import winreg
import socket
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# --- CONFIGURATION ---
VERSION = "2.8"
ANNEE_CREATION = "2026"
URL_SITE = "https://www.fgdeveloppement.com"

if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
    if os.path.basename(BASE_PATH).lower() == "dist":
        BASE_PATH = os.path.dirname(BASE_PATH)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_PATH, "img", "logo", "bg-wallpaper.jpg")
DEBUG_LOG_PATH = os.path.join(BASE_PATH, "debug_wallpaper.txt")

# Infos globales
infos_actuelles = {
    "titre": "Chargement...",
    "localisation": "En attente...",
    "date": "Non définie",
    "chemin_local": ""
}

def log_debug(message):
    """Enregistre un message dans le fichier de debug avec horodatage."""
    try:
        maintenant = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{maintenant}] {message}\n")
    except: pass

def verifier_instance_unique():
    """Empêche de lancer plusieurs instances."""
    try:
        global _lock_socket
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.bind(("127.0.0.1", 65432))
        return True
    except socket.error:
        return False

def gerer_demarrage_automatique():
    """Force l'inscription au démarrage de Windows."""
    try:
        if getattr(sys, 'frozen', False):
            chemin = f'"{sys.executable}"'
        else:
            chemin = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "BG_WALLPAPER", 0, winreg.REG_SZ, chemin)
        log_debug(f"Démarrage auto OK : {chemin}")
    except Exception as e:
        log_debug(f"Erreur Démarrage auto : {str(e)}")

def appliquer_fond_ecran(chemin_img):
    """Applique le fond d'écran avec une robustesse maximale."""
    if not chemin_img or not os.path.exists(chemin_img):
        log_debug(f"Erreur : Image introuvable ({chemin_img})")
        return False
    
    chemin_abs = os.path.abspath(chemin_img)
    log_debug(f"Tentative d'application : {chemin_abs}")

    # Validation de l'image avant application
    try:
        with Image.open(chemin_abs) as img:
            img.verify()
        log_debug("Validation image : OK")
    except Exception as e:
        log_debug(f"Validation image : ÉCHEC - {str(e)}")
        return False

    succes = False

    # Méthode 1 : PowerShell COM - Tous les écrans ($null)
    # On utilise des guillemets doubles et l'échappement pour les chemins complexes
    ps_cmd_1 = f'$w = New-Object -ComObject DesktopWallpaper; $w.SetWallpaper($null, \"{chemin_abs}\")'
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd_1], 
                           creationflags=0x08000000, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            log_debug("Méthode 1 (COM All Monitors) : Succès")
            succes = True
        else:
            log_debug(f"Méthode 1 : Échec ({res.returncode}) - {res.stderr}")
    except Exception as e:
        log_debug(f"Méthode 1 : Exception - {str(e)}")

    # Méthode 2 : API Windows Standard (Système)
    try:
        # SPI_SETDESKWALLPAPER = 20
        # SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE = 3
        res_spi = ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_abs, 3)
        if res_spi:
            log_debug("Méthode 2 (SystemParametersInfoW) : Succès")
            succes = True
        else:
            log_debug("Méthode 2 : Échec (Retour 0)")
    except Exception as e:
        log_debug(f"Méthode 2 : Exception - {str(e)}")

    # Méthode 3 : Registre + Refresh forcé
    try:
        ps_cmd_3 = f'Set-ItemProperty -Path "HKCU:\\Control Panel\\Desktop" -Name Wallpaper -Value \"{chemin_abs}\"; rundll32.exe user32.dll,UpdatePerUserSystemParameters'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd_3], creationflags=0x08000000)
        log_debug("Méthode 3 (Registry) : Tentée")
    except: pass

    return succes

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
    try:
        dt = datetime.datetime.strptime(date_brute, "%Y%m%d")
        return dt + datetime.timedelta(days=1)
    except: return datetime.datetime.now()

def ajouter_log_trie(dossier, message):
    try:
        log_path = os.path.join(dossier, "bg_wallpaper_log.txt")
        maintenant = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{maintenant} - {message}\n")
    except: pass

def attendre_internet(tentatives=30, delai=5):
    """Attend que la connexion internet soit disponible (max 150s)."""
    log_debug("Vérification connexion internet...")
    for i in range(tentatives):
        try:
            requests.get("https://www.bing.com", timeout=5)
            log_debug(f"Connexion établie ({i+1}).")
            return True
        except:
            time.sleep(delai)
    log_debug("Échec de connexion.")
    return False

def telecharger_bing(forcer=False, icon=None):
    global infos_actuelles
    try:
        log_debug(f"Vérification Bing (idx=0, force={forcer})")
        api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=fr-FR&ts={int(time.time())}"
        res = requests.get(api_url, timeout=10).json()
        img_data = res['images'][0]
        
        dt_reel = ajuster_date_bing(img_data['startdate'])
        date_str = dt_reel.strftime("%d-%m-%Y")
        titre = img_data.get('title', 'Sans titre')
        
        dossier = obtenir_dossier_du_mois(dt_reel)
        chemin_img = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.jpg"))
        chemin_txt = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.txt"))

        # Si l'image n'existe pas ou qu'on force l'actualisation
        if not os.path.exists(chemin_img) or forcer:
            log_debug(f"Téléchargement : {titre}")
            url_base = "https://www.bing.com" + img_data['urlbase']
            url_4k = f"{url_base}_3840x2160.jpg&uhd=1"
            try:
                r = requests.get(url_4k, timeout=15)
                if r.status_code != 200:
                    r = requests.get(f"https://www.bing.com{img_data['url']}", timeout=15)
            except:
                r = requests.get(f"https://www.bing.com{img_data['url']}", timeout=15)
            
            if r.status_code == 200:
                with open(chemin_img, 'wb') as f: f.write(r.content)
                with open(chemin_txt, 'w', encoding='utf-8') as f:
                    f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {img_data.get('copyright')}")
                ajouter_log_trie(dossier, f"MAJ {'Force' if forcer else 'Auto'} - Succès")
                log_debug("Téléchargement réussi.")
            else:
                log_debug(f"Erreur HTTP : {r.status_code}")
                return False

        # Vérifier si l'image est déjà celle en place (en mémoire)
        deja_en_place = (infos_actuelles["chemin_local"] == chemin_img)

        infos_actuelles.update({
            "titre": titre, "localisation": img_data.get('copyright', 'Inconnu'),
            "date": date_str, "chemin_local": chemin_img
        })

        if os.path.exists(chemin_img):
            if not deja_en_place or forcer:
                if appliquer_fond_ecran(chemin_img):
                    if icon:
                        icon.notify(f"Image appliquée : {titre}", "BG WALLPAPER")
                        log_debug("Notification envoyée.")
                else:
                    log_debug("Toutes les méthodes d'application ont échoué.")
            else:
                log_debug("Image déjà active, application ignorée.")
        return True
    except Exception as e:
        log_debug(f"Erreur telecharger_bing : {str(e)}")
        return False

def ouvrir_dossier_images(icon=None):
    try: os.startfile(os.path.join(BASE_PATH, "images"))
    except: pass

def voir_log_debug(icon=None):
    try: os.startfile(DEBUG_LOG_PATH)
    except: pass

def charger_image_specifique(img_data):
    try:
        dt_reel = ajuster_date_bing(img_data['startdate'])
        date_str = dt_reel.strftime("%d-%m-%Y")
        dossier = obtenir_dossier_du_mois(dt_reel)
        chemin_img = os.path.abspath(os.path.join(dossier, f"bing_{date_str}.jpg"))
        
        if os.path.exists(chemin_img):
            return False, "Cette image existe déjà."

        url_base = "https://www.bing.com" + img_data['urlbase']
        r = requests.get(f"{url_base}_3840x2160.jpg&uhd=1", timeout=15)
        if r.status_code != 200:
            r = requests.get(f"https://www.bing.com{img_data['url']}", timeout=15)
        
        if r.status_code == 200:
            with open(chemin_img, 'wb') as f: f.write(r.content)
            with open(chemin_img.replace(".jpg", ".txt"), 'w', encoding='utf-8') as f:
                f.write(f"TITRE : {img_data.get('title')}\nDATE : {date_str}\nLOCALISATION : {img_data.get('copyright')}")
            
            appliquer_fond_ecran(chemin_img)
            infos_actuelles.update({"titre": img_data.get('title'), "date": date_str, "chemin_local": chemin_img})
            return True, "Image chargée !"
        return False, "Erreur réseau."
    except Exception as e:
        log_debug(f"Erreur charger_image_specifique : {str(e)}")
        return False, "Erreur."

def ouvrir_charger_image(icon=None):
    def create_window():
        root = tk.Tk(); root.title("Charger une image manquée"); centrer_fenetre(root, 500, 400); root.attributes("-topmost", True)
        tk.Label(root, text="Sélectionner une image des 16 derniers jours :", font=("Arial", 10, "bold")).pack(pady=20)
        options = []; map_data = {}
        try:
            for idx in [0, 8]:
                res = requests.get(f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={idx}&n=8&mkt=fr-FR", timeout=5).json()
                for img in res.get('images', []):
                    d_str = ajuster_date_bing(img['startdate']).strftime("%d-%m-%Y")
                    lib = f"{d_str} : {img.get('title', 'Sans titre')}"
                    if lib not in options: options.append(lib); map_data[lib] = img
        except: pass
        if not options: 
            tk.Label(root, text="Erreur de chargement des données Bing.", fg="red").pack()
            return
        var = tk.StringVar(root); var.set(options[0]); tk.OptionMenu(root, var, *options).pack(pady=10, padx=20, fill=tk.X)
        def action():
            success, msg = charger_image_specifique(map_data[var.get()])
            messagebox.showinfo("Résultat", msg)
            if success: root.destroy()
        tk.Button(root, text="Appliquer", command=action, bg="#0078d7", fg="white", font=("Arial", 10, "bold")).pack(pady=20)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def afficher_historique(icon):
    def create_window():
        root = tk.Tk(); root.title("Historique"); centrer_fenetre(root, 600, 480)
        lb = tk.Listbox(root, font=("Arial", 9)); lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        imgs = []
        base = os.path.join(BASE_PATH, "images")
        for r, d, files in os.walk(base):
            for f in files:
                if f.startswith("bing_") and f.endswith(".jpg"):
                    d_str = f.replace("bing_", "").replace(".jpg", "")
                    try:
                        dt = datetime.datetime.strptime(d_str, "%d-%m-%Y")
                        imgs.append({"date": d_str, "dt": dt, "chemin": os.path.abspath(os.path.join(r, f))})
                    except: continue
        imgs.sort(key=lambda x: x["dt"], reverse=True)
        for i in imgs: lb.insert(tk.END, f"{i['date']} - {os.path.basename(i['chemin'])}")
        def apply():
            s = lb.curselection()
            if s: appliquer_fond_ecran(imgs[s[0]]["chemin"])
        tk.Button(root, text="Appliquer", command=apply).pack(fill=tk.X, padx=10)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def afficher_infos_custom(icon):
    def create_window():
        root = tk.Tk(); root.title("Infos Wallpaper"); centrer_fenetre(root, 450, 580); root.attributes("-topmost", True)
        path = infos_actuelles["chemin_local"]
        if path and os.path.exists(path):
            try:
                img = Image.open(path); img.thumbnail((400, 300))
                tk_img = ImageTk.PhotoImage(img); l = tk.Label(root, image=tk_img); l.image = tk_img; l.pack(pady=10)
            except: pass
        tk.Label(root, text=infos_actuelles["titre"], font=("Arial", 11, "bold"), wraplength=400).pack(pady=5)
        tk.Label(root, text=infos_actuelles["localisation"], font=("Arial", 9), wraplength=400).pack(pady=5)
        tk.Label(root, text=f"Date : {infos_actuelles['date']}", fg="gray").pack(pady=5)
        tk.Button(root, text="Fermer", command=root.destroy).pack(pady=20)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def afficher_a_propos(icon):
    def create_window():
        root = tk.Tk(); root.title("À propos"); centrer_fenetre(root, 300, 220); root.attributes("-topmost", True)
        tk.Label(root, text="BG WALLPAPER", font=("Arial", 12, "bold")).pack(pady=20)
        tk.Label(root, text=f"Version : {VERSION}", font=("Arial", 10, "bold")).pack()
        lbl = tk.Label(root, text="By FG Developpement", fg="blue", cursor="hand2", font=("Arial", 9, "underline"))
        lbl.pack(pady=5); lbl.bind("<Button-1>", lambda e: webbrowser.open(URL_SITE))
        tk.Label(root, text=f"(c) {ANNEE_CREATION}", font=("Arial", 8)).pack(pady=10)
        tk.Button(root, text="Fermer", command=root.destroy).pack()
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def centrer_fenetre(f, l, h):
    sw = f.winfo_screenwidth(); sh = f.winfo_screenheight()
    f.geometry(f"{l}x{h}+{(sw-l)//2}+{(sh-h)//2}")

def quitter_app(icon): 
    log_debug("Quitter.")
    icon.stop(); os._exit(0)

def boucle_temporelle(icon):
    derniere_verif = time.time()
    dernier_jour = datetime.date.today()
    log_debug("Boucle de surveillance active.")
    while True:
        try:
            time.sleep(60) # Vérification toutes les minutes
            maintenant = time.time()
            jour_actuel = datetime.date.today()
            
            # Sortie de veille ou changement de jour
            if (maintenant - derniere_verif) > 150 or jour_actuel != dernier_jour:
                log_debug(f"Réveil ou Nouveau jour ({jour_actuel}).")
                if attendre_internet(tentatives=10, delai=10):
                    telecharger_bing(icon=icon)
                    dernier_jour = jour_actuel
                derniere_verif = maintenant
            else:
                # Petite mise à jour toutes les 6 heures pour être sûr
                if (maintenant - derniere_verif) > 21600:
                    log_debug("Vérification périodique (6h).")
                    if attendre_internet(tentatives=5, delai=5):
                        telecharger_bing(icon=icon)
                    derniere_verif = maintenant
        except Exception as e:
            log_debug(f"Erreur Boucle : {str(e)}")
            time.sleep(60)

def lancer_app():
    if not verifier_instance_unique(): sys.exit(0)

    log_debug(f"--- DÉMARRAGE v{VERSION} ---")
    gerer_demarrage_automatique()
    
    try: logo = Image.open(LOGO_PATH)
    except: logo = Image.new('RGB', (64, 64), color='blue')
    
    menu = pystray.Menu(
        item('Voir l\'image du jour', afficher_infos_custom),
        item('Historique des archives', afficher_historique),
        item('Charger une image manquée', ouvrir_charger_image),
        item('Ouvrir le dossier images', ouvrir_dossier_images),
        item('Voir le journal technique (Log)', voir_log_debug),
        pystray.Menu.SEPARATOR,
        item('Actualiser maintenant', lambda i: telecharger_bing(forcer=True, icon=i)),
        item('À propos', afficher_a_propos),
        item('Quitter', quitter_app)
    )
    
    icon = pystray.Icon("BG_Wallpaper", logo, "BG WALLPAPER", menu)
    
    def initialisation():
        try:
            log_debug("Initialisation...")
            # On tente de charger l'image immédiatement si internet est là
            if attendre_internet(tentatives=24, delai=5):
                telecharger_bing(icon=icon)
            # Quoi qu'il arrive, on lance la boucle de surveillance
            threading.Thread(target=boucle_temporelle, args=(icon,), daemon=True).start()
        except Exception as e:
            log_debug(f"Erreur Init : {str(e)}")
    
    threading.Thread(target=initialisation, daemon=True).start()
    icon.run()

if __name__ == "__main__":
    try: lancer_app()
    except Exception as e:
        log_debug(f"CRASH : {str(e)}")
