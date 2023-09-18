import pandas as pd
import numpy as np
import requests
import warnings
import logging
import csv


class Pulizia:
    def __init__(self, catena):
        self.catena = catena

    def configurazioni_rete(self):
        host = 'localhost:5000'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Host': 'webgui.tpl.intranet.fw'}
        return host, headers

    def pulizia_usim_su_rete(self):
        sim_pulite = 0
        list_sim_error = []

        warnings.filterwarnings("ignore")
        logging.basicConfig(filename='pulizia_usim_rete.log', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Apri il file CSV iniziale in modalità lettura
        # Apri il file CSV iniziale in modalità lettura
        with open('output.csv', 'r', newline='') as input_file:
            # Leggi il file CSV iniziale
            reader = csv.reader(input_file, delimiter=';')

            # Crea una lista per contenere gli elementi della seconda colonna
            second_column_items = []

            # Crea una lista per contenere gli elementi della prima colonna
            first_column_items = []

            # Scansiona le righe del file CSV iniziale
            for row in reader:
                if len(row) >= 2:
                    # Aggiungi l'elemento della seconda colonna alla lista
                    second_column_items.append(row[1]+";")

                    # Aggiungi l'elemento della prima colonna alla lista
                    first_column_items.append(row[0]+";")

        # Apri il file CSV di destinazione in modalità scrittura
        with open('USIM_RETE.csv', 'w', newline='') as output_file:
            # Scrivi gli elementi delle due colonne nel nuovo CSV
            writer = csv.writer(output_file)

            for first, second in zip(first_column_items, second_column_items):
                writer.writerow([first])
                writer.writerow([second])

        host, headers = self.configurazioni_rete()
        usim = list(np.array(pd.read_csv("USIM_RETE.csv", header=None)))

        # Cicla finché l'array usim non si svuota
        while usim:
            dn = usim.pop(0)[0].replace(";", "")
            if dn[0] == '2':
                url = "https://" + host + "/api/deleteUSIM?imsi=" + dn
                logging.info("Url generato: " + url)
            else:
                url = "https://" + host + "/api/deleteUSIM?msisdn=" + dn + "&imsi="
                logging.info("Url generato: " + url)

            response = requests.get(url, headers=headers, verify=False)
            logging.info(response.content)
            if response.status_code == 200:
                sim_pulite+=1
            if response.status_code != 200:
                logging.error("Status code diverso da 200, salvo la SIM " + dn + " e riprovo più tardi")
                usim.append(dn)  # Aggiungi il DN nuovamente all'array per riprovarlo successivamente
                list_sim_error.append(dn)

        return sim_pulite
