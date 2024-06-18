import tkinter as tk
from tkinter import filedialog, messagebox
from ttkthemes import ThemedTk
from tkinter import ttk
import requests
import fitz  # PyMuPDF
import pandas as pd
import pyperclip

API_KEY = ""
MAX_TOKENS = 4096
SYSTEM_PROMPT_TOKENS = 50 
QUESTION_TOKENS = 50  
CHUNK_SIZE = 2000  

LIGHT_BLUE = "#ADD8E6"

class ApplicationQA:
    def __init__(self, root):
        self.root = root
        self.root.title("Question/Réponse Documentaire")
        self.root.geometry("800x600")

        self.afficher_ecran_chargement()

        # Délai pour simuler le chargement
        self.root.after(2000, self.afficher_ecran_principal)

    def afficher_ecran_chargement(self):
        self.frame_chargement = ttk.Frame(self.root)
        self.frame_chargement.pack(fill='both', expand=True)

        self.label_chargement = ttk.Label(self.frame_chargement, text="Chargement...", font=("Helvetica", 24))
        self.label_chargement.pack(expand=True)

    def afficher_ecran_principal(self):
        self.frame_chargement.pack_forget()
        self.root.geometry("1600x900")

        self.frame_principal = ttk.Frame(self.root)
        self.frame_principal.pack(fill='both', expand=True)

        self.frame_haut = ttk.Frame(self.frame_principal, style="Custom.TFrame")
        self.frame_haut.pack(fill='x')

        self.btn_ouvrir_pdf = ttk.Button(self.frame_haut, text="Ouvrir PDF", command=self.ouvrir_pdf)
        self.btn_ouvrir_pdf.pack(side='left', padx=10, pady=10)

        self.btn_ouvrir_excel = ttk.Button(self.frame_haut, text="Ouvrir Excel", command=self.ouvrir_excel)
        self.btn_ouvrir_excel.pack(side='left', padx=10, pady=10)

        self.btn_ouvrir_txt = ttk.Button(self.frame_haut, text="Ouvrir TXT", command=self.ouvrir_txt)
        self.btn_ouvrir_txt.pack(side='left', padx=10, pady=10)

        self.frame_milieu = ttk.Frame(self.frame_principal, style="Custom.TFrame")
        self.frame_milieu.pack(fill='both', expand=True)

        self.txt_affichage = tk.Text(self.frame_milieu, wrap='word', height=20)
        self.txt_affichage.pack(padx=10, pady=10, fill='both', expand=True)

        self.frame_bas = ttk.Frame(self.frame_principal, style="Custom.TFrame")
        self.frame_bas.pack(fill='both', expand=True)

        self.lbl_question = ttk.Label(self.frame_bas, text="Entrez votre question :")
        self.lbl_question.pack(pady=5)

        self.entry_question = ttk.Entry(self.frame_bas, width=50)
        self.entry_question.pack(pady=5)
        self.entry_question.bind("<Return>", self.poser_question)

        self.btn_poser = ttk.Button(self.frame_bas, text="Poser", command=self.poser_question)
        self.btn_poser.pack(pady=10)

        self.affichage_reponse = tk.Text(self.frame_bas, wrap='word', height=10, state='normal')
        self.affichage_reponse.pack(padx=10, pady=10, fill='both', expand=True)

        self.btn_copier = ttk.Button(self.frame_bas, text="Copier", command=self.copier_reponse)
        self.btn_copier.pack(pady=5)

    def ouvrir_pdf(self):
        chemin_fichier = filedialog.askopenfilename(filetypes=[("Fichiers PDF", "*.pdf")])
        if chemin_fichier:
            self.traiter_pdf(chemin_fichier)

    def ouvrir_excel(self):
        chemin_fichier = filedialog.askopenfilename(filetypes=[("Fichiers Excel", "*.xlsx")])
        if chemin_fichier:
            self.traiter_excel(chemin_fichier)

    def ouvrir_txt(self):
        chemin_fichier = filedialog.askopenfilename(filetypes=[("Fichiers Texte", "*.txt")])
        if chemin_fichier:
            self.traiter_txt(chemin_fichier)

    def traiter_pdf(self, chemin_fichier):
        try:
            doc = fitz.open(chemin_fichier)
            texte = ""
            for page in doc:
                texte += page.get_text()
            if len(texte) > 250000:
                messagebox.showwarning("Avertissement", "Le document dépasse la limite de 250 000 caractères. Seuls les premiers 250 000 caractères seront traités.")
                texte = texte[:250000]
            self.afficher_texte(texte)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la lecture du fichier PDF : {e}")

    def traiter_excel(self, chemin_fichier):
        try:
            df = pd.read_excel(chemin_fichier)
            texte = df.to_string()
            if len(texte) > 250000:
                messagebox.showwarning("Avertissement", "Le document dépasse la limite de 250 000 caractères. Seuls les premiers 250 000 caractères seront traités.")
                texte = texte[:250000]
            self.afficher_texte(texte)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la lecture du fichier Excel : {e}")

    def traiter_txt(self, chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                texte = fichier.read()
            if len(texte) > 250000:
                messagebox.showwarning("Avertissement", "Le document dépasse la limite de 250 000 caractères. Seuls les premiers 250 000 caractères seront traités.")
                texte = texte[:250000]
            self.afficher_texte(texte)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la lecture du fichier TXT : {e}")

    def afficher_texte(self, texte):
        self.txt_affichage.delete(1.0, tk.END)
        self.txt_affichage.insert(tk.END, texte)
        messagebox.showinfo("Fichier Chargé", "Fichier lu avec succès, veuillez poser vos questions")

    def poser_question(self, event=None):
        question = self.entry_question.get()
        if question:
            self.entry_question.config(state='disabled')
            self.btn_poser.config(state='disabled')
            texte = self.txt_affichage.get(1.0, tk.END)
            réponse = self.appeler_openai(question, texte)
            self.afficher_reponse(réponse)
            self.entry_question.config(state='normal')
            self.btn_poser.config(state='normal')
        else:
            messagebox.showwarning("Saisie Requise", "Veuillez entrer une question")

    def afficher_reponse(self, reponse):
        self.affichage_reponse.config(state='normal')
        self.affichage_reponse.delete(1.0, tk.END)
        self.affichage_reponse.insert(tk.END, reponse)
        self.affichage_reponse.config(state='disabled')

    def copier_reponse(self):
        reponse = self.affichage_reponse.get(1.0, tk.END)
        pyperclip.copy(reponse)
        messagebox.showinfo("Copié", "La réponse a été copiée dans le presse-papiers")

    def appeler_openai(self, question, texte):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        morceaux = [texte[i:i + CHUNK_SIZE] for i in range(0, len(texte), CHUNK_SIZE)]
        reponses = []

        for morceau in morceaux:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Vous êtes un assistant utile. Fournissez une seule réponse concise à la question basée sur le texte fourni."},
                    {"role": "user", "content": f"Texte : {morceau}\n\nQ : {question}\nR :"}
                ],
                "max_tokens": 500 
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                reponses.append(response.json()["choices"][0]["message"]["content"].strip())
            else:
                reponses.append(f"Erreur : {response.status_code} - {response.text}")
                break

        return self.selectionner_meilleure_reponse(reponses)

    def selectionner_meilleure_reponse(self, reponses):
        return reponses[0] if reponses else "Aucune réponse valide reçue."

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    root.geometry("800x600")

    style = ttk.Style()
    style.configure("Custom.TFrame", background=LIGHT_BLUE)
    style.configure("Custom.TLabel", background=LIGHT_BLUE)

    app = ApplicationQA(root)
    root.mainloop()
