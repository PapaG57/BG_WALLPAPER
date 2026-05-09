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
    BASE_PATH = os.path.dirname(sys.executable)
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
    "titre": "Chargement...",
    "localisation": "Vérification de la connexion...",
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
    maintenant = datetime.datetime.now()
    date_aujourdhui = maintenant.strftime("%d-%m-%Y")
    
    try:
        api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=fr-FR&ts={int(time.time())}"
        response = requests.get(api_url, timeout=10).json()
        
        for image_data in response.get('images', []):
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
            url_image = url_image.replace("1920x1080", "3840x2160")
            if "&uhd=1" not in url_image:
                url_image += "&uhd=1"
            url_page = "https://bing.gifposter.com/fr" + image_data['url']

            if not os.path.exists(chemin_img):
                img_res = requests.get(url_image, timeout=15)
                if img_res.status_code == 200:
                    with open(chemin_img, 'wb') as f:
                        f.write(img_res.content)
                    with open(chemin_txt, 'w', encoding='utf-8') as f:
                        f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {copyright_info}\nLIEN PAGE : {url_page}")
                    with open(log_path, 'a', encoding='utf-8') as log:
                        log.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - Téléchargement {date_str} - Succès\n")
                    
                    if date_str == date_aujourdhui:
                        ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)

            if date_str == date_aujourdhui:
                infos_actuelles["titre"] = titre
                infos_actuelles["localisation"] = copyright_info
                infos_actuelles["date"] = date_str
                infos_actuelles["lien_image"] = url_image
                infos_actuelles["lien_page"] = url_page
    except Exception as e:
        print(f"Erreur API : {e}")

    # Fallback sur le local si toujours rien
    if infos_actuelles["titre"] in ["Chargement...", "En attente..."]:
        archives = lister_images_archivees()
        if archives:
            derniere = archives[0]
            infos_actuelles["titre"] = derniere["titre"]
            infos_actuelles["date"] = derniere["date"]
            infos_actuelles["lien_image"] = derniere["chemin"]
            if os.path.exists(derniere["chemin_txt"]):
                try:
                    with open(derniere["chemin_txt"], 'r', encoding='utf-8') as f:
                        for line in f:
                            if "LOCALISATION :" in line:
                                infos_actuelles["localisation"] = line.replace("LOCALISATION :", "").strip()
                except: pass
    return True

def telecharger_image_directe(image_data):
    try:
        date_brute = image_data.get('startdate')
        dt_image = datetime.datetime.strptime(date_brute, "%Y%m%d")
        date_str = dt_image.strftime("%d-%m-%Y")
        
        dossier_dest = obtenir_dossier_du_mois(dt_image)
        chemin_img = os.path.join(dossier_dest, f"bing_{date_str}.jpg")
        chemin_txt = os.path.join(dossier_dest, f"bing_{date_str}.txt")
        log_path = os.path.join(dossier_dest, "bg_wallpaper_log.txt")

        titre = image_data.get('title', 'Sans titre')
        url_image = "https://www.bing.com" + image_data['url']
        url_image = url_image.replace("1920x1080", "3840x2160")
        if "&uhd=1" not in url_image: url_image += "&uhd=1"
        url_page = "https://bing.gifposter.com/fr" + image_data['url']

        if not os.path.exists(chemin_img):
            img_res = requests.get(url_image, timeout=15)
            if img_res.status_code == 200:
                with open(chemin_img, 'wb') as f:
                    f.write(img_res.content)
                with open(chemin_txt, 'w', encoding='utf-8') as f:
                    f.write(f"TITRE : {titre}\nDATE : {date_str}\nLOCALISATION : {image_data.get('copyright')}\nLIEN PAGE : {url_page}")
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - Récupération directe {date_str}\n")
        
        ctypes.windll.user32.SystemParametersInfoW(20, 0, chemin_img, 3)
        return True, f"Image '{titre}' activée avec succès !"
    except Exception as e:
        return False, f"Erreur : {str(e)}"

def ouvrir_recuperation_manuelle(icon=None):
    def create_download_window():
        root = tk.Tk()
        root.title("BG WALLPAPER - Récupérer une image")
        centrer_fenetre(root, 550, 400)
        root.attributes("-topmost", True)

        tk.Label(root, text="Choisir une image parmi les 16 derniers jours :", font=("Arial", 10, "bold")).pack(pady=15)

        options = []
        map_data = {}
        
        try:
            for idx in [0, 8]:
                api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={idx}&n=8&mkt=fr-FR&ts={int(time.time())}"
                res = requests.get(api_url, timeout=5).json()
                for img in res.get('images', []):
                    d_str = datetime.datetime.strptime(img['startdate'], "%Y%m%d").strftime("%d-%m-%Y")
                    lib = f"{d_str} : {img.get('title', 'Sans titre')}"
                    if lib not in options:
                        options.append(lib)
                        map_data[lib] = img
        except:
            tk.Label(root, text="Erreur de connexion API.", fg="red").pack()

        if not options:
            tk.Button(root, text="Fermer", command=root.destroy).pack(pady=10)
            return

        variable = tk.StringVar(root)
        variable.set(options[0])
        tk.OptionMenu(root, variable, *options).pack(pady=10)

        label_status = tk.Label(root, text="", fg="blue", wraplength=500)
        label_status.pack(pady=5)

        def action():
            sel = variable.get()
            data = map_data.get(sel)
            if not data: return
            label_status.config(text="Traitement en cours...", fg="orange")
            root.update()
            
            ok, msg = telecharger_image_directe(data)
            if ok:
                label_status.config(text=msg, fg="green")
                # Afficher l'aperçu
                try:
                    d_str = datetime.datetime.strptime(data['startdate'], "%Y%m%d").strftime("%d-%m-%Y")
                    path = os.path.join(obtenir_dossier_du_mois(datetime.datetime.strptime(data['startdate'], "%Y%m%d")), f"bing_{d_str}.jpg")
                    if os.path.exists(path):
                        centrer_fenetre(root, 550, 750)
                        img_tk = ImageTk.PhotoImage(Image.open(path).resize((450, 250)))
                        if not hasattr(root, 'p'):
                            root.p = tk.Label(root)
                            root.p.pack(pady=10)
                        root.p.config(image=img_tk)
                        root.p.image = img_tk
                        
                        inf = f"TITRE : {data.get('title')}\nLOCALISATION : {data.get('copyright')}"
                        if not hasattr(root, 'i'):
                            root.i = tk.Label(root, font=("Arial", 9), wraplength=500)
                            root.i.pack(pady=5)
                        root.i.config(text=inf)
                        btn.config(text="Fermer", command=root.destroy, bg="#6c757d")
                except: pass
            else:
                label_status.config(text=msg, fg="red")

        btn = tk.Button(root, text="Récupérer et Appliquer", command=action, bg="#28a745", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8)
        btn.pack(pady=15)
        root.mainloop()

    threading.Thread(target=create_download_window, daemon=True).start()

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
                    images.append({"date": date_str, "dt": dt, "titre": titre, "chemin": os.path.join(root, file), "chemin_txt": txt_path})
                except: continue
    images.sort(key=lambda x: x["dt"], reverse=True)
    return images

def afficher_historique(icon):
    def create_history_window():
        root = tk.Tk(); root.title("BG WALLPAPER - Historique")
        centrer_fenetre(root, 750, 550); root.attributes("-topmost", True)
        frame_liste = tk.Frame(root); frame_liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame_liste, text="Archives disponibles :", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        scrollbar = tk.Scrollbar(frame_liste); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(frame_liste, yscrollcommand=scrollbar.set, font=("Arial", 9)); listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        frame_apercu = tk.Frame(root, width=380); frame_apercu.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        l_titre = tk.Label(frame_apercu, text="Sélectionnez une image", font=("Arial", 11, "bold"), wraplength=350); l_titre.pack(pady=5)
        l_img = tk.Label(frame_apercu); l_img.pack(pady=10)
        l_det = tk.Label(frame_apercu, text="", wraplength=350, justify=tk.LEFT, font=("Arial", 9)); l_det.pack(pady=5, fill=tk.X)
        imgs = lister_images_archivees()
        for i in imgs: listbox.insert(tk.END, f"{i['date']} - {i['titre']}")
        def on_select(e):
            sel = e.widget.curselection()
            if sel:
                d = imgs[sel[0]]; l_titre.config(text=d["titre"])
                try:
                    p = Image.open(d["chemin"]); p.thumbnail((350, 250))
                    tk_p = ImageTk.PhotoImage(p); l_img.config(image=tk_p); l_img.image = tk_p
                except: l_img.config(image="", text="Erreur")
                det = f"Date : {d['date']}\n"
                if os.path.exists(d["chemin_txt"]):
                    try:
                        with open(d["chemin_txt"], 'r', encoding='utf-8') as f:
                            for line in f:
                                if "LOCALISATION :" in line: det += f"Lieu : {line.replace('LOCALISATION :', '').strip()}\n"
                    except: pass
                l_det.config(text=det)
        listbox.bind('<<ListboxSelect>>', on_select)
        def apply():
            sel = listbox.curselection()
            if sel: ctypes.windll.user32.SystemParametersInfoW(20, 0, imgs[sel[0]]["chemin"], 3)
        tk.Button(frame_apercu, text="Définir comme fond d'écran", command=apply, bg="#0078d7", fg="white", font=("Arial", 10, "bold"), pady=8).pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(frame_apercu, text="Ouvrir le dossier", command=lambda: os.startfile(os.path.join(BASE_PATH, "images"))).pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        if imgs: listbox.select_set(0); listbox.event_generate("<<ListboxSelect>>")
        root.mainloop()
    threading.Thread(target=create_history_window, daemon=True).start()

def centrer_fenetre(f, l, h):
    sw = f.winfo_screenwidth(); sh = f.winfo_screenheight()
    f.geometry(f"{l}x{h}+{(sw-l)//2}+{(sh-h)//2}")

def ouvrir_page_bing(icon=None):
    if infos_actuelles["lien_page"]: webbrowser.open(infos_actuelles["lien_page"])

def afficher_infos_custom(icon):
    def create_window():
        root = tk.Tk(); root.title("BG WALLPAPER - Infos du jour")
        centrer_fenetre(root, 450, 600); root.attributes("-topmost", True)
        try:
            d = obtenir_dossier_du_mois(); path = os.path.join(d, f"bing_{datetime.datetime.now().strftime('%d-%m-%Y')}.jpg")
            if os.path.exists(path):
                p = Image.open(path); p.thumbnail((400, 300))
                tk_p = ImageTk.PhotoImage(p); l = tk.Label(root, image=tk_p); l.image = tk_p; l.pack(pady=10)
        except: tk.Label(root, text="\nImage non chargée.\n").pack()
        tk.Label(root, text=infos_actuelles["titre"], font=("Arial", 12, "bold"), wraplength=400).pack(pady=5)
        tk.Label(root, text=infos_actuelles["localisation"], wraplength=400, font=("Arial", 10)).pack(pady=5)
        tk.Label(root, text=f"Mise à jour : {infos_actuelles['date']}", fg="gray").pack(pady=5)
        f = tk.Frame(root); f.pack(pady=20)
        tk.Button(f, text="En savoir plus", command=ouvrir_page_bing, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="Fermer", command=root.destroy, width=15).pack(side=tk.LEFT, padx=5)
        root.mainloop()
    threading.Thread(target=create_window, daemon=True).start()

def quitter_app(icon): icon.stop(); os._exit(0)

def boucle_temporelle(icon):
    while True:
        if datetime.datetime.now().hour >= 1: telecharger_bing()
        time.sleep(900)

def lancer_app():
    try: image_logo = Image.open(LOGO_PATH)
    except: image_logo = Image.new('RGB', (64, 64), color='blue')
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
    telecharger_bing()
    threading.Thread(target=boucle_temporelle, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    lancer_app()
