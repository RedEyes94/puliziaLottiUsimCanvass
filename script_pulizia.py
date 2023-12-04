from tkinter import messagebox

import pandas as pd
import numpy as np
import requests
import warnings
import logging
import csv

from db_automation import DB_Automation


class Pulizia:
    def __init__(self, catena):
        self.catena = catena
        self.db_automation = DB_Automation()

    def configurazioni_rete(self):
        host = 'localhost:5000'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Host': 'webgui.tpl.intranet.fw'}
        return host, headers

    def pulizia_netdb(self, catena):
        import datetime

        # Nome del file CTL di input
        input_ctl_file = 'File_pulizia_NETDB/16_Load_TEMP_IMSI_MSISDN_CATENA.ctl'

        # Nome del file CSV di input
        input_csv_file = 'output.csv'

        '''
        Sostituisco lo 0
        '''
        # Leggi il contenuto del file CSV
        with open(input_csv_file, 'r') as csv_file:
            csv_read = csv_file.read()
        # Sostituisci il carattere ";" con un altro carattere o una stringa vuota, a seconda delle tue esigenze
        # Supponiamo di voler sostituire ";" con ","
        csv_read = csv_read.replace('";"', '0')
        # Sovrascrivi il file CSV con il contenuto modificato
        with open(input_csv_file, 'w') as csv_file:
            csv_file.write(csv_read)

        '''
        Leggo il csv pulito
        '''
        # Leggi il contenuto del file CSV
        with open(input_csv_file, 'r') as csv_file:
            csv_lines = csv_file.readlines()
        # Rimuovi eventuali spazi bianchi in eccesso dalle righe CSV
        csv_lines = [line.strip() for line in csv_lines]

        # Formatta le righe CSV nel formato richiesto
        formatted_lines = [f'"{line.split(";")[0]}";"{line.split(";")[1]}"' for line in csv_lines]

        # Formatta la data corrente nel formato "GG-MM-YYYY"
        current_date = datetime.datetime.now().strftime('%d-%m-%Y')

        # Crea il nome del nuovo file CTL con la data corrente
        new_ctl_file_name = f'16_Load_TEMP_IMSI_MSISDN_{self.catena}.ctl'

        # Copia il contenuto del file CTL di input nel nuovo file
        with open(input_ctl_file, 'r') as original_ctl_file:
            original_content = original_ctl_file.read()
            # Sostituisci "CATENA" con il valore desiderato (self.catena)
            original_content = original_content.replace('CATENA', self.catena)

            with open(new_ctl_file_name, 'w') as new_ctl_file:
                new_ctl_file.write(original_content)

        # Apri il nuovo file CTL in modalità append e aggiungi le righe formattate una sotto l'altra
        with open(new_ctl_file_name, 'a') as ctl_file:
            formatted_lines = [line.replace('"0"', '""') for line in formatted_lines]
            ctl_file.write('\n'.join(formatted_lines) + '\n')

        print(f'Le righe dal file CSV sono state accodate una sotto l\'altro nel nuovo file CTL: {new_ctl_file_name}')

    def pulizia_usim_su_rete(self, recovery,catena):
        sim_pulite = 0
        list_sim_error = []
        only_imsi = False
        termina_pulizia = False

        warnings.filterwarnings("ignore")
        logging.basicConfig(filename='pulizia_usim_rete.log', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        if not recovery:
            # Apri il file CSV iniziale in modalità lettura
            # Apri il file CSV iniziale in modalità lettura
            with open('output.csv', 'r', newline='') as input_file:
                # Leggi il file CSV iniziale
                reader = csv.reader(input_file, delimiter=';')

                # Crea una lista per contenere gli elementi della seconda colonna
                second_column_items = []

                # Crea una lista per contenere gli elementi della prima colonna
                first_column_items = []

                third_column_items = []
                # Scansiona le righe del file CSV iniziale
                for row in reader:
                    if len(row) >= 2:
                        # Aggiungi l'elemento della seconda colonna alla lista
                        second_column_items.append(row[1] + ";")

                        # Aggiungi l'elemento della prima colonna alla lista
                        first_column_items.append(row[0] + ";")
                        try:
                            third_column_items.append(row[2] + ";")
                            if row[0] == ';':
                                only_imsi = True
                        except IndexError:
                            print("Indice 2 non presente nella riga, salto la riga")
                            only_imsi = True
                            continue

            # Apri il file CSV di destinazione in modalità scrittura
            with open('USIM_RETE.csv', 'w', newline='') as output_file:
                # Scrivi gli elementi delle due colonne nel nuovo CSV
                writer = csv.writer(output_file)

                if only_imsi:
                    for second, third in zip(second_column_items, third_column_items):
                        writer.writerow([second,third])

                else:
                    for first, second, third in zip(first_column_items, second_column_items, third_column_items):
                        writer.writerow([first,third])
                        writer.writerow([second,third])
            usim = list(np.array(pd.read_csv("USIM_RETE.csv", header=None)))
        elif recovery:
            # se devo fare il recovery leggo direttamente il file di USIM in errore
            usim = list(np.array(pd.read_csv("USIM_IN_ERRORE_RETE.csv", header=None)))

        host, headers = self.configurazioni_rete()

        # Cicla finché l'array usim non si svuota oppure se l'utente decide di terminare l'esecuzione dopo aver
        # avuto diversi KO da rete
        totale = len(usim)
        count = 0
        msisdn = '0'
        imsi = '0'
        while usim:
            count=count+1
            descrizione = usim[0][1].replace(";", "")
            dn = str(usim.pop(0)[0]).replace(";", "")

            if dn != '':
                if dn[0] == '2':
                    url = "https://" + host + "/api/deleteUSIM?imsi=" + dn
                    logging.info("Url generato: " + url)
                    imsi = dn
                else:
                    url = "https://" + host + "/api/deleteUSIM?msisdn=" + dn + "&imsi="
                    logging.info("Url generato: " + url)
                    msisdn = dn

                response = requests.get(url, headers=headers, verify=False)
                '''
                Loggo su DB AUTOMATION
                CREATE TABLE LOG_USIM_CANVAS (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    SISTEMA VARCHAR(50),
                    MSISDN VARCHAR(50),
                    IMSI VARCHAR(50),
                    STATO, VARCHAR(50), --> pulita/preattivata
                    DESCRIZIONE VARCHAR(200),
                    URL VARCHAR(200),
                    ESITO VARCHAR(250), --> esito del web service
                    ERRORE VARCHAR(250),
                    DATA_ESECUZIONE VARCHAR(50)
                );
                DA COMPLETARE LA DESCRIZIONE CHE VA INSERITA PER OGNI RIGA NEL FILE USIM_RETE.CSV COSI LA RIUTILIZZO QUI
                
                '''
                self.db_automation.insert_into_db_log(sistema='RETE', msisdn=msisdn, catena=catena,imsi=imsi, url=url, esito=str(response.status_code), stato='PULITA', descrizione=descrizione, response=response.content)
                logging.info(response.content)
                if count % 2 == 0:
                    self.db_automation.insert_into_db_sim(sistema='RETE', msisdn=msisdn, catena=catena,imsi=imsi, stato='PULITA', descrizione=descrizione)
                    msisdn = '0'
                    imsi = '0'

                if response.status_code == 200:
                    sim_pulite += 1
                if response.status_code != 200:
                    logging.error("Status code diverso da 200, errore :" + str(
                        response.status_code) + ". Salvo la SIM " + dn + " e riprovo più tardi")
                    usim.append(dn)  # Aggiungi il DN nuovamente all'array per riprovarlo successivamente
                    list_sim_error.append(dn)
                    if len(list_sim_error) > 10:
                        response = messagebox.askquestion("Errori di raggiungibilità verso RETE",
                                                          "Rete non sta rispondendo correttamente impedendo la cancellazione di alcune USIM. Vuoi interrompere la pulizia?")
                        if response == "yes":
                            logging.info(">>>>>>>>   PULIZIA INTERROTTA DALL'UTENTE    <<<<<<<<<<<<")
                            termina_pulizia = True  # mi fa uscire dal loop e termina la pulizia verso rete
                            # Apri il file CSV in modalità scrittura

                            with open('USIM_IN_ERRORE_RETE.csv', mode='w', newline='') as csv_file:
                                # Crea un writer CSV con il separatore personalizzato ';'
                                csv_writer = csv.writer(csv_file, delimiter=';')
                                # Scrivi i dati dalla lista nel file CSV
                                csv_writer.writerow(list_sim_error)
            logging.info("------------------------------------------------------- ")
            logging.info("----------------  Avanzamento pulizia  ---------------- ")
            logging.info("---------------- " + str(100 - len(usim) / totale * 100) + " % ----------------")
            logging.info("------------------------------------------------------- ")

        return sim_pulite
