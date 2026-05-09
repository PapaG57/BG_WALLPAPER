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

def obtenir_dossier_du_mois(dt=None):
    if dt is None:
        dt = datetime.datetime.now()
    annee = dt.strftime("%Y")
    nom_mois = dt.strftime("%m_%B").lower()
    dossier = os.path.join(BASE_PATH, "images", annee, nom_mois)
    if not os.path.exists(dossier):
        os.makedirs(dossier, exist_ok=True)
    return dossier

def telecharger_bing():
    global infos_actuelles
    try:
        # On récupère les 8 dernières images (maximum autorisé par l'API officielle)
        api_url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=fr-FR"
        response = requests.get(api_url, timeout=10).json()
        
        maintenant = datetime.datetime.now()
        date_aujourdhui = maintenant.strftime("%d-%m-%Y")
        succes_un_au_moins = False

        for image_data in response.get('images', []):
            # Extraire la date de l'image (format YYYYMMDD)
            date_brute = image_data.get('startdate')
            dt_image = datetime.datetime.strptime(date_brute, "%Y%m%d")
            date_str = dt_image.strftime("%d-%m-%Y")
            
            dossier_dest = obtenir_dossier_du_mois(dt_image)
            chemin_img = os.path.join(dossier_dest, f"bing_{date_str}.jpg")
            chemin_txt = os.path.join(dossier_dest, f"bing_{date_str}.txt")
            log_path = os.path.join(dossier_dest, "bg_wallpaper_log.txt")

            titre = image_data.get('title', 'Sans titre')
            copyright_info = image_data.get('copyright', 'Localisation inconnue')
            url_image = "https://www.bing.com" + image_data['url']
            # Forcer la résolution UHD (4K) si disponible dans l'URL
            url_image = url_image.replace("1920x1080", "3840x2160")
            if "&uhd=1" not in url_image:
                url_image += "&uhd=1"
            url_page = "https://bing.gifposter.com/fr" + image_data['url']

            # Si c'est l'image d'aujourd'hui, on met à jour les infos globales
            if date_str == date_aujourdhui:
                infos_actuelles["titre"] = titre
                infos_actuelles["localisation"] = copyright_info
                infos_actuelles["date"] = dt_image.strftime("%d/%m/%Y")
                infos_actuelles["lien_image"] = url_image
                infos_actuelles["lien_page"] = url_page

            # Téléchargement si l'image n'existe pas
            if not os.path.exists(chemin_img):
                img_res = requests.get(url_image, timeout=15)
                if img_res.status_code == 200:
                    with open(chemin_img, 'wb') as f:
                        f.write(img_res.content)
                    
                    with open(chemin_txt, 'w', encoding='utf-8') as f:
                        f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {copyright_info}\nLIEN PAGE : {url_page}")

                    with open(log_path, 'a', encoding='utf-8') as log:
                        log.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - Téléchargement {date_str} - Succès\n")
                    
                    # Appliquer comme fond d'écran si c'est celle d'aujourd'hui
                    if date_str == date_aujourdhui:
                        ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)
                    
                    succes_un_au_moins = True

        return succes_un_au_moins
    except Exception as e:
        print(f"Erreur téléchargement : {e}")
    return False

def telecharger_image_specifique(date_voulue):
    """
    Télécharge une image spécifique parmi les 8 derniers jours si elle existe.
    date_voulue: string au format "dd-mm-yyyy"
    """
    try:
        api_url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=fr-FR"
        response = requests.get(api_url, timeout=10).json()
        
        for image_data in response.get('images', []):
            date_brute = image_data.get('startdate')
            dt_image = datetime.datetime.strptime(date_brute, "%Y%m%d")
            date_str = dt_image.strftime("%d-%m-%Y")
            
            if date_str == date_voulue:
                dossier_dest = obtenir_dossier_du_mois(dt_image)
                chemin_img = os.path.join(dossier_dest, f"bing_{date_str}.jpg")
                chemin_txt = os.path.join(dossier_dest, f"bing_{date_str}.txt")
                log_path = os.path.join(dossier_dest, "bg_wallpaper_log.txt")

                titre = image_data.get('title', 'Sans titre')
                copyright_info = image_data.get('copyright', 'Localisation inconnue')
                url_image = "https://www.bing.com" + image_data['url']
                
                # Forcer la résolution UHD (4K)
                url_image = url_image.replace("1920x1080", "3840x2160")
                if "&uhd=1" not in url_image:
                    url_image += "&uhd=1"
                
                url_page = "https://bing.gifposter.com/fr" + image_data['url']

                img_res = requests.get(url_image, timeout=15)
                if img_res.status_code == 200:
                    with open(chemin_img, 'wb') as f:
                        f.write(img_res.content)
                    
                    with open(chemin_txt, 'w', encoding='utf-8') as f:
                        f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {copyright_info}\nLIEN PAGE : {url_page}")

                    with open(log_path, 'a', encoding='utf-8') as log:
                        log.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - Récupération manuelle {date_str} - Succès\n")
                    
                    ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)
                    return True, f"Image du {date_str} récupérée et appliquée !"
        
        return False, "Image non trouvée dans les 8 derniers jours."
    except Exception as e:
        return False, f"Erreur : {str(e)}"

def ouvrir_recuperation_manuelle(icon=None):
    def create_download_window():
        root = tk.Tk()
        root.title("BG WALLPAPER - Récupérer une image")
        centrer_fenetre(root, 400, 250)
        root.attributes("-topmost", True)
        root.resizable(False, False)

        tk.Label(root, text="Choisir une image parmi les 8 derniers jours :", 
                 font=("Arial", 10, "bold")).pack(pady=15)

        # Récupérer les dates disponibles via l'API pour remplir le menu
        dates_dispo = []
        try:
            api_url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=fr-FR"
            res = requests.get(api_url, timeout=5).json()
            for img in res.get('images', []):
                dt = datetime.datetime.strptime(img['startdate'], "%Y%m%d")
                dates_dispo.append(dt.strftime("%d-%m-%Y"))
        except:
            # Fallback : dates calculées (peut être imprécis si l'API est décalée)
            for i in range(8):
                d = datetime.datetime.now() - datetime.timedelta(days=i)
                dates_dispo.append(d.strftime("%d-%m-%Y"))

        variable = tk.StringVar(root)
        variable.set(dates_dispo[0])
        
        opt_menu = tk.OptionMenu(root, variable, *dates_dispo)
        opt_menu.config(width=20)
        opt_menu.pack(pady=10)

        label_status = tk.Label(root, text="", fg="blue")
        label_status.pack(pady=5)

        def lancer_telechargement():
            date_sel = variable.get()
            label_status.config(text="Téléchargement en cours...", fg="orange")
            root.update()
            
            succes, msg = telecharger_image_specifique(date_sel)
            if succes:
                label_status.config(text=msg, fg="green")
                
                # Affichage de l'aperçu de l'image récupérée
                try:
                    # On retrouve le chemin de l'image qu'on vient de télécharger
                    dt_obj = datetime.datetime.strptime(date_sel, "%d-%m-%Y")
                    dossier = obtenir_dossier_du_mois(dt_obj)
                    chemin_img = os.path.join(dossier, f"bing_{date_sel}.jpg")
                    
                    if os.path.exists(chemin_img):
                        # Agrandir un peu la fenêtre pour l'aperçu et les infos
                        centrer_fenetre(root, 450, 650)
                        
                        img_pil = Image.open(chemin_img)
                        img_pil.thumbnail((400, 300))
                        img_tk = ImageTk.PhotoImage(img_pil)
                        
                        # Création ou mise à jour du label d'aperçu
                        if not hasattr(root, 'label_preview'):
                            root.label_preview = tk.Label(root)
                            root.label_preview.pack(pady=10)
                        
                        root.label_preview.config(image=img_tk)
                        root.label_preview.image = img_tk

                        # Récupération et affichage des infos (titre et lieu)
                        infos_sup = ""
                        chemin_txt = chemin_img.replace(".jpg", ".txt")
                        if os.path.exists(chemin_txt):
                            try:
                                with open(chemin_txt, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    # Extraction simple pour l'affichage
                                    for line in content.split("\n"):
                                        if line.startswith("TITRE :"):
                                            infos_sup += line + "\n"
                                        if line.startswith("LOCALISATION :"):
                                            infos_sup += line
                            except:
                                pass
                        
                        if not hasattr(root, 'label_infos_preview'):
                            root.label_infos_preview = tk.Label(root, font=("Arial", 9), wraplength=400, justify=tk.CENTER)
                            root.label_infos_preview.pack(pady=5)
                        
                        root.label_infos_preview.config(text=infos_sup)
                        
                        # Modifier le bouton pour qu'il serve à fermer
                        btn_dl.config(text="Fermer", command=root.destroy, bg="#6c757d")
                except Exception as e:
                    print(f"Erreur aperçu : {e}")
            else:
                label_status.config(text=msg, fg="red")

        btn_dl = tk.Button(root, text="Récupérer et Appliquer", command=lancer_telechargement, 
                  bg="#28a745", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5)
        btn_dl.pack(pady=15)

        root.mainloop()

    threading.Thread(target=create_download_window, daemon=True).start()

def lister_images_archivees():
    images = []
    base_images = os.path.join(BASE_PATH, "images")
    if not os.path.exists(base_images):
        return images
    
    for root, dirs, files in os.walk(base_images):
        for file in files:
            if file.endswith(".jpg") and file.startswith("bing_"):
                chemin_img = os.path.join(root, file)
                date_str = file.replace("bing_", "").replace(".jpg", "")
                
                # Vérifier le format de la date pour le tri
                try:
                    dt_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                except:
                    continue

                chemin_txt = chemin_img.replace(".jpg", ".txt")
                titre = "Sans titre"
                if os.path.exists(chemin_txt):
                    try:
                        with open(chemin_txt, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith("TITRE : "):
                                    titre = line.replace("TITRE : ", "").strip()
                                    break
                    except:
                        pass
                
                images.append({
                    "date": date_str,
                    "dt": dt_obj,
                    "titre": titre,
                    "chemin": chemin_img,
                    "chemin_txt": chemin_txt
                })
    
    # Trier par date décroissante
    images.sort(key=lambda x: x["dt"], reverse=True)
    return images

def afficher_historique(icon):
    def create_history_window():
        root = tk.Tk()
        root.title("BG WALLPAPER - Historique")
        centrer_fenetre(root, 750, 550)
        root.attributes("-topmost", True)
        root.focus_force()

        # Frame gauche : Liste des images
        frame_liste = tk.Frame(root)
        frame_liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame_liste, text="Archives disponibles :", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        scrollbar = tk.Scrollbar(frame_liste)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame_liste, yscrollcommand=scrollbar.set, font=("Arial", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Frame droite : Aperçu et détails
        frame_apercu = tk.Frame(root, width=380)
        frame_apercu.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        label_titre_img = tk.Label(frame_apercu, text="Sélectionnez une image", font=("Arial", 11, "bold"), wraplength=350)
        label_titre_img.pack(pady=5)
        
        label_img_prev = tk.Label(frame_apercu)
        label_img_prev.pack(pady=10)
        
        label_infos_det = tk.Label(frame_apercu, text="", wraplength=350, justify=tk.LEFT, font=("Arial", 9))
        label_infos_det.pack(pady=5, fill=tk.X)

        images_dispo = lister_images_archivees()
        for img in images_dispo:
            listbox.insert(tk.END, f"{img['date']} - {img['titre']}")

        def on_select(event):
            selection = event.widget.curselection()
            if selection:
                idx = selection[0]
                img_data = images_dispo[idx]
                
                label_titre_img.config(text=img_data["titre"])
                
                try:
                    img_pil = Image.open(img_data["chemin"])
                    img_pil.thumbnail((350, 250))
                    img_tk = ImageTk.PhotoImage(img_pil)
                    label_img_prev.config(image=img_tk)
                    label_img_prev.image = img_tk
                except:
                    label_img_prev.config(image="", text="Erreur de chargement")

                # Récupération des détails
                details = f"Date : {img_data['date']}\n"
                if os.path.exists(img_data["chemin_txt"]):
                    try:
                        with open(img_data["chemin_txt"], 'r', encoding='utf-8') as f:
                            for line in f:
                                if "LOCALISATION :" in line:
                                    details += f"Lieu : {line.replace('LOCALISATION :', '').strip()}\n"
                                if "LIEN PAGE :" in line:
                                    # On garde le lien pour un futur usage si besoin
                                    pass
                    except:
                        pass
                label_infos_det.config(text=details)

        listbox.bind('<<ListboxSelect>>', on_select)

        def appliquer_selection():
            selection = listbox.curselection()
            if selection:
                img_data = images_dispo[selection[0]]
                if os.path.exists(img_data["chemin"]):
                    ctypes.windll.user32.SystemParametersInfoW(20, 0, img_data["chemin"], 3)

        btn_apply = tk.Button(frame_apercu, text="Définir comme fond d'écran", 
                               command=appliquer_selection, bg="#0078d7", fg="white", 
                               font=("Arial", 10, "bold"), pady=8)
        btn_apply.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        btn_open_dir = tk.Button(frame_apercu, text="Ouvrir le dossier des images", 
                                  command=lambda: os.startfile(os.path.join(BASE_PATH, "images")))
        btn_open_dir.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        if images_dispo:
            listbox.select_set(0)
            listbox.event_generate("<<ListboxSelect>>")

        root.mainloop()

    threading.Thread(target=create_history_window, daemon=True).start()

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
        item('Historique des images', afficher_historique),
        item('Récupérer une image passée', ouvrir_recuperation_manuelle),
        item('Ouvrir le dossier des images', lambda icon: os.startfile(os.path.join(BASE_PATH, "images"))),
        pystray.Menu.SEPARATOR,
        item('En savoir plus (Bing.com)', ouvrir_page_bing),
        item('Actualiser maintenant', lambda icon: telecharger_bing()),
        pystray.Menu.SEPARATOR,
        item('Quitter BG WALLPAPER', quitter_app)
    )

    icon = pystray.Icon("BG_Wallpaper", image_logo, "BG WALLPAPER", menu)
    
    # Lancement initial pour remplir infos_actuelles
    telecharger_bing()
    
    threading.Thread(target=boucle_temporelle, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    lancer_app()