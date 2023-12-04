import csv
import warnings
from time import sleep
from tkinter import messagebox
import csv
import logging
import cx_Oracle
import requests
import db_connection
from db_automation import DB_Automation


class SDNO:
    def __init__(self, catena, host, con):
        self.catena = catena
        self.db_conn = db_connection.DB_Connection(self.catena)
        self.host = host
        self.con = con
        self.db_automation = DB_Automation()

    def step_3_preattivazione(self, imsi_start, imsi_end, totale):
        # STEP 1: Esecuzione WF OSS_Oso_update_states
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_Update_States')
        sleep(3)

        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 2: Verifica status = SCHEDULED, PHASE = NETDB
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'SCHEDULED', 'NETDB_NEW', totale)

        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_NETDB_SUBMITNEW')
        sleep(3)

        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 4: Verifica status = DONE, PHASE = NETDB
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'DONE', 'NETDB_NEW', totale)

        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_Update_States')
        sleep(3)

        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 6: Verifica status = SCHEDULED, PHASE = MRM_CS
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'SCHEDULED', 'MRM_CS', totale)
        # STEP 7: Esecuzione wf OSS_OSO_MRM_ChangeStatus
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_MRM_ChangeStatus')
        sleep(3)

        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 8: Verifica status = DONE, PHASE = MRM_CS
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'DONE', 'MRM_CS', totale)

        # STEP 9: Esecuzione WF OSS_Oso_update_states
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_Update_States')
        sleep(3)
        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 10: Verifica status = COMPLETED, PHASE = MRM_CS
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'COMPLETED', 'MRM_CS', totale)
        # LOGGA A DB CHE LA SIM E PREATTIVA

    def step_2_preattivazione(self, imsi_start, imsi_end, totale, parziale):
        # STEP 1
        self.execute_query(self.con,
                           f"UPDATE OSO_MOBILE_BROADBAND_USIM SET STATUS = 'SCHEDULED', PHASE = 'DCCORE' WHERE "
                           f"IMSI BETWEEN '{imsi_start}' AND '{imsi_end}'")

        # STEP 2
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob",
                          workflow='OSS_OSO_DCCORE_Preprovisioning')
        sleep(5)

        # STEP 3 & 4: Attendi fino a STATUS = DONE
        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            count = 0
            while count != totale:
                res = self.execute_query(self.con,
                                         f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'DONE' AND PHASE ='DCCORE'")
                if len(res) > 0:
                    count = res[0][0]

                sleep(5)

            # STEP 5
            self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob",
                              workflow='OSS_OSO_Update_States')
            sleep(3)

            # STEP 6 & 7
            if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
                # se abbiamo un errore da rete termino
                return -1
            count = 0
            while count != totale:
                res = self.execute_query(self.con,
                                         f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'SCHEDULED' AND PHASE = 'DCVOICE'")
                if len(res) > 0:
                    count = res[0][0]
                sleep(5)

            self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob",
                              workflow='OSS_OSO_DCVOICE_Preprovisioning')

            # STEP 8 & 9: Attendi fino a STATUS = DONE e PHASE = DCVOICE
            if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
                # se abbiamo un errore da rete termino
                return -1
            count = 0
            while count != totale:
                res = self.execute_query(self.con,
                                         f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = 'DONE' AND PHASE = 'DCVOICE'")
                if len(res) > 0:
                    count = res[0][0]
                sleep(5)

            if parziale == 'SI':
                # Ultimo STEP: Aggiorna a STATUS = COMPLETED e PHASE = MRM_CS
                self.execute_query(self.con,
                                   f"UPDATE OSO_MOBILE_BROADBAND_USIM SET STATUS = 'COMPLETED', PHASE = 'MRM_CS' WHERE "
                                   f"IMSI BETWEEN '{imsi_start}' AND '{imsi_end}'")
            return 0

    def step_1_preattivazione(self, imsi_start, imsi_end, totale):
        # STEP 1: Esecuzione WF OSS_Oso_update_states
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_Update_States')
        sleep(3)
        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 2: Verifica status = SCHEDULED, PHASE = MRM_UI
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'SCHEDULED', 'MRM_UI', totale)

        # STEP 3: Esecuzione del WF OSS_OSO_MRM_UsimIngestion
        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_MRM_UsimIngestion')

        if self.check_error_from_rete(con=self.con, imsi_start=imsi_start, imsi_end=imsi_end) == - 1:
            # se abbiamo un errore da rete termino
            return -1
        else:
            # STEP 4: Verifica status = DONE, PHASE = MRM_UI
            self.wait_for_status_phase(self.con, imsi_start, imsi_end, 'DONE', 'MRM_UI', totale)

        self.exe_workflow(url=f"http://{self.host}/sa/sa/startAndWaitForJob", workflow='OSS_OSO_Update_States')
        sleep(3)

    def SDNO_preattivazione_full(self, lot_tree, catena):

        with open('output_sdno.csv', 'r', newline='') as input_file:
            reader = csv.reader(input_file, delimiter=';')
            for row in reader:
                imsi_start = row[0]
                imsi_end = row[1]
                descrizione = row[2]
                totale = int(imsi_end) - int(imsi_start) + 1

                res = self.step_1_preattivazione(imsi_start=imsi_start, imsi_end=imsi_end, totale=totale)
                self.db_automation.insert_into_db_sim(sistema='SDNO',msisdn=imsi_start,imsi=imsi_end,stato='IN PREATTIVAZIONE-Step 1',descrizione=descrizione, catena=catena)
                if res == 0:

                    res = self.step_2_preattivazione(imsi_start=imsi_start, imsi_end=imsi_end, totale=totale,
                                                     parziale='NO')
                    self.db_automation.insert_into_db_sim(sistema='SDNO', msisdn=imsi_start, imsi=imsi_end,
                                                          stato='IN PREATTIVAZIONE-Step 2',
                                                          descrizione=descrizione,catena=catena)

                    if res == 0:
                        self.step_3_preattivazione(imsi_start=imsi_start, imsi_end=imsi_end, totale=totale)
                        self.db_automation.insert_into_db_sim(sistema='SDNO', msisdn=imsi_start, imsi=imsi_end,
                                                              stato='PREATTIVA',
                                                              descrizione=descrizione,catena=catena)
    # Metodi di supporto
    def wait_for_status_phase(self, con, imsi_start, imsi_end, status, phase, totale):
        count = 0
        while count != totale:
            res = self.execute_query(con,
                                     f"SELECT count(*) FROM OSO_MOBILE_BROADBAND_USIM WHERE IMSI BETWEEN '{imsi_start}' AND '{imsi_end}' AND STATUS = '{status}' AND PHASE = '{phase}'")
            if len(res) > 0:
                count = res[0][0]
            sleep(5)

    def SDNO_recupero_preattivazione(self, lot_tree):
        with open('output_sdno.csv', 'r', newline='') as input_file:
            reader = csv.reader(input_file, delimiter=';')
            for row in reader:
                imsi_start = row[0]
                imsi_end = row[1]
                totale = int(imsi_end) - int(imsi_start) + 1

                res = self.step_2_preattivazione(imsi_start=imsi_start, imsi_end=imsi_end, totale=totale,
                                                 parziale='SI')

        return res

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
