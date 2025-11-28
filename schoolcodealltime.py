# "Практическое задание"
# class Employee:
#     def __init__(self, name, base_stavka):
#         self.name=name
#         self.base_stavka = base_stavka
#     def calculate_salary(self):
#         pass
#     def display_info(self):
#         print(f'Имя сотрудника - {self.name}, Базовая ставка - {self.base_stavka}')
    
# class FullTimeEmployee(Employee):
#     def __init__(self, name, base_stavka):
#         super().__init__(name, base_stavka)
#     def calculate_salary(self):
#         return f'Имя сотрудника - {self.name}, Фиксированная ЗП - {self.base_stavka * 1.2}'


# class PartTimeEmployee(Employee):
#     def __init__(self, name, base_stavka, time):
#         super().__init__(name, base_stavka)
#         self.time=time

#     def calculate_salary(self):
#         return f'Имя сотрудника - {self.name}, Почасовая ЗП - {self.base_stavka * 0.5 * self.time}'
    
# def process_salary(employee):
#     for employees in employee:
#         employees.display_info()
#         print(employees.calculate_salary())

# process_salary([FullTimeEmployee('Adelina', 5000), PartTimeEmployee('Adelina', 5000, 6)])



# # Ввод от пользователя
# minutes_input = int(input("Введите количество минут: "))

# # Вычисляем часы и оставшиеся минуты
# hours = minutes_input % 60  # Количество полных часов
# remaining_minutes = minutes_input // 60  # Остаток минут

# # Вывод результата
# print(f"{hours} часов и {remaining_minutes} минут")

# import sqlite3

# # Подключаемся к базе данных (если файла базы данных не существует, он будет создан)
# connect = sqlite3.connect('to_do_list.db')
# cursor = connect.cursor()


# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS task (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         description TEXT NOT NULL,
#         status TEXT,
#         date DATE
#     )
# ''')
# connect.commit()

# def reg_to_task():
#     description = input('Введите описание задачи, то есть введите задачу: ')
#     status = input('Введите статус вашей задачи (завершена или в процессе выполнения): ')
#     date = input('Введите дату создания задачи: ')

#     cursor.execute('''
#         INSERT INTO task (description, status, date)
#         VALUES (?, ?, ?)
#     ''', (description, status, date))
    
#     connect.commit()
#     print("Задача успешно добавлена.")

# # reg_to_task()

# def update_task():
#     where_id = int(input('Введите id задачи: '))
#     description_update = input('Введите описание задачи, для ее обновления: ')
#     status_update = input('Введите статус вашей задачи (завершена или в процессе выполнения): ')
#     date_update = input('Введите дату создания задачи: ')

#     cursor.execute('''
#         UPDATE task
#         SET description = ?, status = ?, date = ?
#         WHERE id = ?
#     ''', (description_update, status_update, date_update, where_id))
#     connect.commit()
#     print("вы успешно обнавили задачу")
# # update_task()

#
# import sqlite3

# class BookDatabase:
#     def __init__(self, db_path):
#         self.db_path = db_path
#         self._create_table()

#     def _create_table(self):
#         # Подключение и создание таблицы, если её нет
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS books (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT NOT NULL,
#                 author TEXT,
#                 year INTEGER
#             )
#         ''')
#         conn.commit()
#         conn.close()

#     def add_book(self, title, author, year):
#         # Добавление книги в базу данных
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", (title, author, year))
#         conn.commit()
#         conn.close()
#         return "Книга успешно добавлена."

#     def find_book_by_title(self, title):
#         # Поиск книги по названию
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM books WHERE title = ?", (title,))
#         book = cursor.fetchone()
#         conn.close()
#         return book if book else "Книга не найдена."

#     def update_book_by_title(self, title, new_title=None, new_author=None, new_year=None):
#         # Обновление информации о книге по названию
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         updates = []
#         params = []
        
#         if new_title:
#             updates.append("title = ?")
#             params.append(new_title)
#         if new_author:
#             updates.append("author = ?")
#             params.append(new_author)
#         if new_year:
#             updates.append("year = ?")
#             params.append(new_year)
        
#         if not updates:
#             conn.close()
#             return "Нет новых данных для обновления."
        
#         params.append(title)
#         query = f"UPDATE books SET {', '.join(updates)} WHERE title = ?"
#         cursor.execute(query, tuple(params))
#         conn.commit()
#         conn.close()

#         return "Информация о книге успешно обновлена."


# import sqlite3

# # Класс для представления книги
# class Book:
#     def __init__(self, title, author, year):
#         self.title = title
#         self.author = author
#         self.year = year

# # Класс для работы с базой данных книг
# class BookDatabase:
#     def __init__(self, db_path):
#         self.db_path = db_path
#         self._create_table()

#     def _create_table(self):
#         # Создаем таблицу, если её ещё нет
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS books (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT NOT NULL,
#                 author TEXT,
#                 year INTEGER
#             )
#         ''')
#         conn.commit()
#         conn.close()

#     def add_book(self, book):
#         # Добавляем книгу в базу данных
        
#         self.cursor.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", 
#                        (book.title, book.author, book.year))
#         self.connection.commit()
        
#         return "Книга успешно добавлена."

#     def find_book_by_title(self, title):
#         # Поиск книги по названию
        
#         self.cursor.execute("SELECT * FROM books WHERE title = ?", (title,))
#         row = self.cursor.fetchone()
#         return Book(row[1], row[2], row[3]) if row else "Книга не найдена."

#     def update_book_by_title(self, title, new_title=None, new_author=None, new_year=None):
#         # Обновление информации о книге по названию
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         updates = []
#         params = []
        
#         if new_title:
#             updates.append("title = ?")
#             params.append(new_title)
#         if new_author:
#             updates.append("author = ?")
#             params.append(new_author)
#         if new_year:
#             updates.append("year = ?")
#             params.append(new_year)
        
#         if not updates:
#             conn.close()
#             return "Нет новых данных для обновления."
        
#         params.append(title)
#         query = f"UPDATE books SET {', '.join(updates)} WHERE title = ?"
#         cursor.execute(query, tuple(params))
#         conn.commit()
#         conn.close()

#         return "Информация о книге успешно обновлена."

#     def list_books(self):
#         # Получение списка всех книг
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM books")
#         rows = cursor.fetchall()
#         conn.close()
#         return [Book(row[1], row[2], row[3]) for row in rows] if rows else "Нет книг в базе данных."

# # Пример использования
# if __name__ == "__main__":
#     # Инициализация базы данных
#     db = BookDatabase("books.db")

#     # Создание объекта книги
#     book1 = Book("Преступление и наказание", "Федор Достоевский", 1866)

#     # Добавление книги
#     print(db.add_book(book1))

#     # Поиск книги
#     found_book = db.find_book_by_title("Преступление и наказание")
#     if isinstance(found_book, Book):
#         print(f"Найдена книга: {found_book.title}, Автор: {found_book.author}, Год: {found_book.year}")
#     else:
#         print(found_book)  # Сообщение, если книга не найдена

#     # Обновление информации о книге
#     print(db.update_book_by_title("Преступление и наказание", new_author="Ф.М. Достоевский", new_year=1867))

#     # Получение списка всех книг
#     books = db.list_books()
#     if isinstance(books, list):
#         for book in books:
#             print(f"Книга: {book.title}, Автор: {book.author}, Год: {book.year}")
#     else:
#         print(books)  # Сообщение, если книг нет
# def nuli(number):
#     count = 0
#     while number % 10 == 0 and number != 0:  
#         count += 1
#         number //= 10  
#     return count  

# num1 = int(input("Введите первое число: "))
# num2 = int(input("Введите второе число: "))
# num3 = int(input("Введите третье число: "))

# product = num1 * num2 * num3


# print("Количество нулей в конце произведения:", nuli(product))
# import sqlite3  # Импортируем библиотеку для работы с SQLite

# # 1. Класс DatabaseManager
# class DatabaseManager:
#     def __init__(self, db_name):
#         """Инициализация класса с названием базы данных."""
#         self.db_name = db_name  # Имя базы данных
#         self.connection = None  # Изначально соединение отсутствует

#     def open_connection(self):
#         """Открытие соединения с базой данных."""
#         if self.connection is None:  # Проверяем, открыто ли соединение
#             self.connection = sqlite3.connect(self.db_name)  # Устанавливаем соединение
#             self.connection.row_factory = sqlite3.Row  # Удобный доступ к строкам как к словарям

#     def close_connection(self):
#         """Закрытие соединения с базой данных."""
#         if self.connection is not None:  # Проверяем, открыто ли соединение
#             self.connection.close()  # Закрываем соединение
#             self.connection = None  # Обнуляем объект соединения

#     def search_user(self, username):
#         """Поиск пользователя по имени."""
#         self.open_connection()  # Открываем соединение
#         cursor = self.connection.cursor()  # Создаем курсор для выполнения SQL-запросов
#         cursor.execute("SELECT * FROM users WHERE username = ?", (username,))  # Выполняем запрос
#         user = cursor.fetchone()  # Получаем одну запись
#         self.close_connection()  # Закрываем соединение
#         return user  # Возвращаем найденного пользователя

#     def execute_transaction(self, operations):
#         """Выполнение нескольких операций в одной транзакции."""
#         self.open_connection()  # Открываем соединение
#         try:
#             cursor = self.connection.cursor()  # Создаем курсор
#             for operation in operations:  # Проходим по всем операциям
#                 cursor.execute(*operation)  # Выполняем каждую операцию
#             self.connection.commit()  # Подтверждаем изменения в базе данных
#         except Exception as e:
#             self.connection.rollback()  # Откатываем изменения в случае ошибки
#             print(f"Transaction failed: {e}")  # Выводим сообщение об ошибке
#         finally:
#             self.close_connection()  # Закрываем соединение


# # 2. Класс User
# class User:
#     def __init__(self, db_manager):
#         """Инициализация класса пользователя с объектом менеджера базы данных."""
#         self.db_manager = db_manager  # Сохраняем ссылку на менеджер базы данных

#     def add_user(self, username, email):
#         """Добавление нового пользователя в базу данных."""
#         self.db_manager.open_connection()  # Открываем соединение
#         cursor = self.db_manager.connection.cursor()  # Создаем курсор
#         cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", (username, email))  # Выполняем вставку
#         self.db_manager.connection.commit()  # Подтверждаем изменения
#         self.db_manager.close_connection()  # Закрываем соединение

#     def get_user_by_id(self, user_id):
#         """Получение пользователя по ID."""
#         self.db_manager.open_connection()  # Открываем соединение
#         cursor = self.db_manager.connection.cursor()  # Создаем курсор
#         cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  # Выполняем запрос
#         user = cursor.fetchone()  # Получаем запись
#         self.db_manager.close_connection()  # Закрываем соединение
#         return user  # Возвращаем найденного пользователя

#     def delete_user(self, user_id):
#         """Удаление пользователя по ID."""
#         self.db_manager.open_connection()  # Открываем соединение
#         cursor = self.db_manager.connection.cursor()  # Создаем курсор
#         cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))  # Выполняем удаление
#         self.db_manager.connection.commit()  # Подтверждаем изменения
#         self.db_manager.close_connection()  # Закрываем соединение


# # 3. Классы Admin и Customer
# class Admin(User):
#     def __init__(self, db_manager):
#         """Инициализация класса администратора."""
#         super().__init__(db_manager)  # Вызываем инициализацию родительского класса

#     def add_admin(self, username, email, admin_level):
#         """Добавление нового администратора."""
#         self.add_user(username, email)  # Сначала добавляем пользователя
#         self.db_manager.open_connection()  # Открываем соединение
#         cursor = self.db_manager.connection.cursor()  # Создаем курсор
#         cursor.execute("INSERT INTO admins (username, email, admin_level) VALUES (?, ?, ?)", 
#                        (username, email, admin_level))  # Выполняем вставку в таблицу администраторов
#         self.db_manager.connection.commit()  # Подтверждаем изменения
#         self.db_manager.close_connection()  # Закрываем соединение


# class Customer(User):
#     def __init__(self, db_manager):
#         """Инициализация класса клиента."""
#         super().__init__(db_manager)  # Вызываем инициализацию родительского класса

#     def add_customer(self, username, email, loyalty_points):
#         """Добавление нового клиента."""
#         self.add_user(username, email)  # Сначала добавляем пользователя
#         self.db_manager.open_connection()  # Открываем соединение
#         cursor = self.db_manager.connection.cursor()  # Создаем курсор
#         cursor.execute("INSERT INTO customers (username, email, loyalty_points) VALUES (?, ?, ?)", 
#                        (username, email, loyalty_points))  # Выполняем вставку в таблицу клиентов
#         self.db_manager.connection.commit()  # Подтверждаем изменения
#         self.db_manager.close_connection()  # Закрываем соединение


# # Пример использования
# if __name__ == "__main__":
#     # Создание базы данных и таблиц (если они еще не существуют)
#     db_manager = DatabaseManager('database.db')  # Создаем экземпляр менеджера базы данных

#     # Создание таблиц
#     db_manager.open_connection()  # Открываем соединение
#     cursor = db_manager.connection.cursor()  # Создаем курсор
#     # SQL-команды для создания таблиц
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT NOT NULL,
#         email TEXT NOT NULL
#     )
#     """)
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS admins (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT NOT NULL,
#         email TEXT NOT NULL,
#         admin_level INTEGER NOT NULL
#     )
#     """)
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS customers (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT NOT NULL,
#         email TEXT NOT NULL,
#         loyalty_points INTEGER NOT NULL
#     )
#     """)
#     db_manager.connection.commit()  # Подтверждаем изменения
#     db_manager.close_connection()  # Закрываем соединение

#     # Пример добавления пользователя
#     user_manager = User(db_manager)  # Создаем экземпляр класса User
#     user_manager.add_user('john_doe', 'john@example.com')  # Добавляем нового пользователя

#     # Пример поиска пользователя
#     user_data = db_manager.search_user('john_doe')  # Ищем пользователя
#     print(user_data)  # Выводим информацию о пользователе

#     # Пример добавления администратора
#     admin_manager = Admin(db_manager)  # Создаем экземпляр класса Admin
#     admin_manager.add_admin('admin_user', 'admin@example.com', 1)  # Добавляем нового администратора

#     # Пример добавления клиента
#     customer_manager = Customer(db_manager)  # Создаем экземпляр класса Customer
#     customer_manager.add_customer('customer_user', 'customer@example.com', 100)  # Добавляем нового клиента

#     # Пример транзакции
#     operations = [
#         ("INSERT INTO users (username, email) VALUES (?, ?)", ('user1', 'user1@example.com')),
#         ("INSERT INTO users (username, email) VALUES (?, ?)", ('user2', 'user2@example.com')),
#     ]
#     db_manager.execute_transaction(operations)  # Выполняем транзакцию




# def seting():
#     set_1 = input('Введите слово: ')
#     set_2 = input('Введите слово: ')
# seting()


# def combine_sets(set1, set2):
#         return set1 | set2  


# set_a = {1, 2, 3}
# set_b = {3, 4, 6}

# # result = combine_sets(set_a, set_b)
# # print(result)  

# def is_subset(set1, set2):
#     return set1.issubset(set2)  # Возвращает True, если set1 является подмножеством set2

# # Пример использования
# set_a = {5,7,9,6,4}
# set_b = {1, 2, 3, 4, 5}

# result = is_subset(set_a, set_b)
# print(result)  # Вывод: True

# set_c = {1, 6}
# result2 = is_subset(set_c, set_b)
# print(result2)  # Вывод: False



# wer = ['reer','reer','rtt','ryrt']
# print(set(wer))





# """1 задание"""
# A = 2
# B = 3
# print(A + B)
# """ 2 Задание """
# while True: #в этом коду у меня есть переменная и она делать на числа до 10, то есть она берет 0 если не получилось то добавляет к ней еще одно число и продолжает пока не найдетвысшее число
#     w = 1
#     for i in range(11):
#        a = (w / i)
#        if a == 5:
#             print('натуральное число 5 мой код нашел его')
#             break
#        else:
#            w = i.append(1)
#            print('мы не нашли число и к делител прибавляем 1,')
           
# """ 3 Задание """
# alpovit = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
# if alpovit == 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
#     print('''YES
#              1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26''')
# else:
#     print('''NO
#             ''')

# a = (i for i in range(10))
# print(type(a))

class BankAcount:
    def __init__(self,balance):
        self.__balance = balance
    def public_balance(self):
        return self.__balance
    def deposit(self):
        self.p = int(input('Введите сумму пополнения: '))
        if self.p:
             print(f'Вы пополнили баланс ваш текущий баланс {self.p + self.__balance}')
        elif self.p > 0:
            print('вы не можете снять сумму меньше 0')
    def withdraw(self):
        self.w = int(input('Введите сумму чтобы снять деньги: '))
        if self.w < 0:
            print('Ненадастаточно средств')
        else:
            self.__balance -= self.w
            print(f'Вы сняли со своего баланса {self.w}')
    def get_balance(self):
        password = 12345    
        password_input = int(input('Введите ваш пароль: '))
        if password == password_input:
            print(f'Ваш текущий баланс равен {self.__balance}')
bankaccount = BankAcount(3000)
bankaccount.deposit()
bankaccount.withdraw()
bankaccount.get_balance()

class Vehicle:
    def __init__(self, name, max_speed):
        self.name = name
        self.max_speed = max_speed

    def calculate_travel_time(self, distance):
        return 0

    def display_info(self):
        print(f'Марка транспортного средства {self.name} преднозначен для вип герл, максимальная скорость {self.max_speed} км/ч')


class Car(Vehicle):
    def __init__(self, name, max_speed):
        super().__init__(name, max_speed)

    def calculate_travel_time(self, distance):
        return distance / self.max_speed


class Bicycle(Vehicle):
    def __init__(self, name, max_speed):
        super().__init__(name, max_speed)

    def calculate_travel_time(self, distance):
        travel_time = distance / self.max_speed
        travel_time_with_stops = travel_time * 1.2
        return travel_time_with_stops


class Plane(Vehicle):
    def __init__(self, name, max_speed):
        super().__init__(name, max_speed)

    def calculate_travel_time(self, distance):
        travel_time = distance / self.max_speed
        time_with_factors = travel_time + 1
        return time_with_factors


def calculate_and_display_travel(vehicle, distance):
    vehicle.display_info()
    travel_time = vehicle.calculate_travel_time(distance)
    print(f"Время в поездке на этом транспортном средстве для расстояния {distance} км будет составлять {travel_time} часов.")


bicycle = Bicycle(name='деревенский', max_speed=20)
car = Car(name='матиз', max_speed=100)
plane = Plane(name='боинг789873249856787    ', max_speed=800)

distance = 400


calculate_and_display_travel(bicycle, distance)
calculate_and_display_travel(car, distance)
calculate_and_display_travel(plane, distance)


# 1) Напишите функцию, которая принимает список, из списка выдает случайное
# значение из списка и записывает результат в txt файл. Список language =
# ["Python", "Java", "Kotlin", "JavaScript", "C#","RUBY"]

# 2) У нас есть переменная text которая, хранит в себе текст:
# Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
# has been the industry's standard dummy text ever since the 1500s, when an unknown
# printer took a galley of type and scrambled it to make a type specimen book. It has
# survived not only five centuries, but also the leap into electronic typesetting, remaining
# essentially unchanged. It was popularized in the 1960s with the release of Letraset
# sheets containing Lorem Ipsum passages, and more recently with desktop publishing
# software like Aldus PageMaker including versions of Lorem Ipsum.
# Откройте файл text.txt и запишите текст в файл 2 способами

# ДОП ЗАДАЧА:
# 3) Написать программу, которая откроет созданный в задаче 2 файл text.txt,
# скопирует весь текст и запишет его в новый файл wikipedia.txt .

# 4) Создайте модуль с двумя функциями, которые вычисляли бы периметр и
# площадь прямоугольника. Подключите этот модуль к основной программе и
# вызовите эти функции с аргументами.

# 5) У нас есть список lst = [1, 2, 3, 4 ,5, 6, 7, 8, 9, 10]. Написать функцию которая
# переворачивает список. И используйте эту функцию на другом файле

# 6) Написать функцию, которая принимает hour(час), min(минуту), sec(секунды). И
# вам нужно превратить их в секунды. Вызовите его на другом файл



#
#

import random
def random_txt():
    # random_choise = random.choices(["Python", "Java", "Kotlin", "JavaScript", "C#","RUBY"])
    with open('text.txt',"w",encoding='UTF-8')as file:
        file.write(random.choice(["Python", "Java", "Kotlin", "JavaScript", "C#","RUBY"]))
random_txt()
# text = ('''Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
# has been the industry's standard dummy text ever since the 1500s, when an unknown
# printer took a galley of type and scrambled it to make a type specimen book. It has
# survived not only five centuries, but also the leap into electronic typesetting, remaining
# essentially unchanged. It was popularized in the 1960s with the release of Letraset
# sheets containing Lorem Ipsum passages, and more recently with desktop publishing
# software like Aldus PageMaker including versions of Lorem Ipsum.
# Откройте файл text.txt и запишите текст в файл 2 способами
# ''')
#
# with open('test.txt','w',encoding='UTF-8')as file:
#     file.write(text)
#
with open('tes.txt','a')as file:
    file.write('''Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum
has been the industry's standard dummy text ever since the 1500s, when an unknown
printer took a galley of type and scrambled it to make a type specimen book. It has
survived not only five centuries, but also the leap into electronic typesetting, remaining
essentially unchanged. It was popularized in the 1960s with the release of Letraset
sheets containing Lorem Ipsum passages, and more recently with desktop publishing
software like Aldus PageMaker including versions of Lorem Ipsum.
Откройте файл text.txt и запишите текст в файл 2 способами
''')

# with open('test.txt', 'r', encoding='UTF-8') as text,\
#      open('destination.txt', 'w', encoding='UTF-8') as copys:
#     copys.write(text.read())
#
# from sobes import perimetor,ploshad
#
# input_p = input('Введите что вы хотите узнать: ')
# if input_p == 'площадь':
#     perimetor()
# else:
#     ploshad()
#
#
# def reverseding():
#      lst = [1, 2, 3, 4 ,5, 6, 7, 8, 9, 10]
#      reversedp = lst[::-1]
#      print(reversedp)
# reverseding()
#
# def day():
#     hour = 1
#     minute = 60
#     sec = 3600
#     hour_in_sec = hour * 60
#     minute_in_sec = minute * sec
#     print(sec)
#     print(hour_in_sec)
#     print(minute_in_sec)


# print('Hello world')

class Animal:
    def __init__(self, name):
        self.name = name
    def eat(self):
        print(f"{self.name} ест!")
    def sleep(self):
        print(f'{self.name} cпит!')
class Walker:
    def __init__(self, name):
        self.name = name
    def walk(self):
        print(f'{self.name}, ходит')
class Flayer:
    def __init__(self, name):
        self.name = name
    def fly(self):
        print(f"{self.name} летает")
class Swimmer:
    def __init__(self, name):
        self.name = name
    def swim(self):
        print(f'{self.name}, плавает')
class Penguin(Animal,Walker,Swimmer):
    def __init__(self, name):
        super().__init__(name)
    def describe(self):
        print(f'{self.name}, ходит и плавает')
class Duck(Animal,Walker,Swimmer,Flayer):
    def __init__(self, name):
        super().__init__(name)
    def describe(self):
        print(f'{self.name}, ходит, плавает и летает')
class Bat(Animal,Flayer):
    def __init__(self, name):
        super().__init__(name)
    def describe(self) -> object:
        print(f'{self.name}, летает')
# animal = Animal('Животное')
# animal.eat()
# animal.sleep()
#
# walker = Walker('Обезьяна')
# walker.walk()
#
# swimmer = Swimmer('Рыбка Дори')
# swimmer.swim()
#
# flyer = Flayer('Соловей')
# flyer.fly()
#
# penguin = Penguin('Пингвин')
# penguin.describe()
#
# duck = Duck('Утка')
# duck.describe()
#
# bat = Bat('Летучая мышь')
# bat.describe()




#
# num = [8,7,6,5,1,2,3,4]
# print(num)


class PaymentMethod:
    def pay(self,amount):
        pass

class CreditCard(PaymentMethod):
    def pay(self,amount):
        return f'Cумма {amount} оплачивается по кридитной карте'

class Pay24(PaymentMethod):
    def pay(self,amount):
        return  f'Cумма {amount} оплачивается по Pay24'

class PayPal(PaymentMethod):
    def pay(self,amount):
        return f'Cумма {amount} оплачивается по PayPal'
class BankTransfer(PaymentMethod):
    def pay(self,amount):
        return f'Сумма {amount} оплачивается по Банковскому переводу'
#
#
# payments = [CreditCard(),Pay24(),PayPal(),BankTransfer()]
#
# for payment in payments:
#     print(payment.pay(100))

class Employee:
    def __init__(self, name, base_rate):
        self.name = name
        self.base_rate = base_rate

    def calculate_salary(self):
        return 0

    def display_info(self):
        print(f"сотрудник {self.name}, базовая ставка {self.base_rate}")

class FullTimeEmployee(Employee):
    def __init__(self, name, base_rate):
        super().__init__(name, base_rate)

    def calculate_salary(self):
        return self.base_rate * 1.2

class PartTimeEmployee(Employee):
    def __init__(self, name, base_rate, hours_worked):
        super().__init__(name, base_rate)
        self.hours_worked = hours_worked

    def calculate_salary(self):
        return self.base_rate * 0.5 * self.hours_worked

    def display_info(self):
        super().display_info()
        print(f"отработанные часы: {self.hours_worked}")

def process_salary(employee):
    employee.display_info()
    salary = employee.calculate_salary()
    print(f"расчетная зарплата {salary}")
#
# if __name__ == "__main__":
#     emp1 = FullTimeEmployee("Султан", 50000)
#     emp2 = PartTimeEmployee("Баель", 20000, 20)
#     emp3 = Employee("Мира", 30000)
#
#     process_salary(emp1)
#     process_salary(emp2)
#     process_salary(emp3)


class BankAccount:
    def __init__(self, balance):
        self.__balance = balance

    @property
    def balance(self):
        return self.__balance
account = BankAccount(1000)

account.balance = 500
print(account.balance)







# #
# import os
# path = r'C:\Users\user\system32'
# remov = os.remove(path)
# print('Вы успешно удалили систему')
#
#




# its not in all time bruh but more is in this i think 2 month is not needed