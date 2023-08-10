import csv
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def add_lot():
    msisdn_start = first_num_entry.get()
    msisdn_end = last_num_entry.get()
    imsi_start = additional_info_entry.get()
    imsi_end = another_field_entry.get()
    if msisdn_start and msisdn_end and imsi_start and imsi_end:
        usim_tot = calcola_totale_lotto(msisdn_start,msisdn_end, imsi_start, imsi_end)
        usim_tot = str(usim_tot)
        if int(usim_tot) <= 0:
            messagebox.showinfo("Quantità MSISDN/IMSI non conforme", "Il numero di MSISDN inseriti non è pari al numero di IMSI")

        lot_tree.insert("", "end", values=(msisdn_start, msisdn_end, imsi_start, imsi_end,usim_tot,usim_tot,usim_tot,usim_tot))
        first_num_entry.delete(0, tk.END)
        last_num_entry.delete(0, tk.END)
        additional_info_entry.delete(0, tk.END)
        another_field_entry.delete(0, tk.END)

def calcola_totale_lotto(msisdn_start,msisdn_end, imsi_start, imsi_end):
    filename = "output.csv"
    rows = []

    if msisdn_start is not None and msisdn_end is not None:
        for msisdn, imsi in zip(range(int(msisdn_start), int(msisdn_end) + 1), range(int(imsi_start), int(imsi_end) + 1)):
            rows.append((str(msisdn), str(imsi)))
    elif imsi_start is not None and imsi_end is not None:
        for imsi in range(int(imsi_start), int(imsi_end) + 1):
            rows.append((";", str(imsi)))

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(rows)

    print(f"CSV file '{filename}' created successfully.")
    return len(rows)

def delete_lot():
    selected_item = lot_tree.selection()
    if selected_item:
        lot_tree.delete(selected_item)

def start_cleanup():
    response = messagebox.askquestion("Avvia pulizia", "Sei sicuro di avviare la pulizia sui sistemi RETE?")
    if response == 'yes':
        print("Pulizia avviata")
        print("Dati in tabella:")
        for item in lot_tree.get_children():
            values = lot_tree.item(item, "values")
            if values:
                print("Primo Numero:", values[0], "Ultimo Numero:", values[1], "Informazione Aggiuntiva:", values[2], "Altro Campo:", values[3])
    else:
        print("Pulizia NON avviata")

# Creazione dell'interfaccia
root = tk.Tk()
root.title("Gestione Lotti USIM")
root.geometry("1200x500")
root.configure(bg="#1e1e1e")

# Creazione dei campi in input
input_frame = ttk.Frame(root, padding=10)
input_frame.configure(style="Dark.TFrame")
input_frame.pack(side="left", fill="y", padx=20, pady=20)

ttk.Label(input_frame, text="MSISDN Start:").grid(row=0, column=0, padx=5, pady=5)
first_num_entry = ttk.Entry(input_frame)
first_num_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="MSISDN End:").grid(row=1, column=0, padx=5, pady=5)
last_num_entry = ttk.Entry(input_frame)
last_num_entry.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="IMSI Start:").grid(row=2, column=0, padx=5, pady=5)
additional_info_entry = ttk.Entry(input_frame)
additional_info_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="IMSI End:").grid(row=3, column=0, padx=5, pady=5)
another_field_entry = ttk.Entry(input_frame)
another_field_entry.grid(row=3, column=1, padx=5, pady=5)

add_button = ttk.Button(input_frame, text="Aggiungi Lotto", command=add_lot)
add_button.grid(row=4, columnspan=2, pady=10)

delete_button = ttk.Button(input_frame, text="Elimina Lotto", command=delete_lot)
delete_button.grid(row=5, columnspan=2, pady=5)

start_cleanup_button = ttk.Button(input_frame, text="Avvia pulizia", command=start_cleanup)
start_cleanup_button.grid(row=6, columnspan=2, pady=5)

# Barra di avanzamento

# Etichetta sopra la barra di avanzamento
progress_label = ttk.Label(root, text="Avanzamento Pulizia")
progress_label.pack(side="bottom", padx=5, pady=(10, 0))
progress_bar = ttk.Progressbar(root, mode="determinate", maximum=100, value=0, length=800)
progress_bar.pack(side="bottom", fill="x", padx=10, pady=10)
progress_bar['value'] = 50
# Creazione della tabella per i lotti
lot_tree = ttk.Treeview(root, columns=("MSISDN Start", "MSISDN End", "IMSI Start", "IMSI End","Rete", "Netdb", "MRM", "OCS"), show="headings")
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
lot_tree.heading("#7", text="MRM")
lot_tree.column("#7", width=50)
lot_tree.heading("#8", text="OCS")
lot_tree.column("#8", width=50)
lot_tree.pack(side="right", fill="both", expand=True, padx=20, pady=20)

# Applicazione del tema dark ai widget
style = ttk.Style()
style.theme_use("clam")
style.configure("Dark.TFrame", background="#1e1e1e")

root.mainloop()
