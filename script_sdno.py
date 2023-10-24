import csv
import warnings
from time import sleep
from tkinter import messagebox
import csv
import logging
import cx_Oracle
import requests
import db_connection


class SDNO:
    def __init__(self, catena):
        self.catena = catena
        self.db_conn = db_connection.DB_Connection(self.catena)

    def SDNO_recupero_preattivazione(self, lot_tree):
        con = self.db_conn.sdno_connection()

        # Configura la connessione in base alla catena
        if self.catena == '3A':
            host = 'localhost:8089'
        elif self.catena == '3C':
            host = 'localhost:8090'
        else:
            raise ValueError("Catena non valida")

        with open('output_sdno.csv', 'r', newline='') as input_file:
            reader = csv.reader(input_file, delimiter=';')
            for row in reader:
                imsi_start = row[0]
                imsi_end = row[1]
                totale = int(imsi_end)-int(imsi_start) + 1
                # STEP 1
                self.execute_query(con,
                                   f"UPDATE OSO_MOBILE_BROADBAND_USIM SET STATUS = 'SCHEDULED', PHASE = 'DCCORE' WHERE "
                                   f"IMSI BETWEEN '{imsi_start}' AND '{imsi_end}'")

                # STEP 2
                self.exe_workflow(url=f"http://{host}/sa/sa/startAndWaitForJob",
                                  workflow='OSS_OSO_DCCORE_Preprovisioning')
                sleep(5)

                # STEP 3 & 4: Attendi fino a STATUS = DONE
                if self.check_error_from_rete(con=con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
                    # se abbiamo un errore da rete termino
                    break
                else:
                    count = 0
                    while count != totale:
                        res = self.execute_query(con,
                                                 f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'DONE'")
                        if len(res)>0:
                            count = res[0][0]

                        sleep(5)

                    # STEP 5
                    self.exe_workflow(url=f"http://{host}/sa/sa/startAndWaitForJob",
                                      workflow='OSS_OSO_Update_States')
                    sleep(3)

                    # STEP 6 & 7
                    if self.check_error_from_rete(con=con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
                        # se abbiamo un errore da rete termino
                        break
                    count = 0
                    while count != totale:
                        res = self.execute_query(con,
                                                 f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'SCHEDULED' AND PHASE = 'DCVOICE'")
                        if len(res) > 0:
                            count = res[0][0]
                        sleep(5)

                    self.exe_workflow(url=f"http://{host}/sa/sa/startAndWaitForJob",
                                      workflow='OSS_OSO_DCVOICE_Preprovisioning')

                    # STEP 8 & 9: Attendi fino a STATUS = DONE e PHASE = DCVOICE
                    if self.check_error_from_rete(con=con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
                        # se abbiamo un errore da rete termino
                        break
                    count = 0
                    while count != totale:
                        res = self.execute_query(con,
                                                 f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'DONE' AND PHASE = 'DCVOICE'")
                        if len(res) > 0:
                            count = res[0][0]
                        sleep(5)

                    # Ultimo STEP: Aggiorna a STATUS = COMPLETED e PHASE = MRM_CS
                    self.execute_query(con,
                                       f"UPDATE OSO_MOBILE_BROADBAND_USIM SET STATUS = 'COMPLETED', PHASE = 'MRM_CS' WHERE "
                                       f"IMSI BETWEEN '{imsi_start}' AND '{imsi_end}'")


    def check_error_from_rete(self, con, imsi_start, imsi_end):
        res = self.execute_query(con,
                                 f"SELECT STATUS, PHASE, RESULTDESC FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'ERROR'")
        if len(res) > 0:
            if res[0][0] == 'ERROR':
                logging.error("Errore: " + res[0][2])
                messagebox.showinfo("Errore di chiamata",
                                    "Il flusso è stato interrotto, riscontrato il seguente errore : " + res[0][2])
                return -1

        return 0



    def execute_query(self, con, query):

        try:
            cur = con.cursor()

            # fetchall() is used to fetch all records from result set
            cur.execute(query)
            if query[:6].upper() == 'SELECT':
                rows = cur.fetchall()
            if query[:6].upper() == 'UPDATE':
                con.commit()
                rows = 0
            return rows
        except cx_Oracle.DatabaseError as er:
            print('There is an error in the Oracle database:', er)

        except Exception as er:
            print('Error:' + str(er))

        finally:
            if cur:
                cur.close()

    def exe_workflow(self, url, workflow):
        if workflow not in ('OSS_OSO_DCCORE_Preprovisioning',
                            'OSS_OSO_Update_States',
                            'OSS_OSO_DCVOICE_Preprovisioning',
                            'OOG_MIG_NPNNG_MANUAL_ACTION_DEFAULT_KO_CREATOR'):
            print('>>>>> IL WORKFLOW ' + workflow + ' NON E CORRETTO <<<<<<')
        else:
            payload = {
                "workflowName": workflow,
            }
            headers = {'Authorization': 'Basic c2E6c2E=', 'Content-type': 'application/json;charset=UTF-8',
                       'Accept': 'application/json'}
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # print(response.json())
                print("Il workflow " + workflow + " è stato eseguito correttamente")
            else:
                print("Request failed with status code:", response.status_code)
