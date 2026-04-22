# ==============================================================================
# LOGICIEL : BG WALLPAPER
# CONCEPTION : FG DEVELOPPEMENT & GEMINI
# DATE : 08 avril 2026
# (c) Tous droits réservés.
# CONTACT : florentgerard@fgdeveloppement.com
# ==============================================================================

import sys
import os
import requests
import ctypes
import datetime
import locale
import threading
import time
import webbrowser
import tkinter as tk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# --- CONFIGURATION DES CHEMINS ---
if getattr(sys, 'frozen', False):
    # Dossier de l'exécutable (ex: .../dist)
    BASE_PATH = os.path.dirname(sys.executable)
    # Si on est dans le dossier 'dist', on remonte d'un cran pour atteindre la racine du projet
    if os.path.basename(BASE_PATH).lower() == "dist":
        BASE_PATH = os.path.dirname(BASE_PATH)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(BASE_PATH, "img", "logo", "bg-wallpaper.jpg")

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "French_France.1252")
    except:
        pass

infos_actuelles = {
    "titre": "En attente...",
    "localisation": "En attente...",
    "date": "Non définie",
    "lien_image": "",
    "lien_page": "https://bing.gifposter.com/fr"
}

def obtenir_dossier_du_mois():
    maintenant = datetime.datetime.now()
    annee = maintenant.strftime("%Y")
    nom_mois = maintenant.strftime("%m_%B").lower()
    dossier = os.path.join(BASE_PATH, "images", annee, nom_mois)
    if not os.path.exists(dossier):
        os.makedirs(dossier, exist_ok=True)
    return dossier

def telecharger_bing():
    global infos_actuelles
    try:
        api_url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=fr-FR"
        response = requests.get(api_url, timeout=10).json()
        data = response['images'][0]

        maintenant = datetime.datetime.now()
        date_str = maintenant.strftime("%d-%m-%Y")
        dossier_dest = obtenir_dossier_du_mois()
        
        chemin_img = os.path.join(dossier_dest, f"bing_{date_str}.jpg")
        chemin_txt = os.path.join(dossier_dest, f"bing_{date_str}.txt")
        log_path = os.path.join(dossier_dest, "bg_wallpaper_log.txt")

        infos_actuelles["titre"] = data.get('title', 'Sans titre')
        infos_actuelles["localisation"] = data.get('copyright', 'Localisation inconnue')
        infos_actuelles["date"] = maintenant.strftime("%d/%m/%Y à %H:%M")
        infos_actuelles["lien_image"] = "https://www.bing.com" + data['url']
        infos_actuelles["lien_page"] = "https://bing.gifposter.com/fr" + data['url']

        if not os.path.exists(chemin_img):
            img_res = requests.get(infos_actuelles["lien_image"])
            with open(chemin_img, 'wb') as f:
                f.write(img_res.content)
            
            with open(chemin_txt, 'w', encoding='utf-8') as f:
                f.write(f"TITRE : {infos_actuelles['titre']}\nDATE : {infos_actuelles['date']}\nLOCALISATION : {infos_actuelles['localisation']}\nLIEN PAGE : {infos_actuelles['lien_page']}")

            with open(log_path, 'a', encoding='utf-8') as log:
                log.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - MAJ auto - Succès\n")

            ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)
            return True
    except Exception as e:
        pass
    return False

# --- INTERFACE GRAPHIQUE ---

def centrer_fenetre(fenetre, largeur, hauteur):
    screen_width = fenetre.winfo_screenwidth()
    screen_height = fenetre.winfo_screenheight()
    x = (screen_width // 2) - (largeur // 2)
    y = (screen_height // 2) - (hauteur // 2)
    fenetre.geometry(f"{largeur}x{hauteur}+{x}+{y}")

def ouvrir_page_bing(icon=None):
    if infos_actuelles["lien_page"]:
        webbrowser.open(infos_actuelles["lien_page"])

def afficher_infos_custom(icon):
    def create_window():
        root = tk.Tk()
        root.title("BG WALLPAPER - Infos du jour")
        largeur_fen, hauteur_fen = 450, 550
        centrer_fenetre(root, largeur_fen, hauteur_fen)
        root.attributes("-topmost", True)
        root.resizable(False, False)

        def fermer_fenetre():
            root.quit()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", fermer_fenetre)

        try:
            dossier = obtenir_dossier_du_mois()
            date_str = datetime.datetime.now().strftime("%d-%m-%Y")
            chemin_img = os.path.join(dossier, f"bing_{date_str}.jpg")
            
            if os.path.exists(chemin_img):
                img_pil = Image.open(chemin_img)
                img_pil.thumbnail((400, 300))
                img_tk = ImageTk.PhotoImage(img_pil)
                label_img = tk.Label(root, image=img_tk)
                label_img.image = img_tk 
                label_img.pack(pady=10)
        except:
            tk.Label(root, text="\nImage non chargée.\n").pack()

        tk.Label(root, text=infos_actuelles["titre"], font=("Arial", 12, "bold"), wraplength=400).pack(pady=5)
        tk.Label(root, text=infos_actuelles["localisation"], wraplength=400, font=("Arial", 10)).pack(pady=5)
        tk.Label(root, text=f"Mise à jour : {infos_actuelles['date']}", fg="gray").pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="En savoir plus", command=ouvrir_page_bing, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Fermer", command=fermer_fenetre, width=15).pack(side=tk.LEFT, padx=5)

        root.mainloop()

    t = threading.Thread(target=create_window)
    t.daemon = True
    t.start()

# --- LOGIQUE DE BOUCLE OPTIMISÉE ---

def quitter_app(icon):
    icon.stop()
    os._exit(0)

def boucle_temporelle(icon):
    while True:
        maintenant = datetime.datetime.now()
        
        # On ne tente le téléchargement que s'il est plus de 01h00 du matin
        # Cela évite de chercher l'image de demain avant qu'elle n'existe
        if maintenant.hour >= 1:
            telecharger_bing()
        
        # On vérifie toutes les 15 minutes (900 secondes)
        # C'est très léger pour le PC et très réactif au réveil de veille
        time.sleep(900)

def lancer_app():
    try:
        image_logo = Image.open(LOGO_PATH)
    except:
        image_logo = Image.new('RGB', (64, 64), color='blue')
    
    menu = pystray.Menu(
        item('Voir l\'image du jour', afficher_infos_custom),
        item('En savoir plus (Bing.com)', ouvrir_page_bing),
        pystray.Menu.SEPARATOR,
        item('Actualiser maintenant', lambda icon: telecharger_bing()),
        item('Quitter BG WALLPAPER', quitter_app)
    )

    icon = pystray.Icon("BG_Wallpaper", image_logo, "BG WALLPAPER", menu)
    threading.Thread(target=boucle_temporelle, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    lancer_app()