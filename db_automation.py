from datetime import datetime

import cx_Oracle
import mysql.connector
import configparser


class DB_Automation:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.properties')
        self.AUTOMATION_PSW = config['SERVER_DB']['AUTOMATION_PSW']
        self.AUTOMATION_HOST = config['SERVER_DB']['AUTOMATION_HOST']

    def connect_to_automation_db(self):

        connection = mysql.connector.connect(
            host=self.AUTOMATION_HOST,
            port=3310,
            user="testautom",
            password=self.AUTOMATION_PSW,
            database="tstauto"
        )

        try:
            # Crea una connessione al database
            connection = mysql.connector.connect(
                host=self.AUTOMATION_HOST,
                port=3310,
                user="testautom",
                password=self.AUTOMATION_PSW,
                database="tstauto"
            )
            cursor = connection.cursor()

        except mysql.connector.Error as err:
            print(f"Errore MySQL: {err}")
            print(f"Istruzione SQL: {cursor.statement}")

        return cursor, connection

    def insert_into_db_log(self, sistema, msisdn, imsi, url, esito,stato, descrizione, response, catena):
        try:
            cursor, connection = self.connect_to_automation_db()

            # Assicurati che response sia una stringa, se è in formato binario, decodificalo
            if isinstance(response, bytes):
                response = response.decode('utf-8')

            query = """
                   INSERT INTO LOG_USIM_CANVAS 
                   (SISTEMA, MSISDN, IMSI, STATO, URL, DESCRIZIONE,CATENA, ESITO, ERRORE, DATA_ESECUZIONE, RESPONSE) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '-', %s, %s)
               """

            cursor.execute(query, (sistema, msisdn, imsi, stato, url, descrizione,catena, esito, datetime.now(), response))

            id = cursor.lastrowid
            connection.commit()
            print(cursor.rowcount, "Record inserted successfully")

        except mysql.connector.Error as e:
            print("Error occurred:", e)
        finally:
            if cursor is not None:
                cursor.close()

        return id

    def insert_into_db_sim(self, sistema, msisdn, imsi,stato, descrizione, catena):
        cursor, connection = self.connect_to_automation_db()
        cursor.execute(
            "INSERT INTO USIM_CANVASS (SISTEMA, MSISDN, IMSI, STATO, DESCRIZIONE, CATENA, DATA_INSERIMENTO) "
            "VALUES ('" + sistema + "', '" + msisdn + "', '" + imsi + "', '" + stato + "','" + descrizione + "', '"+catena+"', "
                                                                                                            "'" + str(
                datetime.now()) + "')")
        id = cursor.lastrowid
        connection.commit()
        print(cursor.rowcount, "Record inserted successfully")
        cursor.close()
        return id

    def update_into_db_log(self, id, response,errore):
        cursor, connection = self.connect_to_automation_db()
        cursor.execute(
            "UPDATE LOG_USIM_CANVAS SET ESITO = '"+response+"', ERRORE = '" + errore + "' WHERE ID = " + str(
                id))
        connection.commit()
        print(cursor.rowcount, "Record inserted successfully")
        cursor.close()
        return 0
