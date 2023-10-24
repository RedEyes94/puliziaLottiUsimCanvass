import tkinter as tk
from tkinter import ttk
import threading
import time


def esegui_operazione():
    # Simuliamo un'operazione che richiede del tempo
    for i in range(1, 101):
        time.sleep(0.1)  # Simuliamo un ritardo di 0.1 secondi
        progressbar_var.set(i)  # Aggiorniamo il valore della barra di avanzamento
    # Quando l'operazione è completata, nascondiamo la barra di avanzamento
    progressbar.stop()
    progressbar.grid_remove()


def avvia_operazione():
    # Disabilita il pulsante mentre l'operazione è in corso
    start_button.config(state=tk.DISABLED)

    # Mostra la barra di avanzamento
    progressbar.grid()

    # Avvia un thread per eseguire l'operazione in background
    thread = threading.Thread(target=esegui_operazione)
    thread.start()


# Creazione della finestra principale
root = tk.Tk()
root.title("Esempio Barra di Avanzamento")

# Creazione della barra di avanzamento
progressbar_var = tk.IntVar()
progressbar = ttk.Progressbar(root, mode='determinate', variable=progressbar_var)
progressbar.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
progressbar.grid_remove()  # Nascondi la barra di avanzamento inizialmente

# Creazione del pulsante per avviare l'operazione
start_button = tk.Button(root, text="Avvia Operazione", command=avvia_operazione)
start_button.grid(row=1, column=0, padx=20, pady=10)

# Pulsante per uscire dall'applicazione
exit_button = tk.Button(root, text="Esci", command=root.quit)
exit_button.grid(row=1, column=1, padx=20, pady=10)

root.mainloop()
