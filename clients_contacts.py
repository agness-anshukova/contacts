import psycopg2
import re

# Класс менеджера БД
class DbManager :

    def __init__(self, db_name, user_name, pwd, rm_prev=False ) :
        self.db_name = db_name
        self.user_name = user_name
        self.pwd = pwd
        try:
            if rm_prev :
                self.drop_tables()
            self.create_tables() 
            self.connection.close()
        except psycopg2.OperationalError:
            print('Can\'t init DB')
    
    # Функция, удаляющая структуру БД
    def drop_tables(self) :
        self.get_cursor()
        try:
            cursor = self.connection.cursor()
            with cursor as cur :
                cur.execute('DROP TABLE IF EXISTS persons CASCADE;')
                cur.execute('DROP TABLE IF EXISTS phones CASCADE;')
                self.connection.commit()
            self.connection.close()
        except psycopg2.OperationalError:
            print('Can\'t drop tables')

    # Функция, создающая структуру БД
    def create_tables(self) :
        self.get_cursor()
        try:
            cursor = self.connection.cursor()
            with cursor as cur :
                # Таблица клиентов с email
                cur.execute('CREATE TABLE IF NOT EXISTS persons(\
                                person_id serial primary key,\
                                familyname varchar(40) not null,\
                                name varchar(40) not null,\
                                email varchar(256) not null unique check(email similar to \'([aA-zZ,0-9,\.,\-,\_]*)@([0-9]*[aA-zZ]*).[aA-zZ]*\'),\
                                unique(familyname,name,email));')
                # Таблица с номерами телефонов
                cur.execute('CREATE TABLE IF NOT EXISTS phones(\
                                phone_id serial primary key,\
	                            phone_code varchar(3) not null check(phone_code similar to \'\d{3}\'),\
	                            phone_number varchar(9) not null check(phone_number similar to \'\d{2,3}-\d{2}-\d{2}\'),\
	                            is_main boolean not null default false,\
	                            person_id integer not null references persons(person_id),\
	                            unique(is_main, person_id));')
                self.connection.commit()
            self.connection.close()
        except psycopg2.OperationalError:
            print('Can\'t create tables')
    
    def get_cursor(self) :
        self.connection = psycopg2.connect(database=self.db_name, user=self.user_name, password=self.pwd)

# Класс клиент
class Client :
    def __init__(self, client_familyname, client_name, client_email) :
        self.id = None
        self.client = {}
        self.familyname = client_familyname.strip()
        self.name = client_name.strip()
        pattern = re.compile("([aA-zZ,0-9,\.,\-,\_]*)@([0-9]*[aA-zZ]*).[aA-zZ]*")
        if pattern.match(client_email.strip()) :
            self.email = client_email.strip()
        else:
            print('Invalid email')

        self.get_id(db_manager)


    # Функция, позволяющая добавить нового клиента
    def add_new_client(self, db_manager) :
        if self.email :
            try:
                db_manager.get_cursor()
                cursor = db_manager.connection.cursor()
                with cursor as cur :
                    sql_string = "INSERT INTO persons (familyname,name, email) VALUES (%s,%s,%s) RETURNING person_id;"
                    cur.execute(sql_string, (self.familyname,self.name,self.email))
                    self.id = cur.fetchone()[0]
                    db_manager.connection.commit()
                db_manager.connection.close()
            except psycopg2.OperationalError:
                print('Can\'t add person')    

    # Функция, позволяющая изменить данные о клиенте
    def update_client(self, db_manager, client_dict) :
        if self.id is None :
            print('You have to add a person before update it')
        # Начинаем работу с базой
        db_manager.get_cursor()
        cursor = db_manager.connection.cursor()
        if type(client_dict) is dict :
            try:
                with cursor as cur :
                    if 'familyname' in client_dict :
                        sql_string = "UPDATE persons SET familyname=%s WHERE person_id = %s;"
                        cur.execute(sql_string, (client_dict.get('familyname'),self.id,))
                        self.familyname = client_dict.get('familyname')
                    db_manager.connection.commit()
                    if 'name' in client_dict :
                        sql_string = "UPDATE persons SET name=%s WHERE person_id = %s;"
                        cur.execute(sql_string, (client_dict.get('name'),self.id,))
                        self.name = client_dict.get('name')
                    db_manager.connection.commit()
                    if 'email' in client_dict :
                        sql_string = "UPDATE persons SET email=%s WHERE person_id = %s;"
                        cur.execute(sql_string, (client_dict.get('email'),self.id,))
                        self.email = client_dict.get('email')
                    if 'phone' in client_dict and (type(client_dict.get('phone')) is list):
                        for i in client_dict.get('phone') :
                            pattern = re.compile('\d{3}-\d{2,3}-\d{2}-\d{2}')
                            old_phone = i['old_phone'] 
                            if pattern.match(old_phone.strip()) :
                                old_code = old_phone.strip().split('-')[0]
                                old_numb = old_phone.strip()[4:]
                            new_phone = i['new_phone'] 
                            if pattern.match(new_phone.strip()) :
                                new_code = new_phone.strip().split('-')[0]
                                new_numb = new_phone.strip()[4:]   
                             
                                sql_string = "UPDATE phones SET phone_code=%s, phone_number=%s\
                                  WHERE  phone_code=%s and phone_number=%s and person_id = %s;"
                                cur.execute(sql_string, (new_code, new_numb, old_code, old_numb, self.id,))
                    db_manager.connection.commit()
                db_manager.connection.close()
                return self.client
            except psycopg2.OperationalError:
                print('Can\'t get person')
                

    # Функция, позволяющая найти клиента по его данным.
    def get_client(self, db_manager, familyname=None, name=None, email=None, phone=None) :
        db_manager.get_cursor()
        cursor = db_manager.connection.cursor()
        if familyname is not None and name is not None :
            return self.get_client_by_fio(db_manager,familyname, name) 
        elif email is not None :
            try:
                with cursor as cur :
                    sql_string = "SELECT person_id,familyname,name FROM persons WHERE email = %s;"
                    cur.execute(sql_string, (email,))
                    result = cur.fetchone()
                    self.client['person_id'] = result[0]
                    self.client['familyname'] = result[1]
                    self.client['name'] = result[2]
                    self.client['email'] =  email
                    sql_string = "SELECT array_agg(phone_code||\'-\'||phone_number) FROM phones WHERE person_id = %s;"
                    cur.execute(sql_string, ( self.client.get('person_id'), ) )
                    result = cur.fetchone()
                    self.client['phone'] =  result[0]
                db_manager.connection.close()
                return self.client
            except psycopg2.OperationalError:
                print('Can\'t get person')
        elif phone is not None :
            pattern = re.compile('\d{3}-\d{2,3}-\d{2}-\d{2}')
            if pattern.match(phone.strip()) :
                code = phone.strip().split('-')[0]
                numb = phone.strip()[4:]
            try:
                with cursor as cur :
                    sql_string = "SELECT person_id,familyname,name,email FROM persons WHERE person_id = \
                                  (SELECT person_id FROM phones WHERE phone_number = %s and phone_code = %s);"
                    cur.execute(sql_string, (numb,code))
                    result = cur.fetchone()
                    self.client['person_id'] = result[0]
                    person_id = self.client['person_id'] 
                    self.client['familyname'] = result[1]
                    self.client['name'] = result[2]
                    self.client['email'] =  result[3]
                    sql_string = "SELECT array_agg(phone_code||\'-\'||phone_number) FROM phones WHERE person_id = %s;"
                    cur.execute(sql_string, ( person_id, ) )
                    result = cur.fetchone()
                    self.client['phone'] =  result[0]
                db_manager.connection.close()
                return self.client
            except psycopg2.OperationalError:
                print('Can\'t get person')


    # Функция, позволяющая найти клиента по его данным: имени, фамилии .
    def get_client_by_fio(self, db_manager, familyname, name) :
        clients=[]
        try:
            db_manager.get_cursor()
            cursor = db_manager.connection.cursor()
            with cursor as cur :
                sql_string = "SELECT person_id, email FROM persons WHERE familyname = %s and name = %s;"
                cur.execute(sql_string, (familyname,name,))
                result = cur.fetchall()
                for i in result :
                    client={}
                    client['person_id'] = i[0]
                    person_id = i[0]
                    client['familyname'] = familyname
                    client['name'] = name
                    client['email'] =  i[1]
                    sql_string = "SELECT array_agg(phone_code||\'-\'||phone_number) FROM phones WHERE person_id = %s;"
                    cur.execute(sql_string, ( person_id, ) )
                    result = cur.fetchone()
                    client['phone'] =  result[0]
                    clients.append(client)
            db_manager.connection.close()
        except psycopg2.OperationalError:
                print('Can\'t get person')
        return clients
    
    def get_id(self, db_manager) :
            try:
                db_manager.get_cursor()
                cursor = db_manager.connection.cursor()
                with cursor as cur :
                    sql_string = "SELECT person_id FROM persons WHERE familyname = %s and name = %s and email = %s;"
                    cur.execute(sql_string, (self.familyname,self.name,self.email))
                    for record in cur:
                        self.id = record[0]
                db_manager.connection.close()
            except psycopg2.OperationalError:
                print('Can\'t get person id')
    
    # Функция, позволяющая добавить телефон для существующего клиента.
    def add_phone(self,db_manager, phone, is_main=False) :
        if self.id is None :
            print('You have to add a person before update it')
        pattern = re.compile('\d{3}-\d{2,3}-\d{2}-\d{2}')
        if pattern.match(phone.strip()) :
            code = phone.strip().split('-')[0]
            numb = phone.strip()[4:]
            try:
                db_manager.get_cursor()
                cursor = db_manager.connection.cursor()
                with cursor as cur :
                    sql_string = "INSERT INTO phones (phone_code,phone_number,is_main,person_id) VALUES (%s,%s,%s,%s) RETURNING person_id;"
                    cur.execute(sql_string, (code,numb,is_main,self.id))
                    self.id = cur.fetchone()[0]
                    db_manager.connection.commit()
                db_manager.connection.close()
            except psycopg2.OperationalError:
                print('Can\'t add phone') 
    
    # Функция, позволяющая удалить телефон для существующего клиента.
    def del_phone (self,db_manager, phone) :
        if self.id is None :
            print('You have to add a person before delete the phone')
        pattern = re.compile('\d{3}-\d{2,3}-\d{2}-\d{2}')
        if pattern.match(phone.strip()) :
            code = phone.strip().split('-')[0]
            numb = phone.strip()[4:]
            try:
                db_manager.get_cursor()
                cursor = db_manager.connection.cursor()
                with cursor as cur :
                    sql_string = "DELETE FROM phones WHERE phone_code=%s and phone_number=%s;"
                    cur.execute(sql_string, (code,numb))
                    db_manager.connection.commit()
                db_manager.connection.close()
            except psycopg2.OperationalError:
                print('Can\'t delete phone') 
    
    # Функция, позволяющая удалить существующего клиента.
    def del_client (self,db_manager) :
        if self.id is None :
            print('You have to add a person before delete')
        try: 
            id1 = self.id
            id2 = self.id
            db_manager.get_cursor()
            cursor = db_manager.connection.cursor()
            with cursor as cur :
                sql_string = "DELETE FROM phones WHERE person_id=%s;"
                cur.execute(sql_string, (self.id,) )
                sql_string = "DELETE FROM persons WHERE person_id=%s;"
                cur.execute(sql_string, (self.id,) )
                db_manager.connection.commit()
            db_manager.connection.close()
        except psycopg2.OperationalError:
                print('Can\'t del person') 



db_manager = DbManager("newbase", "postgres", "xxxxxx")

#martin = Client('evans','martin','martin.evans@gmail.com')
#martin2 = Client('evans','martin','martin2.evans@gmail.com')
peter = Client('evans','peter','peter.evans@gmail.com')
martha = Client('winter','marfa','marfa.winter@gmail.com')

#martha.get_id(db_manager)
#martha.add_new_client(db_manager)
#martha.get_id(db_manager)
#martha.add_phone( db_manager, '496-528-22-75', False) 
#martha.add_phone( db_manager, '493-528-53-88', True) 
#print(martha.id)
#martin2.add_new_client(db_manager)
#peter.add_new_client(db_manager)
#martin.get_id(db_manager)
#print(martin.id)
#print(peter.id)
#martin.add_phone( db_manager, '499-528-22-75', False) 
#peter.add_phone( db_manager, '499-528-53-88', True) 
#print(martin.get_client_by_fio(db_manager, 'evans','martin'))
#print(martin.get_client(db_manager=db_manager, email='martin2.evans@gmail.com'))
#print(martin.get_client(db_manager=db_manager, phone='499-528-52-88'))

client_dict = {'familyname':'winter','name':'marfa','email':'marfa.winter@gmail.com',
               'phone':[{'old_phone':'496-528-22-75', 'new_phone':'596-528-22-75'},
                        {'old_phone':'493-528-53-88', 'new_phone':'596-528-00-75'}]}
martha.update_client(db_manager, client_dict)
martha.get_id(db_manager)
martha.del_phone (db_manager, '596-528-00-75') 
martha.add_phone( db_manager, '477-528-53-88', True) 
martha.del_phone( db_manager, '596-528-22-75')
print(martha.get_client(db_manager=db_manager, email='marfa.winter@gmail.com'))
print(peter.get_client_by_fio(db_manager, 'evans','peter'))
peter.del_client(db_manager)