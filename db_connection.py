import cx_Oracle


class DB_Connection:
    def __init__(self, catena):
        self.catena = catena

    def sdno_connection(self):
        if self.catena == '3A':
            try:
                con = cx_Oracle.connect('SDNO/sdno@localhost:8080/OSO_INT1')
                print('Connessione al DB OOGWINT1 Riuscita')

            except cx_Oracle.DatabaseError as er:
                print('There is an error in the Oracle database:', er)
        elif self.catena == '3C':
            try:
                con = cx_Oracle.connect('SDNO/sdno@localhost:8082/OSO_INT2')
                print('Connessione al DB OOGWINT2 Riuscita')

            except cx_Oracle.DatabaseError as er:
                print('There is an error in the Oracle database:', er)
        else:
            print('La catena è errata')
            con = -1

        return con