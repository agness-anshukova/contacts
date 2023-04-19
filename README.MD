
# Программа для управления клиентами
На языке python с использованием библиотеки psycopg2, базы данных PostgreSQL
Приложение позволяет добавлять, изменять и удалять контактные данные клиентов.
База данных приложения хранит следующие данные о клиенте:
- имя,
- фамилия,
- email,
- телефон.

## Схема базы данных приложения 

![N|Solid](Contacts.jpg)

## Сущности

#### Класс DbManager

Инициализирует базу данных приложения. 
Если при инициализации передан параметр rm_prev=True, происходит удаление существующей базы данных и создание новой.

Методы класса DbManager

Функция, удаляющая структуру БД
drop_tables(self)

Функция, создающая структуру БД
create_tables(self)

Пример создания экземпляра класса без удаления существующей БД
```sh

db_manager = DbManager("postgres", "postgres", "xxxxx")

```

Пример создания экземпляра класса с удалением существующей БД
```sh

db_manager = DbManager("postgres", "postgres", "xxxxx", True)

```


#### Класс Client
Класс для создания, удаления и изменения данных о клиенте.
Пример создания экземпляра класса Client
```sh

martha = Client('winter','marfa','marfa.winter@gmail.com')

```

Методы класса Client

Метод добавления нового клиента.
add_new_client(db_manager).
Параметр db_manager - экземпляр класса DbManager.
Пример вызова метода.
```sh

martha.add_new_client(db_manager)

```

Метод, позволяющий изменить данные о клиенте.
update_client(db_manager, client_dict). 
Параметр client_dict - словарь с ключами, обозначающими атрибуты сущности клиент.
Ключ phone подается как список словарей [{'old_phone':'xxx-xxx-xx-xx', 'new_phone':'xxx-xx-xx-xx'}].
Параметр db_manager - экземпляр класса DbManage.r
Пример вызова метода. 
```sh

client_dict = {'familyname':'winter','name':'marfa','email':'marfa.winter@gmail.com',
               'phone':[{'old_phone':'496-528-22-75', 'new_phone':'596-528-22-75'},
                        {'old_phone':'493-528-53-88', 'new_phone':'596-528-00-75'}]}
martha.update_client(db_manager, client_dict)

```

Метод, позволяющий найти клиента по его данным.
get_client(db_manager, familyname=None, name=None, email=None, phone=None). 
Параметр db_manager - экземпляр класса DbManager.
Пример вызова метода.
```sh

martha.get_client(db_manager=db_manager, email='marfa.winter@gmail.com')

```

Метод, позволяющий найти клиента по его данным: имени, фамилии.
get_client_by_fio(db_manager, familyname, name).
Метод возвращает список словарей со свойствами клиентов, имеющих указанные имя и фамилию.
Параметр db_manager - экземпляр класса DbManager.
Пример вызова метода. 
```sh

peter.get_client_by_fio(db_manager, 'evans','peter')

```

Метод, позволяющий добавить телефон для существующего клиента.
add_phone(db_manager, phone, is_main=False).
Параметр db_manager - экземпляр класса DbManager.
Параметр is_main=False означает, что телефон не является основным для клиента.
Пример вызова метода. 
```sh

martha.add_phone( db_manager, '496-528-22-75', False) 

```

Метод, позволяющий удалить телефон для существующего клиента.
del_phone (db_manager, phone).
Параметр db_manager - экземпляр класса DbManager.
Параметр phone - строка, означает номер телефона, который хотим удалить.
Пример вызова метода. 
```sh

martha.del_phone (db_manager, '596-528-00-75') 

```

Метод, позволяющий удалить существующего клиента.
del_client (db_manager).
Параметр db_manager - экземпляр класса DbManager.
```sh

peter.del_client(db_manager)

```