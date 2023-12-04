import csv
import logging
import numpy as np
import tkinter as tk
import warnings
import pandas as pd
from tkinter import ttk
from tkinter import messagebox

import cx_Oracle
import requests
from ttkthemes import ThemedStyle

import db_connection
from script_pulizia import Pulizia
from script_sdno import SDNO


def add_lot():
    msisdn_start = first_num_entry.get()
    msisdn_end = last_num_entry.get()
    imsi_start = additional_info_entry.get()
    imsi_end = another_field_entry.get()
    descrizione = descrizione_field_entry.get()
    if msisdn_start and msisdn_end and imsi_start and imsi_end:
        usim_tot = calcola_totale_lotto(msisdn_start, msisdn_end, imsi_start, imsi_end, descrizione)
        usim_tot = str(usim_tot)
        if int(usim_tot) <= 0:
            messagebox.showinfo("Quantità MSISDN/IMSI non conforme",
                                "Il numero di MSISDN inseriti non è pari al numero di IMSI")

        lot_tree.insert("", "end",
                        values=(msisdn_start, msisdn_end, imsi_start, imsi_end, usim_tot, usim_tot, descrizione))
        first_num_entry.delete(0, tk.END)
        last_num_entry.delete(0, tk.END)
        additional_info_entry.delete(0, tk.END)
        another_field_entry.delete(0, tk.END)


def calcola_totale_lotto(msisdn_start, msisdn_end, imsi_start, imsi_end, descrizione):
    filename = "output.csv"
    filename_1 = "output_sdno.csv"
    rows = []
    sdno = []
    if msisdn_start != '0' and msisdn_end != '0':
        for msisdn, imsi in zip(range(int(msisdn_start), int(msisdn_end) + 1),
                                range(int(imsi_start), int(imsi_end) + 1)):
            rows.append((str(msisdn), str(imsi), descrizione))
    elif imsi_start != '0' and imsi_end != '0':
        for imsi in range(int(imsi_start), int(imsi_end) + 1):
            rows.append((";",str(imsi), descrizione))

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(rows)

    # sdno.append((int(msisdn_start), int(msisdn_end)))
    sdno.append((int(imsi_start), int(imsi_end), descrizione))
    with open(filename_1, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(sdno)

    print(f"CSV file '{filename}' created successfully.")
    return len(rows)


# funzione che cancella i lotti dalla tabella
def delete_lot():
    selected_item = lot_tree.selection()
    if selected_item:
        lot_tree.delete(selected_item)
    # pulisco il file
    with open("output.csv", mode='w', newline='') as file:
        file.write('')  # Scrivi una stringa vuota nel file
    with open("output_sdno.csv", mode='w', newline='') as file:
        file.write('')  # Scrivi una stringa vuota nel file


# Funzione che aggiorna la gui
def aggiorna_tabella_gui(item_id, new_list):
    # Imposta nuovi valori per l'elemento
    lot_tree.item(item_id,
                  values=new_list)

    # Aggiorna la GUI
    lot_tree.update_idletasks()


# Funzione per eseguire le operazioni selezionate
def switch_sistema(clean,cat):
    if operazione1_checkbox.instate(['selected']):
        print("Avvio pulizia su RETE")
        sim_pulite_rete = clean.pulizia_usim_su_rete(recovery=False, catena=cat)
        print("Totale sim pulite : " + str(sim_pulite_rete))
        #usim_rimaste_su_rete = totale_sim - (sim_pulite_rete / 2)
        #totale_residuo = int(usim_rimaste_su_rete)
        #if totale_residuo < 0:
           # totale_residuo = 0
        #new_list = (values[0], values[1], values[2], values[3], totale_residuo, values[5], values[6])

        #aggiorna_tabella_gui(item_id=item, new_list=new_list)
        '''messagebox.showinfo("Avviso sulla pulizia",
                            "Pulizia su Rete completata")'''

    if operazione2_checkbox.instate(['selected']):
        print("Avvio pulizia su NETDB")

        clean.pulizia_netdb(catena=catena)
        messagebox.showinfo("Avviso sulla pulizia",
                            "Creato il file per la pulizia su NETDB (generato il file CTL)")

    if operazione3_checkbox.instate(['selected']):
        print("Avvio pulizia su MRM")
    if operazione4_checkbox.instate(['selected']):
        print("Avvio pulizia su OCS")


def start_cleanup():
    response = messagebox.askquestion("Avvia pulizia",
                                      "Sei sicuro di avviare la pulizia sui sistemi RETE? Assicurati di aver aperto il tunnel SSH e avviato il CRT su BHLINAPP")
    if response == 'yes':
        if check_catena() == 0:
            index = 0
            print("Pulizia avviata")
            print("Dati in tabella:")
            '''for item in lot_tree.get_children():
                values = lot_tree.item(item, "values")
                if values:'''
            print("Avvio pulizia su catena: " + catena.get())
            clean = Pulizia(catena=catena.get())

            switch_sistema(clean, catena.get() )

        messagebox.showinfo("Avviso sulla pulizia",
                            "Pulizia su Rete completata")
    else:
        print("Pulizia NON avviata")


def check_rete():
    url = "https://webgui-3a.tpl.intranet.fw/?msisdn=393756104999&imsi="
    logging.info("Url generato: " + url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers, verify=False)
    logging.info(response.content)

    if response.status_code == 200:
        print("ok")
    if response.status_code != 200:
        logging.error("Status code diverso da 200")


def check_catena():
    if catena.get() not in ['3A', '3C']:
        messagebox.showinfo("Catenza non valorizzata",
                            "Non è stata inserita la catena sulla quale eseguire la pulizia")
        print("Pulizia NON avviata")
        return -1
    return 0


def recovery_usim():
    messagebox.showinfo("Avvio recupero USIM",
                        "La procedura di recupero USIM è stata avviata, assicurati che il file "
                        "USIM_IN_ERRORE_RETE.csv sia valorizzato")
    clean = Pulizia(catena=catena.get())
    clean.pulizia_usim_su_rete(recovery=True)
    messagebox.showinfo("Avviso pulizia USIM",
                        "La pulizia è stata completata")


def sdno_preattivazione_full():
    response = messagebox.askquestion("Avvia preattivazione SDNO",
                                      "Sei sicuro di avviare la preattivazione su SDNO? Assicurati di aver aperto il tunnel SSH e avviato il CRT su BHLINAPP")
    if response == 'yes':
        if check_catena() == 0:
            con = db_connection.DB_Connection(catena.get()).sdno_connection()
            cat = catena.get()
            # Configura la connessione in base alla catena
            if cat == '3A':
                host = 'localhost:8089'
            elif cat == '3C':
                host = 'localhost:8090'
            else:
                raise ValueError("Catena non valida")
    sdno = SDNO(catena=catena.get(), con=con, host=host)
    sdno.SDNO_preattivazione_full(lot_tree=lot_tree, catena=cat)


def recupero_preattivazione():
    '''
    Recupera le sim da preattivare, non è la preattivazione completa ma solo una parte
    :return:
    '''
    response = messagebox.askquestion("Avvia recupero preattivazione SDNO",
                                      "Sei sicuro di avviare la pulizia sui sistemi RETE? Assicurati di aver aperto il tunnel SSH e avviato il CRT su BHLINAPP")
    if response == 'yes':
        if check_catena() == 0:
            con = db_connection.DB_Connection(catena.get()).sdno_connection()

            # Configura la connessione in base alla catena
            if catena.get() == '3A':
                host = 'localhost:8089'
            elif catena.get() == '3C':
                host = 'localhost:8090'
            else:
                raise ValueError("Catena non valida")
            sdno = SDNO(catena=catena.get(), con=con, host=host)
            sdno.SDNO_recupero_preattivazione(lot_tree=lot_tree)


# Creazione dell'interfaccia
root = tk.Tk()
root.title("Gestione Lotti USIM")
root.iconbitmap("USIM.ico")
root.geometry("1600x500")

with open("output.csv", mode='w', newline='') as file:
    file.write('')  # Scrivi una stringa vuota nel file
with open("output_sdno.csv", mode='w', newline='') as file:
    file.write('')  # Scrivi una stringa vuota nel file

style = ThemedStyle(root)
style.set_theme("breeze")

# Creazione del frame contenitore
container_frame = ttk.Frame(root)
container_frame.pack(side="left", fill="y", padx=20, pady=20)

# Creazione dei campi in input
input_frame = ttk.Frame(container_frame, padding=10)
input_frame.pack(side="left", fill="y", padx=20, pady=20)

ttk.Label(input_frame, text="MSISDN Start:").grid(row=0, column=0, padx=5, pady=5)
first_num_entry = ttk.Entry(input_frame)
first_num_entry.insert(0, '0')  # Inserisci il valore di default
first_num_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="MSISDN End:").grid(row=1, column=0, padx=5, pady=5)
last_num_entry = ttk.Entry(input_frame)
last_num_entry.insert(0, '0')  # Inserisci il valore di default
last_num_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="IMSI Start:").grid(row=2, column=0, padx=5, pady=5)
additional_info_entry = ttk.Entry(input_frame)
additional_info_entry.insert(0, '0')  # Inserisci il valore di default
additional_info_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="IMSI End:").grid(row=3, column=0, padx=5, pady=5)
another_field_entry = ttk.Entry(input_frame)
another_field_entry.insert(0, '0')  # Inserisci il valore di default
another_field_entry.grid(row=3, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Descrizione:").grid(row=4, column=0, padx=5, pady=5)
descrizione_field_entry = ttk.Entry(input_frame)
descrizione_field_entry.insert(0, '')  # Inserisci il valore di default
descrizione_field_entry.grid(row=4, column=1, padx=5, pady=5)

add_button = ttk.Button(input_frame, text="Aggiungi Lotto", command=add_lot)
add_button.grid(row=5, columnspan=2, pady=10)

delete_button = ttk.Button(input_frame, text="Elimina Lotto", command=delete_lot)
delete_button.grid(row=6, columnspan=2, pady=5)

recovery_button = ttk.Button(input_frame, text="Recupera SIM su RETE*", command=recovery_usim)
recovery_button.grid(row=7, columnspan=2, pady=5)

# Creazione della label sotto i bottoni
label_below_buttons = ttk.Label(input_frame, text="* Recupera le SIM presenti in 'USIM_IN_ERRORE_RETE.csv'")
label_below_buttons.configure(font=("Arial", 8), padding=(10, 5))
label_below_buttons.grid(row=8, columnspan=2, pady=5)

# Creazione del riquadro per i radio button
radio_frame = ttk.Frame(container_frame, padding=10)
radio_frame.pack(side="left", fill="y", padx=20, pady=20)

catena = tk.StringVar()

radio_3A = ttk.Radiobutton(radio_frame, text="3A", variable=catena, value="3A")
radio_3A.grid(row=7, column=0, padx=5, pady=5)

radio_3C = ttk.Radiobutton(radio_frame, text="3C", variable=catena, value="3C")
radio_3C.grid(row=7, column=1, padx=5, pady=5)

# Creazione dei checkbox
operazione1_checkbox = ttk.Checkbutton(radio_frame, text="RETE")
operazione1_checkbox.grid(row=8, column=0, padx=5, pady=5)

operazione2_checkbox = ttk.Checkbutton(radio_frame, text="NETDB")
operazione2_checkbox.grid(row=8, column=1, padx=5, pady=5)

operazione3_checkbox = ttk.Checkbutton(radio_frame, text="MRM", state="disabled")
operazione3_checkbox.grid(row=9, column=0, padx=5, pady=5)

operazione4_checkbox = ttk.Checkbutton(radio_frame, text="  OCS  ", state="disabled")
operazione4_checkbox.grid(row=9, column=1, padx=5, pady=5)

start_cleanup_button = ttk.Button(radio_frame, text="Avvia pulizia", command=start_cleanup)
start_cleanup_button.grid(row=11, columnspan=2, pady=5)

start_cleanup_button = ttk.Button(radio_frame, text="Check rete", command=check_rete)
start_cleanup_button.grid(row=12, columnspan=2, pady=5)

start_cleanup_button = ttk.Button(radio_frame, text="Recupero SDNO->RETE", command=recupero_preattivazione)
start_cleanup_button.grid(row=13, columnspan=2, pady=5)

start_cleanup_button = ttk.Button(radio_frame, text="Preattivazione SDNO->RETE", command=sdno_preattivazione_full)
start_cleanup_button.grid(row=14, columnspan=2, pady=5)
# Barra di avanzamento

# Etichetta sopra la barra di avanzamento
progress_label = ttk.Label(root, text="Avanzamento Pulizia")
progress_label.pack(side="bottom", padx=5, pady=(10, 0))
progress_bar = ttk.Progressbar(root, mode="determinate", maximum=100, value=0, length=800)
progress_bar.pack(side="bottom", fill="x", padx=10, pady=10)
progress_bar['value'] = 50

'''# Creazione della barra di avanzamento
progressbar_var = tk.IntVar()
progressbar = ttk.Progressbar(root, mode='determinate', variable=progressbar_var)
progressbar.grid(row=7, column=1, columnspan=2, padx=20, pady=20)
progressbar.grid_remove()  # Nascondi la barra di avanzamento inizialmente'''

# Creazione della tabella per i lotti
lot_tree = ttk.Treeview(root,
                        columns=("MSISDN Start", "MSISDN End", "IMSI Start", "IMSI End", "Rete", "Netdb", "MRM"),
                        show="headings")
lot_tree.heading("#1", text="MSISDN Start")
lot_tree.column("#1", width=150)
lot_tree.heading("#2", text="MSISDN End")
lot_tree.column("#2", width=150)
lot_tree.heading("#3", text="IMSI Start")
lot_tree.column("#3", width=150)
lot_tree.heading("#4", text="IMSI End")
lot_tree.column("#4", width=150)
lot_tree.heading("#5", text="Rete")
lot_tree.column("#5", width=50)
lot_tree.heading("#6", text="Netdb")
lot_tree.column("#6", width=50)
lot_tree.heading("#7", text="Descrizione")
lot_tree.column("#7", width=100)
lot_tree.pack(side="right", fill="both", expand=True, padx=20, pady=20)

root.mainloop()
