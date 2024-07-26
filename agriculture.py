import os
import psycopg2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from psycopg2 import sql
from tkinter import *
from tkinter import ttk
from tkinter import filedialog, Text, Scrollbar, Frame, Button, messagebox
from pathlib import Path
import datetime
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
def select_text_file(table_name, tree):
    # Открывает окно для выбора файла и позволяет выбрать только текстовые файлы
    filetypes = (("Text files", "*.txt"), ("All files", "*.*"))
    filename = filedialog.askopenfilename(title="Select a text file", filetypes=filetypes)
    if filename:
        full_path = Path(filename).resolve()
        try:
            conn = create_connection()
            with conn:
                cursor = conn.cursor()
                table_name = '"' + table_name + '"'
                # Очистка таблицы
                cursor.execute(f"DELETE FROM {table_name}")
                # Копирование данных из файла в таблицу
                cursor.execute(f"COPY {table_name} FROM '{full_path}' WITH ENCODING 'Windows-1251'")
                # Выполнение выборки данных из таблицы
                if table_name == '"Должность"':
                    cursor.execute(f"""
                        SELECT 
                            "ID сотрудника", 
                            "ID фермы", 
                            "Должность", 
                            "Стаж", 
                            CASE 
                                WHEN "Дата увольнения" = 'infinity' THEN 'infinity'
                                ELSE "Дата увольнения"::text
                            END AS "Дата увольнения"
                        FROM 
                            {table_name};
                    """)
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                # Очистка таблицы tree перед заполнением
                tree.delete(*tree.get_children())
                for row in rows:
                    tree.insert('', END, values=row)
            messagebox.showinfo("Успешно", "Данные были успешно добавлены в базу данных")
        except Exception as e:
            messagebox.showerror("Произошла ошибка", f"Произошла ошибка при импорте: {e}")
# Функция для создания подключения к базе данных
def create_connection():
        conn = psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm')
        return conn
# Функция для создания новой базы данных
def create_database():
    try:
        conn = psycopg2.connect('postgresql://postgres:pg123@localhost:5432/')
        conn.autocommit = True
        with conn.cursor() as cursor:
            sql_query= "CREATE DATABASE farm;"
            cursor.execute(sql.SQL(create_table_query))
            cursor.execute(sql.SQL(sql_query))
    except psycopg2.Error as e:
        print('Ошибка создания базы данных:', e)
# Функция для создания Treeview с полосами прокрутки
def create_table(frame, columns):
    # Создание фрейма для Treeview и полос прокрутки
    tree_frame = Frame(frame)
    tree_frame.place(relwidth=0.85, relheight=0.7, relx=0, rely=0)  # Выравнивание tree_frame слева
    # Создание Treeview
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
    # Установка заголовков столбцов и ширины
    for col in columns:
        # Установка заголовков столбцов и привязка к функции сортировки при нажатии
        tree.heading(col, text=col, anchor=W, command=lambda c=col: sort_table_column(tree, c))
        tree.column(col, stretch=NO, width=100)
    # Добавление вертикальной полосы прокрутки
    vscrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
    tree.configure(yscroll=vscrollbar.set)
    vscrollbar.place(relx=0.975, rely=0, relheight=1)
    # Добавление горизонтальной полосы прокрутки
    hscrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(xscroll=hscrollbar.set)
    hscrollbar.place(relx=0, rely=0.975, relwidth=0.975)
    # Размещение Treeview внутри фрейма
    tree.place(relwidth=0.975, relheight=0.975)
    return tree
def load_data(tree, sql_query, create_table_query=None):
    try:
        conn = create_connection()
        with conn:
            with conn.cursor() as cursor:
                if create_table_query:
                    cursor.execute(create_table_query)
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                for row in rows:
                    tree.insert('', END, values=row)
    except Exception as e:
        create_database()
#Выполнение sql запросов с выгрузкой строк
def execute_sql_query(query):
    try:
        conn = create_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return rows
    except psycopg2.Error as e:
        messagebox.showerror("Произошла ошибка", f"Ошибка выполнения SQL-запроса: {e}")
        return None
def execute_sql_query2(query):
    try:
        conn = create_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
    except psycopg2.Error as e:
        messagebox.showerror("Произошла ошибка", f"Ошибка выполнения SQL-запроса: {e}")
# Сортировка таблиц
def sort_table_column(tree, column, descending=False):
    # Получаем данные из столбца
    data = [(tree.set(item, column), item) for item in tree.get_children('')]
    # Пытаемся преобразовать данные в числа (если возможно)
    try:
        data = [(float(value), item) for value, item in data]
    except ValueError:
        pass  # Преобразование не удалось, оставляем значения как строки
    # Сортируем данные
    data.sort(reverse=descending)
    # Перемещаем элементы в Treeview в соответствии с сортировкой
    for index, (value, item) in enumerate(data):
        tree.move(item, '', index)
    # Изменяем направление сортировки для следующего щелчка
    tree.heading(column, command=lambda: sort_table_column(tree, column, not descending))

def export_data_to_file():
    queries = {
        "Animal_data": 'SELECT * FROM "Животное"',
        "Animal_and_Ration_data": 'SELECT * FROM "Животное и рацион"',
        "Breed_data": 'SELECT * FROM "Порода"',
        "Contacts_data": 'SELECT * FROM "Контакты"',
        "Farm_data": 'SELECT * FROM "Ферма"',
        "Food_data": 'SELECT * FROM "Корм"',
        "Food_add_data": 'SELECT * FROM "Кормовые добавки"',
        "Payment_data": 'SELECT * FROM "Схема оплаты"',
        "Post_data": 'SELECT * FROM "Должность"',
        "Purchase_data": 'SELECT * FROM "Закупка"',
        "Ration_data": 'SELECT * FROM "Рацион"',
        "Realization_data": 'SELECT * FROM "Реализация"',
        "Salary_data": 'SELECT * FROM "Зарплата"',
        "Staff_data": 'SELECT * FROM "Сотрудник"',
        "ViewPurchase_data": 'SELECT * FROM "Вид закупки"',
        "ViewRealization_data": 'SELECT * FROM "Вид реализации"',
        "Work_time_data": 'SELECT * FROM "График работы"'
    }
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    if folder_path:
        for table_name, query in queries.items():
            rows = execute_sql_query(query)
            if rows is not None:
                csv_data = "\n".join(["\t".join(map(str, row)) for row in rows])
                file_name = f"{table_name}.txt"
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(csv_data)
# -------Доп окна-----------
#---Животное---
def open_update_window_an():
    def update_parent_combobox(*args):
        selected_breed_id = breed_combobox.get()
        if selected_breed_id:
            sql_family = f"""
                SELECT ID FROM "Животное"
                WHERE ID != {item_values[0]} 
                AND "Животное"."ID породы" IN (
                    SELECT "Порода".ID FROM "Порода" WHERE "Вид животного"=(
                        SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={selected_breed_id}
                    )
                ) 
                AND "Животное".Пол='ж' 
                AND "Животное".Возраст < TIMESTAMP '{item_values[4]}'::TIMESTAMP;
            """
            parent_values = [0] + [row[0] for row in execute_sql_query(sql_family)]
            parent_combobox['values'] = parent_values
            parent_combobox.set('')  # Сбрасываем выбор
    def update_data():
        # Получаем значения только из Entry и Combobox
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))  # Используем cget для Label
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Получаем ID родителя
        parent_id = updated_values[5]
        if parent_id != "0":
            # Получаем ID породы животного
            animal_breed_id = updated_values[1]
            animal_breed_id= execute_sql_query(f"""SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={animal_breed_id};""")[0][0]
            # Получаем возраст и вид родителя
            parent_breed_id= execute_sql_query(f"""SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID=(SELECT "Животное"."ID породы" FROM Животное WHERE ID={parent_id} );""")[0][0]
            parent_age = execute_sql_query(f"""SELECT "Животное"."Возраст" FROM Животное WHERE ID={parent_id};""")[0][0]
            # Проверяем соответствие по породе
            if animal_breed_id != parent_breed_id:
                messagebox.showerror("Ошибка", "Выбранный родитель имеет другую породу.")
                return
            # Получаем возраст животного и преобразуем его в объект datetime.datetime
            animal_age_str = updated_values[4]
            if len(animal_age_str) <= 10:
                # Если длина строки <= 10 (только год, месяц и день), добавляем нули для часов, минут и секунд
                animal_age_str += ' 00:00:00'
            try:
                # Преобразуем строку в объект datetime.datetime
                animal_age = datetime.datetime.strptime(animal_age_str, '%Y-%m-%d %H:%M:%S')
            except:
                messagebox.showerror("Ошибка", "Возраст животного указан не верно")
                return
            # Проверяем, что возраст животного меньше возраста родителя
            if animal_age < parent_age:
                messagebox.showerror("Ошибка", "Возраст животного должен быть меньше возраста родителя.")
                return
        # Формируем SQL-запрос для обновления данных
        sql_update = f"""
            UPDATE "Животное"
            SET "ID породы" = {updated_values[1]},
                "ID фермы" = {updated_values[2]},
                "Пол" = '{updated_values[3]}',
                "Возраст" = '{updated_values[4]}',
                "ID родителя" = {updated_values[5]},
                "Цена" = {updated_values[6]}
            WHERE ID = {updated_values[0]};
        """
        # Выполняем SQL-запрос
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_update)
                    conn.commit()  # Явное подтверждение транзакции
                    init_frame1()
                    bind_frame1_event_handlers()
                    update_window.destroy()  # Закрываем окно после успешного обновления
                    messagebox.showinfo("Успех", "Данные успешно обновлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при обновлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    # Проверяем, есть ли выбранный элемент в таблице
    selected_item = animal_tree.focus()
    if selected_item:
        # Получаем данные выбранного элемента
        item_values = animal_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()  # Захват фокуса
        update_window.title("Изменить данные о животном")
        update_window.geometry("250x400")  # Установите размер по вашему усмотрению
        update_window.resizable(False, False)  # Предотвращение изменения размера окна и развертывание на весь экран
        # Создаем поля для изменения данных
        labels = ("ID", "ID породы", "ID фермы", "Пол", "Возраст", "ID родителя", "Цена")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID" or label_text == "Пол":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            elif label_text == "ID фермы":
                sql_ = """SELECT ID FROM "Ферма";"""
                combo_values = [row[0] for row in execute_sql_query(sql_)]
                farm_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                farm_combobox.grid(row=i, column=1, padx=10, pady=10)
                farm_combobox.set(item_values[i] if item_values[i] is not None else combo_values[0])
                entry_values.append(farm_combobox)
            elif label_text == "ID породы":
                breed_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Порода";""")]
                breed_combobox = ttk.Combobox(update_window, values=breed_values, state="readonly")
                breed_combobox.grid(row=i, column=1, padx=10, pady=10)
                breed_combobox.set(item_values[i] if item_values[i] is not None else breed_values[0])
                breed_combobox.bind("<<ComboboxSelected>>", update_parent_combobox)
                entry_values.append(breed_combobox)
            elif label_text == "ID родителя":
                sql_family = f"""
                              SELECT ID FROM "Животное"
                              WHERE ID != {item_values[0]} 
                              AND "Животное"."ID породы" IN (
                                  SELECT "Порода".ID FROM "Порода" WHERE "Вид животного"=(
                                      SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={item_values[1]}
                                  )
                              ) 
                              AND "Животное".Пол='ж' 
                              AND "Животное".Возраст < TIMESTAMP '{item_values[4]}'::TIMESTAMP;
                          """
                parent_values = [0] + [row[0] for row in execute_sql_query(sql_family)]
                parent_combobox = ttk.Combobox(update_window, values=parent_values, state="readonly")
                parent_combobox.grid(row=i, column=1, padx=10, pady=10)
                parent_combobox.set(item_values[i] if item_values[i] is not None else parent_values[0])
                entry_values.append(parent_combobox)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        # Кнопка для выполнения обновления данных
        update_button = Button(update_window, text="Изменить", command=update_data)
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_an():
    def add_data():
        # Получаем значения только из Entry и Combobox
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))  # Используем cget для Label
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Получаем ID родителя
        parent_id = updated_values[5]
        if parent_id != "0":
            # Получаем ID породы животного
            animal_breed_id = updated_values[1]
            animal_breed_id = execute_sql_query(f"""SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={animal_breed_id};""")[0][0]
            # Получаем возраст и вид родителя
            parent_breed_id = execute_sql_query(
                f"""SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID=(SELECT "Животное"."ID породы" FROM Животное WHERE ID={parent_id} );""")[
                0][0]
            parent_age = execute_sql_query(f"""SELECT "Животное"."Возраст" FROM Животное WHERE ID={parent_id};""")[0][0]
            # Проверяем соответствие по породе
            if animal_breed_id != parent_breed_id:
                messagebox.showerror("Ошибка", "Выбранный родитель имеет другую породу.")
                return
            # Получаем возраст животного и преобразуем его в объект datetime.datetime
            animal_age_str = updated_values[4]
            # Проверяем длину строки времени
            if len(animal_age_str) <= 10:
                # Если длина строки <= 10 (только год, месяц и день), добавляем нули для часов, минут и секунд
                animal_age_str += ' 00:00:00'
            try:
                # Преобразуем строку в объект datetime.datetime
                animal_age = datetime.datetime.strptime(animal_age_str, '%Y-%m-%d %H:%M:%S')
            except:
                messagebox.showerror("Ошибка", "Возраст животного указан не верно")
                return
            # Проверяем, что возраст животного меньше возраста родителя
            if animal_age < parent_age:
                messagebox.showerror("Ошибка", "Возраст животного должен быть меньше возраста родителя.")
                return
        max_id=execute_sql_query('SELECT MAX(ID) FROM "Животное"')
        max_id = max_id[0][0]  # Извлекаем значение из списка
        next_id = max_id + 1 if max_id is not None else 1
        # Формируем SQL-запрос для обновления данных
        sql_insert = f"""
            INSERT INTO "Животное" (ID,"ID породы", "ID фермы", "Пол", "Возраст", "ID родителя", "Цена")
            VALUES( {next_id},{updated_values[1]}, {updated_values[2]}, '{updated_values[3]}', '{updated_values[4]}', {updated_values[5]}, {updated_values[6]});
        """
        # Выполняем SQL-запрос
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert )
                    conn.commit()  # Явное подтверждение транзакции
                    init_frame1()
                    bind_frame1_event_handlers()
                    update_window.destroy()  # Закрываем окно после успешного обновления
                    messagebox.showinfo("Успех", "Данные успешно обновлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при обновлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    def update_parent_combobox(*args):
        selected_breed_id = breed_combobox.get()
        age_value = age_entry.get()
        if age_value==None or age_value=="":
            sql_family = f"""
                            SELECT ID FROM "Животное"
                            WHERE "Животное"."ID породы" IN (
                                SELECT "Порода".ID FROM "Порода" WHERE "Вид животного"=(
                                    SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={selected_breed_id}
                                )
                            ) 
                            AND "Животное".Пол='ж';
                        """
        elif selected_breed_id:
            sql_family = f"""
                 SELECT ID FROM "Животное"
                 WHERE "Животное"."ID породы" IN (
                     SELECT "Порода".ID FROM "Порода" WHERE "Вид животного"=(
                         SELECT "Порода"."Вид животного" FROM "Порода" WHERE ID={selected_breed_id}
                     )
                 ) 
                 AND "Животное".Пол='ж' 
                 AND "Животное".Возраст < TIMESTAMP '{age_value}'::TIMESTAMP;
             """
        parent_values = [0] + [row[0] for row in execute_sql_query(sql_family)]
        parent_combobox['values'] = parent_values
        parent_combobox.set('')  # Сбрасываем выбор
    update_window = Toplevel()
    update_window.grab_set()  # Захват фокуса
    update_window.title("Добавить данные о животном")
    update_window.geometry("250x400")  # Установите размер по вашему усмотрению
    update_window.resizable(False, False)  # Предотвращение изменения размера окна и развертывание на весь экран
    # Создаем поля для изменения данных
    labels = ("ID", "ID породы", "ID фермы", "Пол", "Возраст", "ID родителя", "Цена")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"  # Заполнить пустым значением
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text == "Пол":
            combo_values = ["м","ж"]
            combo_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            combo_combobox.grid(row=i, column=1, padx=10, pady=10)
            entry_values.append( combo_combobox)
        elif label_text == "ID фермы":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Ферма";""")]
            farm_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            farm_combobox.grid(row=i, column=1, padx=10, pady=10)
            farm_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(farm_combobox)
        elif label_text == "ID породы":
            breed_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Порода";""")]
            breed_combobox = ttk.Combobox(update_window, values=breed_values, state="readonly")
            breed_combobox.grid(row=i, column=1, padx=10, pady=10)
            breed_combobox.set("")  # Задать первое значение в списке по умолчанию
            breed_combobox.bind("<<ComboboxSelected>>", update_parent_combobox)
            entry_values.append(breed_combobox)
        elif label_text == "ID родителя":
            parent_combobox = ttk.Combobox(update_window, values=[], state="readonly")
            parent_combobox.grid(row=i, column=1, padx=10, pady=10)
            entry_values.append(parent_combobox)
        elif label_text == "Возраст":
            age_entry = Entry(update_window)
            age_entry.grid(row=4, column=1, padx=10, pady=10)
            age_entry.bind("<FocusOut>", update_parent_combobox)  # Вызов обновления при потере фокуса
            entry_values.append(age_entry)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")  # Заполнить пустым значением
            entry_values.append(entry)
        # Кнопка для выполнения обновления данных
    update_button = Button(update_window, text="Добавить",command=add_data)
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Сотрудник---
def open_update_window_staff():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        inn = updated_values[4]
        if not inn.isdigit():
            messagebox.showerror("Ошибка", "ИНН должен содержать только числовые значения.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Сотрудник" WHERE "ИНН"='{inn}' AND ID!={updated_values[0]};""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Сотрудник с таким ИНН уже существует.")
            return
        sql_update = f"""
              UPDATE "Сотрудник" 
              SET "Фамилия"='{updated_values[1]}', "Имя"='{updated_values[2]}', "Отчество"='{updated_values[3]}', "ИНН"='{updated_values[4]}'
              WHERE ID={updated_values[0]};
          """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(  sql_update )
                    conn.commit()
                    init_frame4()
                    bind_frame4_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = staff_tree.focus()
    if selected_item:
        # Получаем данные выбранного элемента
        item_values = staff_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о сотруднике")
        update_window.geometry("220x300")
        update_window.resizable(False, False)
        labels = ("ID", "Фамилия", "Имя", "Отчество", "ИНН")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        # Кнопка для выполнения обновления данных
        update_button = Button(update_window, text="Изменить",command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_staff():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        inn = updated_values[4]
        if not inn.isdigit():
            messagebox.showerror("Ошибка", "ИНН должен содержать только числовые значения.")
            return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Сотрудник" WHERE "ИНН"='{inn}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Сотрудник с таким ИНН уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Сотрудник"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Сотрудник" (ID,"Фамилия", "Имя", "Отчество", "ИНН")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}', '{updated_values[4]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame4()
                    bind_frame4_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о сотруднике")
    update_window.geometry("220x300")
    update_window.resizable(False, False)
    labels = ("ID", "Фамилия", "Имя","Отчество", "ИНН")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить",command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Контакты---
def open_update_window_contacs():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        tel = updated_values[1]
        if not tel.isdigit():
            messagebox.showerror("Ошибка", "Телефон должен содержать только числовые значения.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Контакты" WHERE "Телефон"='{updated_values[1]}' AND "ID сотрудника"!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Контакт с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Контакты" SET "Телефон"='{updated_values[1]}' WHERE "ID сотрудника"='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame7()
                    bind_frame7_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = contacts_tree.focus()
    if selected_item:
        item_values =contacts_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о контактах")
        update_window.geometry("270x150")
        update_window.resizable(False, False)
        labels = ("ID сотрудника", "Телефон")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text =="ID сотрудника":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_contacs():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        tel = updated_values[1]
        if not tel.isdigit():
            messagebox.showerror("Ошибка", "Телефон должен содержать только числовые значения.")
            return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Контакты" WHERE "Телефон"='{updated_values[1]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Контакт с такими данными уже существует.")
            return
        sql_insert = f"""
            INSERT INTO "Контакты" ("ID сотрудника","Телефон")
            VALUES ( '{updated_values[0]}', '{updated_values[1]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame7()
                    bind_frame7_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о контактах")
    update_window.geometry("270x150")
    update_window.resizable(False, False)
    labels = ("ID сотрудника", "Телефон")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---График работы---
def open_update_window_work_time():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values[:-1]  # Все поля кроме последнего (Примечание)
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'
            elif len(updated_values[3]) == 5 or len(updated_values[3]) == 4:
                updated_values[3] += ':00'
            if updated_values[2] >= updated_values[3]:
                messagebox.showerror("Ошибка", "Время начала должно быть меньше времени окончания.")
                return  
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "График работы" WHERE "Дни недели"='{updated_values[1]}' AND "Время начала"='{updated_values[2]}' AND  "Время окончания"='{updated_values[3]}' AND "ID сотрудника"='{updated_values[4]}' AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "График с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "График работы" SET "Дни недели"='{updated_values[1]}', "Время начала"='{updated_values[2]}', "Время окончания"='{updated_values[3]}', "ID сотрудника"='{updated_values[4]}', "Примечание"='{updated_values[5]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame14()
                    bind_frame14_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = work_time_tree.focus()
    if selected_item:
        # Получаем данные выбранного элемента
        item_values = work_time_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о графике")
        update_window.geometry("290x300")
        update_window.resizable(False, False)
        labels = ("ID", "Дни недели", "Время начала", "Время окончания", "ID сотрудника", "Примечание")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID" or label_text =="ID сотрудника":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        # Кнопка для выполнения обновления данных
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_work_time():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values[:-1]  # Все поля кроме последнего (Примечание)
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'
            elif len(updated_values[3]) == 5 or len(updated_values[3]) == 4:
                updated_values[3] += ':00'
            if updated_values[2] >= updated_values[3]:
                messagebox.showerror("Ошибка", "Время начала должно быть меньше времени окончания.")
                return  
        except ValueError:
            messagebox.showerror("Ошибка","Неверный формат времени. Ожидается формат HH:MM:SS.")

        existing_employee = execute_sql_query(f"""SELECT * FROM "График работы" WHERE "Дни недели"='{updated_values[1]}' AND "Время начала"='{updated_values[2]}' AND  "Время окончания"='{updated_values[3]}' AND "ID сотрудника"='{updated_values[4]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "График с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "График работы"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "График работы" (ID, "Дни недели", "Время начала", "Время окончания", "ID сотрудника","Примечание")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}', '{updated_values[4]}', '{updated_values[5]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame14()
                    bind_frame14_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о графике")
    update_window.geometry("290x300")
    update_window.resizable(False, False)
    labels = ("ID", "Дни недели", "Время начала", "Время окончания", "ID сотрудника","Примечание")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text =="ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Порода---
def open_update_window_breed():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values[:2] + updated_values[3:]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что все поля, кроме первого, содержат только буквы
        for value in required_values[1:]:
            if not value.isalpha():
                messagebox.showerror("Ошибка", "Ошибка синтаксиса")
                return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Порода" WHERE "Название"='{updated_values[1]}' AND "Вид животного"='{updated_values[3]}' AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Порода с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Порода" SET "Название"='{updated_values[1]}', "Описание"='{updated_values[2]}', "Вид животного"='{updated_values[3]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame2()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = breed_tree.focus()
    if selected_item:
        item_values = breed_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о породе")
        update_window.geometry("250x250")
        update_window.resizable(False, False)
        labels = ("ID", "Название", "Описание", "Вид животного")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_breed():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values[:2] + updated_values[3:]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что все поля, кроме первого, содержат только буквы
        for value in required_values[1:]:
            if not value.isalpha():
                messagebox.showerror("Ошибка", "Ошибка синтаксиса")
                return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Порода" WHERE "Название"='{updated_values[1]}' AND "Вид животного"='{updated_values[3]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Порода с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Порода"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Порода" (ID, "Название", "Описание", "Вид животного")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame2()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о графике")
    update_window.geometry("250x250")
    update_window.resizable(False, False)
    labels = ("ID", "Название", "Описание", "Вид животного")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Ферма---
def open_update_window_farm():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что второй столбец содержит только буквы
        if not all(char.isalpha() or char.isspace() for char in updated_values[1]):
            messagebox.showerror("Ошибка", "Ошибка синтаксиса")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Ферма" WHERE ("Название фермы"='{updated_values[1]}' or "Местоположение"='{updated_values[2]}') AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Ферма с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Ферма" SET "Название фермы"='{updated_values[1]}', "Местоположение"='{updated_values[2]}', "Площадь (Га)"='{updated_values[3]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame3()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = farm_tree.focus()
    if selected_item:
        item_values = farm_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о Ферме")
        update_window.geometry("250x250")
        update_window.resizable(False, False)
        labels = ("ID", "Название фермы", "Местоположение", "Площадь (Га)")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_farm():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что второй столбец содержит только буквы
        if not all(char.isalpha() or char.isspace() for char in updated_values[1]):
            messagebox.showerror("Ошибка", "Ошибка синтаксиса")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Ферма" WHERE ("Название фермы"='{updated_values[1]}' or "Местоположение"='{updated_values[2]}');""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Ферма с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Ферма"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Ферма" (ID, "Название фермы", "Местоположение", "Площадь (Га)")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame3()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о Ферме")
    update_window.geometry("250x250")
    update_window.resizable(False, False)
    labels =  ("ID", "Название фермы", "Местоположение", "Площадь (Га)")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Корм---
def open_update_window_food():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Корм" WHERE ("Название"='{updated_values[1]}' and "Описание"='{updated_values[2]}') AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Корм с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Корм" SET "Название"='{updated_values[1]}', "Описание"='{updated_values[2]}', "Цена"='{updated_values[3]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame8()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = food_tree.focus()
    if selected_item:
        item_values = food_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о Корме")
        update_window.geometry("250x250")
        update_window.resizable(False, False)
        labels = ("ID", "Название", "Описание", "Цена")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_food():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Корм" WHERE ("Название"='{updated_values[1]}' and "Описание"='{updated_values[2]}');""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Корм с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Корм"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Корм" (ID, "Название", "Описание", "Цена")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame8()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о Ферме")
    update_window.geometry("250x250")
    update_window.resizable(False, False)
    labels =   ("ID", "Название", "Описание", "Цена")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Кормовые добавки---
def open_update_window_foodadd():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Кормовые добавки" WHERE ("Название"='{updated_values[1]}' and "Описание"='{updated_values[2]}') AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Кормовые добавки с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Кормовые добавки" SET "Название"='{updated_values[1]}', "Описание"='{updated_values[2]}', "Цена"='{updated_values[3]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame9()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = food_add_tree.focus()
    if selected_item:
        item_values = food_add_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о Кормовых добавок")
        update_window.geometry("250x250")
        update_window.resizable(False, False)
        labels = ("ID", "Название", "Описание", "Цена")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)

        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_foodadd():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
            # Проверка, что все поля кроме примечания заполнены
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        # Проверка, что последний столбец содержит только цифры
        if not updated_values[-1].isdigit():
            messagebox.showerror("Ошибка", "Последний столбец должен содержать только цифры.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Кормовые добавки" WHERE ("Название"='{updated_values[1]}' and "Описание"='{updated_values[2]}');""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Кормовые добавки с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Кормовые добавки"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Кормовые добавки" (ID, "Название", "Описание", "Цена")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame9()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о Кормовых добавок")
    update_window.geometry("250x250")
    update_window.resizable(False, False)
    labels =   ("ID", "Название", "Описание", "Цена")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Зарплата---
def open_update_window_salary():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))

        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        sum = updated_values[2]
        if not sum.isdigit():
            messagebox.showerror("Ошибка", "Ошибка синтаксиса")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Зарплата" WHERE "Тип оплаты"='{updated_values[1]}' AND "Сумма"='{updated_values[2]}' AND "ID схемы"!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Зарплата с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Зарплата" SET "Тип оплаты"='{updated_values[1]}', "Сумма"='{updated_values[2]}' WHERE "ID схемы"='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame10()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = salary_tree.focus()
    if selected_item:
        item_values =salary_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о зарплате")
        update_window.geometry("260x200")
        update_window.resizable(False, False)
        labels = ("ID схемы", "Тип оплаты","Сумма")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text =="ID схемы":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            elif label_text == "Тип оплаты":
                combo_values = ["безналичный", "наличный", "бонус"]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i, column=1, padx=10, pady=10)
                staff_combobox.set( item_values[i] if item_values[i] is not None else "")
                entry_values.append(staff_combobox)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_salary():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        sum = updated_values[2]
        if not  sum.isdigit():
            messagebox.showerror("Ошибка", "Ошибка синтаксиса")
            return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Зарплата" WHERE "Тип оплаты"='{updated_values[1]}' AND "Сумма"='{updated_values[2]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Зарплата с такими данными уже существует.")
            return
        sql_insert = f"""
            INSERT INTO "Зарплата" ("ID схемы", "Тип оплаты","Сумма")
            VALUES ( '{updated_values[0]}', '{updated_values[1]}', '{updated_values[2]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame10()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о зарплате")
    update_window.geometry("260x200")
    update_window.resizable(False, False)
    labels = ("ID схемы", "Тип оплаты", "Сумма")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID схемы":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Схема оплаты";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "Тип оплаты":
            combo_values = ["безналичный","наличный","бонус"]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Закупка---
def open_update_window_purchase():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values[:-1]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
        sql_insert = f"""
            UPDATE "Закупка" SET "Дата"='{updated_values[2]}', "Примечания"='{updated_values[3]}' WHERE ID='{updated_values[0]}' and "ID сотрудника"='{updated_values[1]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame11()
                    bind_frame11_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = pursh_tree.focus()
    if selected_item:
        # Получаем данные выбранного элемента
        item_values = pursh_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о закупках")
        update_window.geometry("290x300")
        update_window.resizable(False, False)
        labels = ("ID", "ID сотрудника", "Дата", "Примечания")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID" or label_text =="ID сотрудника":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        # Кнопка для выполнения обновления данных
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_purchase():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values[:-1]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'
        except ValueError:
            messagebox.showerror("Ошибка","Неверный формат времени. Ожидается формат HH:MM:SS.")
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Закупка"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Закупка" (ID, "ID сотрудника", "Дата", "Примечания")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame11()
                    bind_frame11_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о закупках")
    update_window.geometry("290x300")
    update_window.resizable(False, False)
    labels = ("ID", "ID сотрудника", "Дата", "Примечания")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text =="ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Реализация---
def open_update_window_real():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
        sql_insert = f"""
            UPDATE "Реализация" SET "Дата"='{updated_values[2]}' WHERE ID='{updated_values[0]}' and "ID сотрудника"='{updated_values[1]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame12()
                    bind_frame12_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item =real_tree.focus()
    if selected_item:
        # Получаем данные выбранного элемента
        item_values = real_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о реализации")
        update_window.geometry("290x300")
        update_window.resizable(False, False)
        labels = ("ID", "ID сотрудника", "Дата")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID" or label_text =="ID сотрудника":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        # Кнопка для выполнения обновления данных
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_real():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[2]) == 5 or len(updated_values[2]) == 4:
                updated_values[2] += ':00'

        except ValueError:
            messagebox.showerror("Ошибка","Неверный формат времени. Ожидается формат HH:MM:SS.")
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Реализация"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Реализация" (ID, "ID сотрудника", "Дата")
            VALUES ( {next_id},'{updated_values[1]}', '{updated_values[2]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame12()
                    bind_frame12_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о реализации")
    update_window.geometry("290x300")
    update_window.resizable(False, False)
    labels = ("ID", "ID сотрудника", "Дата")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text =="ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Схема оплаты---
def open_add_window_payment():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Схема оплаты"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Схема оплаты" (ID,"ID сотрудника")
            VALUES ( {next_id},'{updated_values[1]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame13()
                    bind_frame13_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о схеме оплаты")
    update_window.geometry("290x300")
    update_window.resizable(False, False)
    labels = ("ID", "ID сотрудника")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID" :
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text =="ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Должность---
def open_update_window_post():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values[:-1]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        if updated_values[4]==None or updated_values[4]=="":
            updated_values[4]="infinity"
        try:
            if len(updated_values[3]) == 5 or len(updated_values[3]) == 4:
                updated_values[3] += ':00'
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Должность" WHERE "ID сотрудника"='{updated_values[0]}' and "ID фермы"='{updated_values[1]}' AND "Должность"='{updated_values[2]}' AND "Стаж"='{updated_values[3]}' AND "Дата увольнения"='{updated_values[4]}' ;""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Должность с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Должность" SET "Дата увольнения"='{updated_values[4]}' WHERE  "ID сотрудника"='{updated_values[0]}' and "ID фермы"='{updated_values[1]}' AND "Должность"='{updated_values[2]} AND  "Стаж"='{updated_values[3]}'';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame15()
                    bind_frame15_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = post_tree.focus()
    if selected_item:
        item_values = post_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о должности")
        update_window.geometry("280x250")
        update_window.resizable(False, False)
        labels = ("ID сотрудника", "ID фермы", "Должность", "Стаж", "Дата увольнения")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text == "ID сотрудника" or label_text == "ID фермы" or label_text == "Должность" or label_text == "Стаж":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_post():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        required_values = updated_values[:-1]
        if any(value.strip() == "" for value in required_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        try:
            if len(updated_values[3]) == 5 or len(updated_values[3]) == 4:
                updated_values[3] += ':00'
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
        if updated_values[4] == None or updated_values[4] == "":
            updated_values[4] = "infinity"
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Должность" WHERE "ID сотрудника"='{updated_values[0]}' and "ID фермы"='{updated_values[1]}' AND "Должность"='{updated_values[2]}' AND "Стаж"='{updated_values[3]}' AND "Дата увольнения"='{updated_values[4]}' ;""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Должность с такими данными уже существует.")
            return
        sql_insert = f"""
            INSERT INTO "Должность" ("ID сотрудника", "ID фермы", "Должность", "Стаж", "Дата увольнения")
            VALUES ({updated_values[0]}, '{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}', '{updated_values[4]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame15()
                    bind_frame15_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о должности")
    update_window.geometry("280x250")
    update_window.resizable(False, False)
    labels = ("ID сотрудника", "ID фермы", "Должность", "Стаж", "Дата увольнения")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID сотрудника":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Сотрудник";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "ID фермы":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Ферма";""")]
            farm_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            farm_combobox.grid(row=i, column=1, padx=10, pady=10)
            farm_combobox.set("")  # Задать первое значение в списке по умолчанию
            entry_values.append(farm_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Рацион---
def open_update_window_ration():
    def update_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        existing_employee = execute_sql_query(
            f"""SELECT * FROM "Рацион" WHERE "ID корма"='{updated_values[1]}' AND "ID кормовых добавок"='{updated_values[2]}' AND ID!='{updated_values[0]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Рацион с такими данными уже существует.")
            return
        sql_insert = f"""
            UPDATE "Рацион" SET "ID корма"='{updated_values[1]}', "ID кормовых добавок"='{updated_values[2]}' WHERE ID='{updated_values[0]}';
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame17()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    selected_item = ration_tree.focus()
    if selected_item:
        item_values =ration_tree.item(selected_item, "values")
        update_window = Toplevel()
        update_window.grab_set()
        update_window.title("Добавить данные о рационе")
        update_window.geometry("310x200")
        update_window.resizable(False, False)
        labels = ("ID", "ID корма","ID кормовых добавок")
        entry_values = []
        for i, label_text in enumerate(labels):
            label = Label(update_window, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=10)
            if label_text =="ID":
                label_value = item_values[i] if item_values[i] is not None else ""
                label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
                label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
                entry_values.append(label)
            elif label_text == "ID корма":
                combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Корм";""")]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i, column=1, padx=10, pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
            elif label_text == "ID кормовых добавок":
                combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Кормовые добавки";""")]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i, column=1, padx=10, pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
            else:
                entry = Entry(update_window)
                entry.grid(row=i, column=1, padx=10, pady=10)
                entry.insert(0, item_values[i] if item_values[i] is not None else "")
                entry_values.append(entry)
        update_button = Button(update_window, text="Изменить", command=lambda: update_data(entry_values))
        update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    else:
        messagebox.showinfo("Нет выбранного элемента", "Пожалуйста, выберите элемент из таблицы перед изменением.")
def open_add_window_ration():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Рацион" WHERE "ID корма"='{updated_values[1]}' AND "ID кормовых добавок"='{updated_values[2]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Рацион с такими данными уже существует.")
            return
        max_id = execute_sql_query('SELECT MAX(ID) FROM "Рацион"')
        max_id = max_id[0][0]
        next_id = max_id + 1 if max_id is not None else 1
        sql_insert = f"""
            INSERT INTO "Рацион" (ID,"ID корма", "ID кормовых добавок")
            VALUES ( '{next_id}', '{updated_values[1]}', '{updated_values[2]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame17()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о рационе")
    update_window.geometry("310x200")
    update_window.resizable(False, False)
    labels = ("ID", "ID корма", "ID кормовых добавок")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID":
            label_value = "DEFAULT"
            label = Label(update_window, text=label_value, relief="sunken", borderwidth=2)
            label.grid(row=i, column=1, padx=10, pady=10, sticky="we")
            entry_values.append(label)
        elif label_text == "ID корма":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Корм";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "ID кормовых добавок":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Кормовые добавки";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Животное и рацион---
def open_add_window_AN_ration():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        existing_employee = execute_sql_query(f"""SELECT * FROM "Животное и рацион" WHERE "ID животного"='{updated_values[0]}' AND "ID рациона"='{updated_values[1]}';""")
        if existing_employee:
            messagebox.showerror("Ошибка", "Рацион и животное с такими данными уже существует.")
            return
        sql_insert = f"""
            INSERT INTO "Животное и рацион" ( "ID животного","ID рациона")
            VALUES (  '{updated_values[0]}', '{updated_values[1]}');
        """
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame16()
                    bind_frame16_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о рационе животного")
    update_window.geometry("310x200")
    update_window.resizable(False, False)
    labels = ("ID животного","ID рациона")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID животного":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Животное";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "ID рациона":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Рацион";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Вид закупки---
def open_add_window_view_purchase():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        if updated_values[0]=="0" or (updated_values[1]=="0" and updated_values[2]=="0" and updated_values[3]=="0" and updated_values[4]=="0" and updated_values[5]=="0")  or (updated_values[2]!="0" and updated_values[4]=="0") or (updated_values[3]!=0 and updated_values[5]==0) or (updated_values[2]=="0" and updated_values[4]!="0") or (updated_values[3]==0 and updated_values[5]!=0):
            messagebox.showerror("Ошибка", "Закупка не может быть пустой")
            return
        existing_employee = execute_sql_query (f"""
        SELECT * FROM "Вид закупки"
        WHERE "ID закупки" = '{updated_values[0]}'
        AND "ID животного" = '{updated_values[1]}'
        AND "ID корма" = '{updated_values[2]}'
        AND "ID кормовых добавок" = '{updated_values[3]}'
        AND "Кол-во корма" = '{updated_values[4]}'
        AND "Кол-во кормовых добавок" = '{updated_values[5]}'
    """)
        if existing_employee:
            messagebox.showerror("Ошибка", "Вид закупки с такими данными уже существует.")
            return
        sql_insert =(f"""
        INSERT INTO "Вид закупки" ("ID закупки", "ID животного", "ID корма", "ID кормовых добавок", "Кол-во корма", "Кол-во кормовых добавок")
        VALUES ('{updated_values[0]}', '{updated_values[1]}', '{updated_values[2]}', '{updated_values[3]}', '{updated_values[4]}', '{updated_values[5]}')
    """)
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame5()
                    bind_frame5_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о закупки")
    update_window.geometry("360x300")
    update_window.resizable(False, False)
    labels = ("ID закупки", "ID животного", "ID корма", "ID кормовых добавок", "Кол-во корма", "Кол-во кормовых добавок")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID животного":
            combo_values = [0] + [row[0] for row in execute_sql_query("""SELECT ID FROM "Животное";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set(0)
            entry_values.append(staff_combobox)
        elif label_text == "ID корма":
            combo_values = [0] + [row[0] for row in execute_sql_query("""SELECT ID FROM "Корм";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set(0)
            entry_values.append(staff_combobox)
        elif label_text == "ID закупки":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Закупка";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "ID кормовых добавок":
            combo_values = [0] + [row[0] for row in execute_sql_query("""SELECT ID FROM "Кормовые добавки";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set(0)
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "0")  # Вставка значения "0" в поле ввода
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---Вид реализации---
def open_add_window_viewreal():
    def add_data(entry_values):
        updated_values = []
        for entry in entry_values:
            if isinstance(entry, Entry) or isinstance(entry, ttk.Combobox):
                updated_values.append(entry.get())
            else:
                updated_values.append(entry.cget("text"))
        if any(value.strip() == "" for value in  updated_values):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return
        existing_employee = execute_sql_query (f"""
        SELECT * FROM "Вид реализации"
        WHERE "ID животного" = '{updated_values[1]}';
    """)
        if existing_employee:
            messagebox.showerror("Ошибка", "Такое животное уже было продано")
            return
        sql_insert =(f"""
        INSERT INTO "Вид реализации" ("ID реализации", "ID животного")
        VALUES ('{updated_values[0]}', '{updated_values[1]}')
    """)
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("Не удалось подключиться к базе данных")
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_insert)
                    conn.commit()
                    init_frame6()
                    bind_frame6_event_handlers()
                    update_window.destroy()
                    messagebox.showinfo("Успех", "Данные успешно добавлены")
        except psycopg2.Error as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Добавить данные о виде реализации")
    update_window.geometry("280x180")
    update_window.resizable(False, False)
    labels = ("ID реализации", "ID животного")
    entry_values = []
    for i, label_text in enumerate(labels):
        label = Label(update_window, text=label_text)
        label.grid(row=i, column=0, padx=10, pady=10)
        if label_text == "ID животного":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Животное";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        elif label_text == "ID реализации":
            combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Реализация";""")]
            staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
            staff_combobox.grid(row=i, column=1, padx=10, pady=10)
            staff_combobox.set("")
            entry_values.append(staff_combobox)
        else:
            entry = Entry(update_window)
            entry.grid(row=i, column=1, padx=10, pady=10)
            entry.insert(0, "")  # Вставка значения "0" в поле ввода
            entry_values.append(entry)
    update_button = Button(update_window, text="Добавить", command=lambda: add_data(entry_values))
    update_button.grid(row=len(labels), column=0, columnspan=2, padx=10, pady=10, sticky="ew")
# ----------ОТЧЕТЫ--------
#---ОТЧЕТ ЗАТРАТЫ---
def generate_report_to_file(animal_type_id,feed_id, supplement_id, date_from,date_to, file_path):
    try:
        with psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm') as conn:
            with conn.cursor() as cur:
                sql_query_base = """
                                    SELECT 
                                        COALESCE("Сотрудник".Фамилия, 'нет данных') AS Фамилия,
                                        COALESCE("Сотрудник".Имя, 'нет данных') AS Имя,
                                        COALESCE("Сотрудник".Отчество, 'нет данных') AS Отчество,
                                        TO_CHAR("Закупка".Дата, 'DD.MM.YYYY') AS Дата,
                                        COALESCE(Порода."Название", 'нет данных') AS "Название породы",
                                        COALESCE(Порода."Вид животного", 'нет данных') AS "Вид животного",
                                        COALESCE("Животное"."Цена", 0) AS "Цена Животного",
                                        COALESCE(Корм.Название, 'нет данных') AS "Корм",
                                        COALESCE(SUM("Вид закупки"."Кол-во корма" * "Корм".Цена), 0) AS "Общая цена корма",
                                        COALESCE("Кормовые добавки".Название, 'нет данных') AS "Кормовые добавки",
                                        COALESCE(SUM("Кормовые добавки".Цена * "Вид закупки"."Кол-во кормовых добавок"), 0) AS "Общая цена корм. доб.",
                                        COALESCE("Животное"."Цена", 0) 
                                            + COALESCE(SUM("Вид закупки"."Кол-во корма" * "Корм".Цена), 0)
                                            + COALESCE(SUM("Кормовые добавки".Цена * "Вид закупки"."Кол-во кормовых добавок"), 0) AS "Общая стоимость закупки"
                                    FROM 
                                        "Вид закупки"
                                    LEFT JOIN 
                                        "Животное" ON "Вид закупки"."ID животного" = "Животное".ID
                                    LEFT JOIN 
                                        "Закупка" ON "Вид закупки"."ID закупки" = "Закупка".ID
                                    LEFT JOIN 
                                        "Сотрудник" ON "Закупка"."ID сотрудника" = "Сотрудник".ID
                                    LEFT JOIN 
                                        "Корм" ON "Вид закупки"."ID корма" = "Корм".ID
                                    LEFT JOIN 
                                        Порода ON Животное."ID породы" = Порода.id
                                    LEFT JOIN 
                                        "Кормовые добавки" ON "Вид закупки"."ID кормовых добавок" = "Кормовые добавки".ID
                                """
                params = []
                sql_query = sql_query_base + " WHERE 1=1 AND ("
                if date_from and date_to:
                    sql_query += '("Закупка".Дата BETWEEN %s AND %s) AND '
                    params.extend([date_from, date_to])
                else:
                    sql_query += '("Закупка".Дата IS NOT NULL) AND '
                if feed_id is not None:
                    sql_query += '("Корм".ID = %s) OR '
                    params.append(feed_id)
                if supplement_id is not None:
                    sql_query += '("Кормовые добавки".ID = %s) OR '
                    params.append(supplement_id)
                if animal_type_id is not None:
                    sql_query += '("Порода"."Вид животного" = %s) OR '
                    params.append(animal_type_id)
                sql_query = sql_query[:-4] + ")"
                sql_query += """
                                   GROUP BY 
                                       "Сотрудник".Фамилия, 
                                       "Сотрудник".Имя,
                                       "Сотрудник".Отчество,
                                       "Закупка".Дата,
                                       "Животное"."Цена",
                                       Порода."Название",
                                       Порода."Вид животного",
                                       "Корм".Название,
                                       "Кормовые добавки".Название
                               """
                cur.execute(sql_query, tuple(params))
                rows = cur.fetchall()
                with open(file_path, 'w') as file:
                    splits = "{:<5} {:<15} {:<15} {:<15} {:<20} {:<20} {:<15} {:<15} {:<15} {:<15} {:<15} {:<20} {:<20}"
                    file.write("Отчет о закупках\n")
                    if date_from and date_to:
                        file.write(f"Период: {date_from} - {date_to}\n")
                    else:
                        file.write("Период: весь период\n")
                    if feed_id:
                        file.write(f"Корм:{feed_id}\n")
                    if supplement_id:
                        file.write(f"Кормовые добавки:{supplement_id}\n")
                    if animal_type_id:
                        file.write(f"Животное:{animal_type_id}\n")
                    file.write("\n")
                    file.write(splits.format(
                        "№", "Фамилия", "Имя", "Отчество", "Дата", "Название породы", "Вид животного", "Животное",
                        "Корм", "Корм цена", "Корм. доб.", "Корм. доб. цена", "Сумма по группе") + "\n")
                    file.write("-" * 220 + "\n")
                    row_num = 1
                    total_cost = 0
                    prev_surname = None
                    prev_name = None
                    prev_patronymic = None
                    total_cost_group = 0
                    for row in rows:
                        surname, name, patronymic, date, breed_name, animal_type, animal_price, food, food_price, supplement, supplement_price, total_price = row
                        if (surname, name, patronymic) != (prev_surname, prev_name, prev_patronymic):
                            if prev_surname is not None:
                                file.write(splits.format(
                                    "", "", "", "", "", "", "", "", "", "", "", "", f"{total_cost_group:>15}") + "\n")
                                file.write("-" * 220 + "\n")
                                total_cost_group = 0
                        file.write(splits.format( row_num, surname if surname != prev_surname else "", name if name != prev_name else "",
                            patronymic if patronymic != prev_patronymic else "", date, breed_name, animal_type,
                            f"{animal_price:>5}", f"{food:>5}", f"{food_price:>5}", f"{supplement:>5}",
                            f"{supplement_price:>5}", f"{total_price:>15}") + "\n")
                        total_cost_group += total_price
                        total_cost += total_price
                        prev_surname, prev_name, prev_patronymic = surname, name, patronymic
                        row_num += 1
                    if prev_surname is not None:
                        file.write(splits.format(
                            "", "", "", "", "", "", "", "", "", "", "", "", f"{total_cost_group:>15}") + "\n")
                        file.write("-" * 220 + "\n")
                    file.write(f"ИТОГО: {total_cost:>10}\n")
                    messagebox.showinfo("Успех", "Отчет успешно сформирован")
    except Exception as e:
        messagebox.showerror("Ошибка", 'Ошибка подключения:', e)
def open_OTCHET_zatraty():
    def click_create():
        values = []
        for widget in entry_values:
            value = widget.get()
            if value == "":
                values.append(None)
            else:
                values.append(value)
        if values[3] is not None and values[4] is not None:
            try:
                if len(values[3]) in [4, 5]:
                    values[3] += ':00'
                if len(values[4]) in [4, 5]:
                    values[4] += ':00'
                if values[3] >= values[4]:
                    messagebox.showerror("Ошибка", "Неверно указано время.")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
                return
        update_window.destroy()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            generate_report_to_file(values[0], values[1], values[2], values[3], values[4], file_path)
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Отчет о затратах")
    update_window.geometry("310x280")
    update_window.resizable(False, False)
    labels = ("Вид животного", "ID корма", "ID кормовых добавок", "Период")
    entry_values = []
    for i, label_text in enumerate(labels):
        if label_text == "Период":
            label = Label(update_window, text=label_text)
            label.grid(row=i+2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
            period1_entry = Entry(update_window)
            period1_entry.grid(row=i + 3, column=0, padx=1, pady=5)
            period2_entry = Entry(update_window)
            period2_entry.grid(row=i + 3, column=1, padx=1, pady=5)
            entry_values.append(period1_entry)
            entry_values.append(period2_entry)
        else:
            label = Label(update_window, text=label_text)
            label.grid(row=i + 1, column=0, padx=10, pady=10)
            if label_text == "Вид животного":
                query_result = execute_sql_query("""SELECT DISTINCT "Вид животного" FROM "Порода";""")
                combo_values = [row[0] for row in query_result]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i + 1, column=1, padx=10, pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
            elif label_text == "ID корма":
                combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Корм";""")]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i + 1, column=1, padx=10, pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
            elif label_text == "ID кормовых добавок":
                combo_values = [row[0] for row in execute_sql_query("""SELECT ID FROM "Кормовые добавки";""")]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i + 1, column=1, padx=10, pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
    update_button = Button(update_window, text="Создать", command=click_create)
    update_button.grid(row=len(labels) + 4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---ОТЧЕТ ПРИБЫЛЬ---
def generate_report2_to_file(staff, date_from, date_to, file_path):
    try:
        with psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm') as conn:
            with conn.cursor() as cur:
                sql_query_base = """
                    SELECT Сотрудник.Фамилия, Сотрудник.Имя, Сотрудник.Отчество,
                           Животное.ID AS "ID животного",
                           "Реализация"."Дата" AS "Дата реализации",
                           Животное.Цена AS "Цена животного",
                           Порода."Вид животного" AS "Вид животного"
                    FROM Животное 
                    JOIN "Вид реализации" ON "Вид реализации"."ID животного" = Животное.ID 
                    JOIN "Реализация" ON "Вид реализации"."ID реализации" = "Реализация".id 
                    JOIN Порода ON Животное."ID породы" = Порода.ID
                    JOIN Сотрудник ON "Реализация"."ID сотрудника" = Сотрудник.ID
                    WHERE 1=1
                """
                params = []
                if date_from and date_to:
                    sql_query_base += ' AND "Реализация"."Дата" BETWEEN %s AND %s'
                    params.extend([date_from, date_to])
                if staff is not None:
                    sql_query_base += ' AND "Реализация"."ID сотрудника" = %s'
                    params.append(staff)

                cur.execute(sql_query_base, tuple(params))
                rows = cur.fetchall()
                with open(file_path, 'w') as file:
                    splits = "{:<5} {:<15} {:<15} {:<15} {:<15} {:<15} {:>20} {:>20}"
                    file.write("Отчет о реализации животных\n")
                    if date_from and date_to:
                        file.write(f"Период: {date_from} - {date_to}\n")
                    else:
                        file.write("Период: весь период\n")
                    if staff:
                        file.write(f"Сотрудник: {staff}\n")
                    file.write("\n")
                    file.write(splits.format("№", "Фамилия", "Имя", "Отчество", "ID животного", "Дата реализации",
                                             "Цена животного", "Вид животного") + "\n")
                    file.write("-" * 130 + "\n")
                    row_num = 1
                    total_cost = 0
                    prev_surname = None
                    prev_name = None
                    prev_patronymic = None
                    total_cost_group = 0
                    for row in rows:
                        surname, name, patronymic, animal_id, date, animal_price, animal_type = row
                        if (surname, name, patronymic) != (prev_surname, prev_name, prev_patronymic):
                            if prev_surname is not None:
                                file.write(splits.format("", "", "", "", "","", f"{total_cost_group:>15}",  "") + "\n")
                                file.write("-" * 130 + "\n")
                                total_cost_group = 0
                        formatted_date = date.strftime("%d.%m.%Y")
                        file.write(splits.format(row_num, surname if surname != prev_surname else "",
                                                 name if name != prev_name else "",
                                                 patronymic if patronymic != prev_patronymic else "", animal_id, formatted_date,
                                                 f"{animal_price:>20}", animal_type) + "\n")
                        total_cost_group += animal_price
                        total_cost += animal_price
                        prev_surname, prev_name, prev_patronymic = surname, name, patronymic
                        row_num += 1
                    if prev_surname is not None:
                        file.write(splits.format("", "", "", "", "","", f"{total_cost_group:>15}",  "") + "\n")
                        file.write("-" * 130 + "\n")
                    file.write(f"ИТОГО: {total_cost:>20}\n")
                    messagebox.showinfo("Успех", "Отчет успешно сформирован")
    except Exception as e:
        messagebox.showerror("Ошибка", f'Ошибка подключения: {e}')
def open_OTCHET_pribyl():
    def click_create():
        values = []
        for widget in entry_values:
            if isinstance(widget, tuple):
                for entry in widget:
                    value = entry.get()
                    if value == "":
                        values.append(None)
                    else:
                        values.append(value)
            else:
                value = widget.get()
                if value == "":
                    values.append(None)
                else:
                    values.append(value)
        if values[1] is not None and values[2] is not None:
            try:
                if len(values[1]) in [4, 5]:
                    values[1] += ':00'
                if len(values[2]) in [4, 5]:
                    values[2] += ':00'
                if values[1] >= values[2]:
                    messagebox.showerror("Ошибка", "Неверно указано время.")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
                return
        update_window.destroy()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            generate_report2_to_file(values[0], values[1], values[2], file_path)
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Отчет о реализации")
    update_window.geometry("275x180")
    update_window.resizable(False, False)
    labels = ("Сотрудник", "Период")
    # Список для хранения значений ввода
    entry_values = []
    # Цикл по меткам
    for i, label_text in enumerate(labels):
        if label_text == "Период":
            # Создание метки для периода
            label = Label(update_window, text=label_text)
            label.grid(row=i + 1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
            # Создание полей ввода для периода 1 и периода 2
            period1_entry = Entry(update_window)
            period1_entry.grid(row=i + 2, column=0, padx=1, pady=5)
            period2_entry = Entry(update_window)
            period2_entry.grid(row=i + 2, column=1, padx=1, pady=5)
            # Добавляем поля ввода в список значений как отдельные элементы
            entry_values.append(period1_entry)
            entry_values.append(period2_entry)
        else:
            label = Label(update_window, text=label_text)
            label.grid(row=i + 1, column=0, padx=10, pady=10)
            if label_text == "Сотрудник":
                query_result = execute_sql_query("""SELECT ID FROM "Сотрудник";""")
                combo_values = [row[0] for row in query_result]
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i + 1, column=1, padx=(0, 30), pady=10)
                staff_combobox.set("")
                entry_values.append(staff_combobox)
    # Создание кнопки под всеми полями ввода
    update_button = Button(update_window, text="Создать", command=click_create)
    update_button.grid(row=len(labels) + 2, column=0, columnspan=2, padx=(10, 30), pady=10, sticky="ew")
#---ОТЧЕТ ДИНАМИКА---
def fetch_and_plot_data(arg1, arg2):
    def fetch_data(sql_query):
        conn = psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        data = cursor.fetchall()
        conn.close()
        return data
    def plot_functions(data1, data2):
        plot_window = Toplevel()
        plot_window.title("График")
        plot_window.geometry("600x400")
        plot_window.grab_set()
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.plot(data1[0], data1[1], color='blue', label='Закупки')
        ax.plot(data2[0], data2[1], color='red', label='Продажи')
        ax.set_xlabel('Год')
        ax.set_ylabel('Цена')
        ax.set_title('Общая стоимость закупок и продаж по годам')
        ax.legend(loc='upper left')
        ax.grid(True)
        for (x, y) in zip(data1[0], data1[1]):
            ax.text(x, y, f'{y}', ha='center', va='bottom', color='blue')

        for (x, y) in zip(data2[0], data2[1]):
            ax.text(x, y, f'{y}', ha='center', va='bottom', color='red')
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    sql_query_base_f1 = """
        SELECT 
            EXTRACT(YEAR FROM "Закупка".Дата) AS Год,
            SUM(
                COALESCE("Животное"."Цена", 0) 
                + COALESCE("Вид закупки"."Кол-во корма" * "Корм".Цена, 0)
                + COALESCE("Кормовые добавки".Цена * "Вид закупки"."Кол-во кормовых добавок", 0)
            ) AS "Общая стоимость закупки"
        FROM 
            "Вид закупки"
        LEFT JOIN 
            "Животное" ON "Вид закупки"."ID животного" = "Животное".ID
        LEFT JOIN 
            "Закупка" ON "Вид закупки"."ID закупки" = "Закупка".ID
        LEFT JOIN 
            "Сотрудник" ON "Закупка"."ID сотрудника" = "Сотрудник".ID
        LEFT JOIN 
            "Корм" ON "Вид закупки"."ID корма" = "Корм".ID
        LEFT JOIN 
            "Кормовые добавки" ON "Вид закупки"."ID кормовых добавок" = "Кормовые добавки".ID
        """
    sql_query_base_f2 = """
        SELECT 
            EXTRACT(YEAR FROM "Реализация"."Дата") AS Год,
            SUM("Животное"."Цена") AS "Общая цена животных"
        FROM 
            "Животное" 
        JOIN 
            "Вид реализации" ON "Вид реализации"."ID животного" = "Животное".ID 
        JOIN 
            "Реализация" ON "Вид реализации"."ID реализации" = "Реализация"."id"
        """
    if arg1 is not None and arg2 is not None:
        sql_query_base_f1 += """
            WHERE 
                "Закупка"."Дата" BETWEEN TO_DATE('%s', 'YYYY') AND TO_DATE('%s', 'YYYY')
            GROUP BY     
                EXTRACT(YEAR FROM "Закупка".Дата)
            ORDER BY 
                Год;
        """
        sql_query_base_f2 += """
            WHERE 
                "Реализация"."Дата" BETWEEN TO_DATE('%s', 'YYYY') AND TO_DATE('%s', 'YYYY')
            GROUP BY 
                EXTRACT(YEAR FROM "Реализация"."Дата")
            ORDER BY 
                Год;
        """
        sql_query_f1 = sql_query_base_f1 % (arg1, arg2)
        sql_query_f2 = sql_query_base_f2 % (arg1, arg2)
    else:
        sql_query_base_f1 += """
            GROUP BY     
                EXTRACT(YEAR FROM "Закупка".Дата)
            ORDER BY 
                Год;
        """
        sql_query_base_f2 += """
            GROUP BY 
                EXTRACT(YEAR FROM "Реализация"."Дата")
            ORDER BY 
                Год;
        """
        sql_query_f1 = sql_query_base_f1
        sql_query_f2 = sql_query_base_f2
    data_f1 = fetch_data(sql_query_f1)
    data_f2 = fetch_data(sql_query_f2)
    t_values_f1 = [int(row[0]) for row in data_f1]
    f1_data = [row[1] for row in data_f1]
    t_values_f2 = [int(row[0]) for row in data_f2]
    f2_data = [row[1] for row in data_f2]
    plot_functions((t_values_f1, f1_data), (t_values_f2, f2_data))
def open_OTCHET_dinamika():
    def click_create(period1_entry, period2_entry):
        values = []
        # Append the period entries to the values list
        values.append(period1_entry.get())
        values.append(period2_entry.get())
        if values[0] == "" or values[1] == "":
            values[0] = None
            values[1] = None
        if  values[0] != None and values[1] != None:
            try:
                if len(values[0]) in [4, 5]:
                    values[0] += ':00'
                if len(values[1]) in [4, 5]:
                    values[1] += ':00'
                if values[0] >= values[1]:
                    messagebox.showerror("Ошибка", "Неверно указано время.")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат времени. Ожидается формат HH:MM:SS.")
                return
        update_window.destroy()
        fetch_and_plot_data(values[0], values[1])
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Отчет о динамике")
    update_window.geometry("260x180")
    update_window.resizable(False, False)
    label = Label(update_window, text="Период")
    label.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    period1_entry = Entry(update_window)
    period1_entry.grid(row=1, column=0, padx=3, pady=5)
    period2_entry = Entry(update_window)
    period2_entry.grid(row=1, column=1, padx=1, pady=5)
    update_button = Button(update_window, text="Создать", command=lambda: click_create(period1_entry, period2_entry))
    update_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---ОТЧЕТ Численность животных---
def generate_animal_report(age_threshold=None, comparison_operator=None, file_path='report.txt'):
    def fetch_data(sql_query, params=None):
        # Подключение к базе данных и выполнение SQL-запроса
        conn = psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm')
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        data = cursor.fetchall()
        conn.close()
        return data
    def create_pivot_table(data):
        # Создание сводной таблицы, где ключами словаря будут названия ферм, а значениями - словари,
        # в которых ключами будут виды животных, а значениями - количество животных данного вида на ферме
        pivot_table = {}
        for row in data:
            farm_name, animal_type = row
            if farm_name not in pivot_table:
                pivot_table[farm_name] = {}
            if animal_type not in pivot_table[farm_name]:
                pivot_table[farm_name][animal_type] = 1
            else:
                pivot_table[farm_name][animal_type] += 1
        return pivot_table
    def print_pivot_table(pivot_table, file):
        # Сортировка названий ферм и видов животных для создания сводной таблицы
        farms = sorted(pivot_table.keys())
        animal_types = sorted(
            set(animal_type for farm_data in pivot_table.values() for animal_type in farm_data.keys()))
        # Создание массивов/списков Xname и Yname на основе названий ферм и видов животных
        Xname = farms
        Yname = animal_types
        M = len(Xname)
        N = len(Yname)
        # Создание "матриц" T и nT для хранения количества животных и их уникальных значений
        T = [[0] * N for _ in range(M)]
        nT = [[0] * N for _ in range(M)]
        for i, farm in enumerate(farms):
            for j, animal_type in enumerate(animal_types):
                count = pivot_table.get(farm, {}).get(animal_type, 0)
                T[i][j] = count
                if count > 0:
                    nT[i][j] = 1
        # Вычисление общего количества животных на каждой ферме и по каждому виду
        total_by_farm = {farm: sum(pivot_table.get(farm, {}).values()) for farm in farms}
        total_by_animal_type = {animal_type: sum(pivot_table.get(farm, {}).get(animal_type, 0) for farm in farms) for
                                animal_type in animal_types}
        total_total = sum(total_by_farm.values())
        str_ = f"Возраст {comparison_operator} {age_threshold} лет" if age_threshold is not None and comparison_operator in valid_operators else "Любого возраста"
        with open(file, 'w', encoding='utf-8') as f:
            f.write("Отчет о численности животных на ферме\n")
            f.write(f"Параметр: {str_}\n")
            f.write("{:<5} {:<20}".format("", "Ферма"))
            for animal_type in animal_types:
                f.write("{:<10}".format(animal_type))
            f.write("{:<10}\n".format("Итого"))

            for i, farm in enumerate(farms):
                f.write("{:<5} {:<20}".format(i + 1, farm))
                for j, animal_type in enumerate(animal_types):
                    f.write("{:<10}".format(T[i][j]))
                f.write("{:<10}\n".format(total_by_farm[farm]))

            f.write("{:<5} {:<20}".format("Всего", ""))
            for animal_type in animal_types:
                f.write("{:<10}".format(total_by_animal_type[animal_type]))
            f.write("{:<10}\n".format(total_total))
    sql_query = """
    SELECT Ферма."Название фермы", Порода."Вид животного" FROM Животное
    LEFT JOIN Порода ON Животное."ID породы" = Порода.ID
    LEFT JOIN Ферма ON Животное."ID фермы" = Ферма.ID
    """
    params = ()
    valid_operators = ['>', '<', '=', '>=', '<=']
    if age_threshold is not None and comparison_operator in valid_operators:
        sql_query += f" WHERE EXTRACT(YEAR FROM AGE(Животное.Возраст)) {comparison_operator} %s"
        params = (age_threshold,)
    data = fetch_data(sql_query, params)
    messagebox.showinfo("Успех", "Отчет успешно сформирован")
    pivot_table = create_pivot_table(data)
    print_pivot_table(pivot_table, file_path)
def open_OTCHET_chislennost():
    def click_create():
        condition = entry_values[0].get()
        age = entry_values[1].get()
        if condition == "":
            condition = None
        if age == "":
            age = None
        update_window.destroy()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            generate_animal_report(age, condition, file_path)
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Отчет о численности животных")
    update_window.geometry("300x180")
    update_window.resizable(False, False)
    labels = ("Условие", "Возраст животного")
    entry_values = []
    for i, label_text in enumerate(labels):
        if label_text == "Возраст животного":
            label = Label(update_window, text=label_text)
            label.grid(row=i + 2, column=0, padx=10, pady=10, sticky="w")
            period1_entry = Entry(update_window)
            period1_entry.grid(row=i + 2, column=1, padx=10, pady=10, sticky="w")
            entry_values.append(period1_entry)
        else:
            label = Label(update_window, text=label_text)
            label.grid(row=i + 1, column=0, padx=10, pady=10, sticky="w")
            if label_text == "Условие":
                combo_values = ['>', '<', '=', '>=', '<=']
                staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
                staff_combobox.grid(row=i + 1, column=1, padx=10, pady=10, sticky="w")
                staff_combobox.set("")
                entry_values.append(staff_combobox)
            else:
                entry = Entry(update_window)
                entry.grid(row=i + 1, column=1, padx=10, pady=10, sticky="w")
                entry_values.append(entry)
    update_button = Button(update_window, text="Создать", command=click_create)
    update_button.grid(row=len(labels) + 2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#---ОТЧЕТ РАСПРЕДЕЛЕНИЕ---
def plot_pie_chart_with_tkinter(farm_name=None):
    def fetch_data(sql_query, params=None):
        conn = psycopg2.connect('postgresql://postgres:pg123@localhost:5432/farm')
        cursor = conn.cursor()
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        data = cursor.fetchall()
        conn.close()
        return data
    if farm_name is None:
        sql_query_farm = """
            SELECT Порода."Вид животного", COUNT(*) as Количество
            FROM Животное
            LEFT JOIN Порода ON Животное."ID породы" = Порода.ID
            LEFT JOIN Ферма ON Животное."ID фермы" = Ферма.ID
            WHERE NOT EXISTS (
                SELECT 1
                FROM "Вид реализации"
                WHERE "Вид реализации"."ID животного" = Животное.ID
            )
            GROUP BY Порода."Вид животного";
            """
        title = 'Распределение видов животных на всех фермах'
        params = None
    else:
        sql_query_farm = """
            SELECT Порода."Вид животного", COUNT(*) as Количество
            FROM Животное
            LEFT JOIN Порода ON Животное."ID породы" = Порода.ID
            LEFT JOIN Ферма ON Животное."ID фермы" = Ферма.ID
            WHERE Ферма."Название фермы" = %s
            AND NOT EXISTS (
                SELECT 1
                FROM "Вид реализации"
                WHERE "Вид реализации"."ID животного" = Животное.ID
            )
            GROUP BY Порода."Вид животного";
            """
        title = f'Распределение видов животных на ферме: {farm_name}'
        params = (farm_name,)
    data = fetch_data(sql_query_farm, params)
    if farm_name:
        title = f'Распределение видов животных на ферме: {farm_name}'
    else:
        title = 'Распределение видов животных на всех фермах'
    fig = Figure(figsize=(10, 8))
    ax = fig.add_subplot(111)
    labels = [row[0] for row in data]
    sizes = [row[1] for row in data]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title(title, pad=20)
    plot_window = Tk()
    plot_window.title("График")
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    mainloop()
def open_OTCHET_raspredelenie():
    def click_create():
        condition = staff_combobox.get() 
        if condition == "":
            condition = None
        update_window.destroy()
        plot_pie_chart_with_tkinter(condition)
    update_window = Toplevel()
    update_window.grab_set()
    update_window.title("Отчет о распределение животных")
    update_window.geometry("300x120")
    update_window.resizable(False, False)
    entry_values = []
    label_text = "Название фермы"
    label = ttk.Label(update_window, text=label_text)
    label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
    query_result = execute_sql_query("""SELECT DISTINCT "Название фермы" FROM "Ферма";""")
    combo_values = [row[0] for row in query_result]
    staff_combobox = ttk.Combobox(update_window, values=combo_values, state="readonly")
    staff_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    staff_combobox.set("")
    update_button = Button(update_window, text="Создать", command=click_create)
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
#-----------Окно животные----------
# SQL запрос для выбора данных из таблицы "Животное"
sql_query = """SELECT * FROM "Животное";"""
# SQL запрос для создания таблицы "Животное", если она не существует
create_table_query = """
CREATE TABLE IF NOT EXISTS "Животное" (
    ID serial primary key,
    "ID породы" integer,
    "ID фермы" integer,
    "Пол" varchar(1),
    "Возраст" TIMESTAMP,
    "ID родителя" integer,
    "Цена" integer
);
"""
# Вывод информации о животном
def show_animal_info(event, tree, info_text):
    item = tree.focus()  # Получаем выбранный элемент
    values = tree.item(item, 'values')
    if values:
        # Получаем ID выбранного животного
        animal_id = values[0]
        # Формируем SQL-запрос для получения информации о выбранном животном
        query = f"""
            SELECT 
                COALESCE(Животное.ID::text, 'пусто') AS ID,
                COALESCE(Порода."Название", 'пусто') AS "Название породы",
                COALESCE(Порода."Вид животного", 'пусто') AS "Вид животного",
                COALESCE(Порода."Описание", 'пусто') AS "Описание породы",
                COALESCE(Животное."Пол", 'пусто') AS "Пол",
                COALESCE(Животное."Возраст"::text, 'пусто') AS "Возраст",
                COALESCE(Животное."ID родителя"::text, 'пусто') AS "ID родителя",
                COALESCE(Животное."Цена"::text, 'пусто') AS "Цена",
                COALESCE(Ферма."Название фермы", 'пусто') AS "Ферма",
                COALESCE(Корм."Название", 'пусто') AS "Название корма",
                COALESCE(Корм."Описание", 'пусто') AS "Описание корма",
                COALESCE(Корм."Цена"::text, 'пусто') AS "Цена корма",
                COALESCE("Кормовые добавки"."Название", 'пусто') AS "Название добавки",
                COALESCE("Кормовые добавки"."Описание", 'пусто') AS "Описание добавки",
                COALESCE("Кормовые добавки"."Цена"::text, 'пусто') AS "Цена добавки",
                COALESCE("Реализация"."Дата"::text, 'не продано') AS "Дата продажи",
                COALESCE("Закупка"."Дата"::text, 'не закупалось') AS "Дата закупки"
            FROM 
                Животное
            LEFT JOIN 
                Порода ON Животное."ID породы" = Порода.ID
            LEFT JOIN 
                "Животное и рацион" ON Животное.ID = "Животное и рацион"."ID животного"
            LEFT JOIN 
                Рацион ON "Животное и рацион"."ID рациона" = Рацион.ID
            LEFT JOIN 
                Корм ON Рацион."ID корма" = Корм.ID
            LEFT JOIN 
                "Кормовые добавки" ON Рацион."ID кормовых добавок" = "Кормовые добавки".ID
            LEFT JOIN 
                Ферма ON Животное."ID фермы" = Ферма.ID
            LEFT JOIN 
                "Вид реализации" ON "Вид реализации"."ID животного" = Животное.ID
            LEFT JOIN
                "Реализация" ON "Вид реализации"."ID реализации"="Реализация".ID
            LEFT JOIN 
                "Вид закупки" ON "Вид закупки"."ID животного" = Животное.ID
            LEFT JOIN
                "Закупка" ON "Закупка".ID="Вид закупки"."ID закупки"
            WHERE
                Животное.ID = {animal_id};
        """
        # Выполняем запрос и получаем результаты
        animal_info = execute_sql_query(query)
        # Если информация о животном найдена, обновляем текстовый виджет animal_info_text
        if animal_info:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            # Форматируем и выводим данные
            info_dict = {}
            for row in animal_info:
                for idx, field in enumerate([
                    "ID", "Название породы", "Вид животного", "Описание породы",
                    "Пол", "Возраст", "ID родителя", "Цена", "Ферма",
                    "Название корма", "Описание корма", "Цена корма",
                    "Название добавки", "Описание добавки", "Цена добавки",
                    "Дата продажи", "Дата закупки"
                ]):
                    if field not in info_dict:
                        info_dict[field] = set()
                    info_dict[field].add(row[idx])
            for field, values in info_dict.items():
                info_text.insert("end", f"{field}: {', '.join(values)}\n")

            info_text.config(state="disabled")
        else:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            info_text.insert("end", "Информация о выбранном животном не найдена.")
            info_text.config(state="disabled")
    else:
        info_text.config(state="normal")
        info_text.delete(1.0, "end")
        info_text.config(state="disabled")
def del_animal():
    try:
        selection = animal_tree.selection()
        for item in selection:
            # Получаем значение первого столбца строки
            animal_id = animal_tree.item(item, 'values')[0]
            sql_del = f"""DELETE FROM "Животное" WHERE ID= {animal_id} ;
            DELETE FROM  "Животное и рацион" WHERE "ID животного"={animal_id};
            DELETE FROM   "Реализация" WHERE "Реализация".ID IN (SELECT "Вид реализации"."ID реализации" FROM "Вид реализации" WHERE "Вид реализации"."ID животного"={animal_id});
            DELETE FROM "Вид реализации" WHERE "Вид реализации"."ID животного"={animal_id};
    
            CREATE OR REPLACE FUNCTION get_purchase_id()
            RETURNS INTEGER AS $$
            DECLARE
                purchase_id INTEGER;
                animal_id INTEGER := {animal_id}; -- Здесь указывается ID животного, которое нужно удалить
                purchase_id_list INTEGER[];
            BEGIN
                -- Получаем список ID закупок, которые нужно удалить
                SELECT ARRAY(SELECT DISTINCT "ID закупки"
                             FROM "Вид закупки"
                             WHERE "ID животного" = animal_id 
                             AND "ID корма" = 0 
                             AND "Кол-во кормовых добавок" = 0)
                INTO purchase_id_list;
    
                -- Удаляем все записи из "Вид закупки" с указанным "ID животного" и без корма и кормовых добавок
                DELETE FROM "Вид закупки"
                WHERE "ID животного" = animal_id 
                AND "ID корма" = 0 
                AND "Кол-во кормовых добавок" = 0;
    
                UPDATE "Вид закупки"
                SET "ID животного"=0
                WHERE "ID животного" = animal_id;
                -- Удаляем записи из "Закупка", если соответствующие записи в "Вид закупки" были полностью удалены
                FOREACH purchase_id IN ARRAY purchase_id_list
                LOOP
                    IF (SELECT COUNT(*) FROM "Вид закупки" WHERE "ID закупки" = purchase_id) = 0 THEN
                        DELETE FROM "Закупка" WHERE ID = purchase_id;
                    END IF;
                END LOOP;
    
                RETURN purchase_id_list[1]; -- Возвращаем первый ID из списка
            END;
            $$ LANGUAGE plpgsql;
    
            -- Вызов пл/пл-функции для получения ID закупки
            SELECT get_purchase_id();
    
            """
            execute_sql_query(sql_del)
            animal_tree.delete(item)
            # Вид Закупки
            init_frame5()
            bind_frame5_event_handlers()
            # Вид реализации
            init_frame6()
            bind_frame6_event_handlers()
            # Закупка
            init_frame11()
            bind_frame11_event_handlers()
            # Реализация
            init_frame12()
            bind_frame12_event_handlers()
            # "Животное и рацион"
            init_frame16()
            bind_frame16_event_handlers()
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
#Инициализация окна животные
def init_frame1():
    global animal_tree, animal_info_text
    # Столбцы для "Животные"
    animal_columns = ("ID", "ID породы", "ID фермы", "Пол", "Возраст", "ID родителя", "Цена")
    # Создание таблицы "Животные"
    animal_tree = create_table(frame1, animal_columns)
    # Загрузка данных
    load_data(animal_tree, sql_query, create_table_query)
    # Создание текстового виджета
    animal_info_text = Text(frame1, wrap="word")
    animal_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    # Создание виджета прокрутки
    scrollbar = Scrollbar(frame1, command=animal_info_text.yview)
    # Привязка прокрутки текстового виджета к виджету прокрутки
    animal_info_text.config(yscrollcommand=scrollbar.set)
    # Удаление
    delete_button = Button(frame1, text="Удалить", command=del_animal, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    # Выгрузить данные из файла
    delete_button = Button(frame1, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Животное",animal_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    # Добавить и обновить
    add_button = Button(frame1, text="Добавить", command=open_add_window_an, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame1, text="Изменить", command=open_update_window_an, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
# Обработчик события на нажатие в таблице
def bind_frame1_event_handlers():
    animal_tree.bind("<<TreeviewSelect>>", lambda event:show_animal_info(event,animal_tree, animal_info_text))
#----------------Окно сотрудник-----
sql_query4 = """SELECT * FROM "Сотрудник";"""
create_table_query4 = """
CREATE TABLE IF NOT EXISTS "Сотрудник" (
 ID serial primary key,
"Фамилия" varchar(50),
"Имя" varchar(50),
"Отчество" varchar(50),
"ИНН" varchar(30)
);
"""
def del_staff():
    try:
        selection = staff_tree.selection()
        for item in selection:
            # Получаем значение первого столбца строки
            staff_id = staff_tree.item(item, 'values')[0]
            sql_del = f"""DELETE FROM "Сотрудник" WHERE ID={staff_id} ;
DELETE FROM "Вид закупки" WHERE "ID закупки" IN (SELECT "Закупка".ID FROM "Закупка" WHERE "Закупка"."ID сотрудника"={staff_id});
DELETE FROM "Закупка" WHERE "Закупка"."ID сотрудника"={staff_id};
DELETE FROM "Контакты" WHERE "Контакты"."ID сотрудника"={staff_id};
DELETE FROM "Вид реализации" WHERE "ID реализации" IN (SELECT "Реализация".ID FROM "Реализация" WHERE "Реализация"."ID сотрудника"={staff_id});
DELETE FROM "Реализация" WHERE "Реализация"."ID сотрудника"={staff_id};
DELETE FROM "Должность" WHERE "Должность"."ID сотрудника"={staff_id};
DELETE FROM "Схема оплаты" WHERE "Схема оплаты"."ID сотрудника"={staff_id};
DELETE FROM "График работы" WHERE "График работы"."ID сотрудника"={staff_id};
            """
            execute_sql_query2(sql_del)
            staff_tree.delete(item)
            # Вид Закупки
            init_frame5()
            bind_frame5_event_handlers()
            # Вид реализации
            init_frame6()
            bind_frame6_event_handlers()
            # Закупка
            init_frame11()
            bind_frame11_event_handlers()
            # Реализация
            init_frame12()
            bind_frame12_event_handlers()
            # Контакты
            init_frame7()
            bind_frame7_event_handlers()
            # "Схема оплаты"
            init_frame13()
            bind_frame13_event_handlers()
            # "График работы"
            init_frame14()
            bind_frame14_event_handlers()
            # "Должность"
            init_frame15()
            bind_frame15_event_handlers()
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def show_staff_info(event, tree, info_text, val):
    item = tree.focus()
    values = tree.item(item, 'values')
    if values:
        staff_id = values[val]
        query = f"""
              SELECT 
    COALESCE(Сотрудник.id::text, 'пусто') AS id,
    COALESCE(Фамилия, 'пусто') AS Фамилия,
    COALESCE(Имя, 'пусто') AS Имя,
    COALESCE(Отчество, 'пусто') AS Отчество,
    COALESCE(ИНН, 'пусто') AS ИНН,
    COALESCE("График работы"."Дни недели", 'пусто') AS "Дни недели",
    COALESCE("Время начала"::text, 'пусто') AS "Время начала",
    COALESCE("Время окончания"::text, 'пусто') AS "Время окончания",
    COALESCE("Примечание", 'пусто') AS Примечание,
    COALESCE("Контакты".Телефон, 'пусто') AS Телефон,
    COALESCE("Должность"."Должность", 'пусто') AS Должность,
    COALESCE("Стаж"::text, 'пусто') AS Стаж,
    COALESCE("Дата увольнения"::text, 'пусто') AS "Дата увольнения",
    COALESCE("Зарплата"."Тип оплаты", 'пусто') AS "Тип оплаты",
    COALESCE("Сумма"::text, 'пусто') AS Сумма,
    COALESCE("Ферма"."Название фермы", 'пусто') AS "Название фермы",
    COALESCE("Местоположение", 'пусто') AS Местоположение
FROM 
    Сотрудник
LEFT JOIN 
    "Контакты" ON Сотрудник.id = "Контакты"."ID сотрудника"
LEFT JOIN 
    "График работы" ON Сотрудник.id = "График работы"."ID сотрудника"
LEFT JOIN 
    "Должность" ON Сотрудник.id = "Должность"."ID сотрудника"
LEFT JOIN 
    "Схема оплаты" ON "Схема оплаты"."ID сотрудника" = Сотрудник.id
LEFT JOIN 
    "Зарплата" ON "Зарплата"."ID схемы" = "Схема оплаты".ID
LEFT JOIN 
    "Ферма" ON "Ферма".ID = "Должность"."ID фермы"
WHERE
    Сотрудник.id = {staff_id};
        """
        staff_info = execute_sql_query(query)
        if staff_info:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            info_dict = {}
            for row in staff_info:
                for idx, field in enumerate(["ID", "Фамилия", "Имя", "Отчество", "ИНН", "Дни недели", "Время начала", "Время окончания", "Примечание", "Телефон", "Должность", "Стаж", "Дата увольнения", "Тип оплаты", "Сумма", "Название фермы", "Местоположение"]):
                    if field not in info_dict:
                        info_dict[field] = set()
                    info_dict[field].add(row[idx])
            for field, values in info_dict.items():
                info_text.insert("end", f"{field}: {', '.join(values)}\n")
            info_text.config(state="disabled")
        else:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            info_text.insert("end", "Информация о выбранном сотруднике не найдена.")
            info_text.config(state="disabled")
    else:
        info_text.config(state="normal")
        info_text.delete(1.0, "end")
        info_text.config(state="disabled")
def init_frame4():
    global staff_tree, staff_info_text
    staff_columns = ("ID", "Фамилия", "Имя", "Отчество", "ИНН")
    staff_tree = create_table(frame4, staff_columns)
    load_data(staff_tree, sql_query4, create_table_query4)
    staff_info_text = Text(frame4, wrap="word")
    staff_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame4, command=staff_info_text.yview)
    staff_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame4, text="Удалить", command=del_staff, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame4, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Сотрудник",staff_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame4, text="Добавить", command=open_add_window_staff, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame4, text="Изменить", command=open_update_window_staff, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def bind_frame4_event_handlers():
    staff_tree.bind("<<TreeviewSelect>>",lambda event: show_staff_info(event,staff_tree, staff_info_text,0))
#-------------Окно Схема оплаты-------------
sql_query13 = """SELECT * FROM "Схема оплаты";"""
create_table_query13 = """
CREATE TABLE IF NOT EXISTS "Схема оплаты" (
ID serial primary key,
"ID сотрудника" integer
);"""
def del_payment():
    try:
        selection = payment_tree.selection()
        for item in selection:
            payment_id =  payment_tree.item(item, 'values')[0]
            sql_del = f"""
                DELETE FROM "Схема оплаты" WHERE ID ={payment_id};
                 DELETE FROM "Зарплата" WHERE "ID схемы" ={payment_id};"""
            execute_sql_query2(sql_del)
            # Зарплата
            init_frame10()
            payment_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame13():
    global payment_tree, payment_info_text
    payment_columns = ("ID", "ID сотрудника")
    payment_tree = create_table(frame13, payment_columns)
    load_data(payment_tree, sql_query13, create_table_query13)
    payment_info_text = Text(frame13, wrap="word")
    payment_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame13, command=payment_info_text.yview)
    payment_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame13, text="Удалить", command=del_payment, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame13, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Схема оплаты",payment_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame13, text="Добавить", command=open_add_window_payment, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
def bind_frame13_event_handlers():
    payment_tree.bind("<<TreeviewSelect>>",lambda event: show_staff_info(event,payment_tree, payment_info_text,1))
#--------------Окно График работы----------
sql_query14 = """SELECT * FROM "График работы";"""
create_table_query14 = """
CREATE TABLE IF NOT EXISTS "График работы" (
ID serial primary key,
"Дни недели" varchar(30),
"Время начала" time,
"Время окончания" time,
"ID сотрудника" integer,
"Примечание" varchar(100)
);
"""
def del_work_time():
    try:
        selection = work_time_tree.selection()
        for item in selection:
            work_time_id = work_time_tree.item(item, 'values')[0]
            sql_del = f"""DELETE FROM "График работы" WHERE "График работы".ID='{work_time_id}' ;"""
            execute_sql_query2(sql_del)
            work_time_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame14():
    global work_time_tree, work_time_info_text
    work_time_columns = ("ID", "Дни недели","Время начала","Время окончания","ID сотрудника","Примечание")
    work_time_tree = create_table(frame14, work_time_columns)
    load_data(work_time_tree, sql_query14, create_table_query14)
    work_time_info_text = Text(frame14, wrap="word")
    work_time_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame14, command=work_time_info_text.yview)
    work_time_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame14, text="Удалить", command=del_work_time, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame14, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("График работы",work_time_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame14, text="Добавить", command=open_add_window_work_time, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame14, text="Изменить", command=open_update_window_work_time, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def bind_frame14_event_handlers():
    work_time_tree.bind("<<TreeviewSelect>>",lambda event: show_staff_info(event,work_time_tree, work_time_info_text,4))
#-----------------Окно Должность-------------------
sql_query15 = """SELECT 
    "ID сотрудника", 
    "ID фермы", 
    "Должность", 
    "Стаж", 
    CASE 
        WHEN "Дата увольнения" = 'infinity' THEN 'infinity'
        ELSE "Дата увольнения"::text
    END AS "Дата увольнения"
FROM 
    "Должность";"""
create_table_query15 = """
CREATE TABLE IF NOT EXISTS "Должность" (
 "ID сотрудника" integer,
    "ID фермы" integer,
    "Должность" varchar(50),
    "Стаж" TIMESTAMP,
    "Дата увольнения" TIMESTAMP DEFAULT NULL
);
"""
def init_frame15():
    global post_tree, post_info_text
    post_columns = ("ID сотрудника", "ID фермы","Должность","Стаж","Дата увольнения")
    post_tree = create_table(frame15, post_columns)
    load_data(post_tree, sql_query15, create_table_query15)
    post_info_text = Text(frame15, wrap="word")
    post_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame15, command=post_info_text.yview)
    post_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame15, text="Удалить", command=del_post, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame15, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Должность",post_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame15, text="Добавить", command=open_add_window_post, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame15, text="Изменить", command=open_update_window_post, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def del_post():
        try:
            selection = post_tree.selection()
            for item in selection:
                post_id = post_tree.item(item, 'values')[0]
                farm_id = post_tree.item(item, 'values')[1]
                post = post_tree.item(item, 'values')[2]
                time = post_tree.item(item, 'values')[3]
                sql_del = f"""DELETE FROM "Должность" WHERE "Должность"."ID сотрудника"='{post_id}' 
                and "Должность"."Должность"='{post}' 
                and "Должность"."ID фермы"= {farm_id}
                and "Должность"."Стаж"='{time}';"""
                execute_sql_query2(sql_del)
                post_tree.delete(item)
                messagebox.showinfo("Успешно", "Данные были успешно удалены")
        except Exception as e:
            messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def bind_frame15_event_handlers():
    post_tree.bind("<<TreeviewSelect>>",lambda event: show_staff_info(event,post_tree, post_info_text,0))
#----------Окно Животное и рацион----------
sql_query16 = """SELECT * FROM "Животное и рацион";"""
create_table_query16 = """
CREATE TABLE IF NOT EXISTS "Животное и рацион" (
"ID животного" integer,
"ID рациона" integer
);
"""
def del_AN_ration():
    try:
        selection = AN_ration_tree.selection()
        for item in selection:
            ration_id = AN_ration_tree.item(item, 'values')[1]
            an_id = AN_ration_tree.item(item, 'values')[0]
            sql_del = f"""DELETE FROM "Животное и рацион" WHERE "Животное и рацион"."ID животного"='{an_id}' and "Животное и рацион"."ID рациона"='{ration_id}';"""
            execute_sql_query2(sql_del)
            AN_ration_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame16():
    global AN_ration_tree,  AN_ration_info_text
    AN_ration_columns = ("ID животного","ID рациона")
    AN_ration_tree = create_table(frame16,  AN_ration_columns)
    load_data( AN_ration_tree, sql_query16, create_table_query16)
    AN_ration_info_text = Text(frame16, wrap="word")
    AN_ration_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame16, command= AN_ration_info_text.yview)
    AN_ration_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame16, text="Удалить", command=del_AN_ration, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame16, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Животное и рацион", AN_ration_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame16, text="Добавить", command=open_add_window_AN_ration, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
def bind_frame16_event_handlers():
    AN_ration_tree.bind("<<TreeviewSelect>>",lambda event:  show_animal_info(event, AN_ration_tree,  AN_ration_info_text))
#------------Окно Контакты--------
sql_query7 = """SELECT * FROM "Контакты";"""
create_table_query7 = """
CREATE TABLE IF NOT EXISTS "Контакты" (
 "ID сотрудника" integer,
"Телефон" varchar(30)
);
"""
def show_contacts_info(event):
    item = contacts_tree.focus()
    values = contacts_tree.item(item, 'values')
    if values:
        contacts_id = values[0]
        query = f"""
SELECT 
    COALESCE(Сотрудник.id::text, 'пусто') AS id,
    COALESCE(Фамилия, 'пусто') AS Фамилия,
    COALESCE(Имя, 'пусто') AS Имя,
    COALESCE(Отчество, 'пусто') AS Отчество,
    COALESCE("Контакты".Телефон, 'пусто') AS Телефон,
    COALESCE("Должность"."Должность", 'пусто') AS Должность
FROM 
    Сотрудник
LEFT JOIN 
    "Контакты" ON Сотрудник.id = "Контакты"."ID сотрудника"
LEFT JOIN 
    "Должность" ON Сотрудник.id = "Должность"."ID сотрудника"
WHERE
    Сотрудник.id = {contacts_id};
        """
        contacts_info = execute_sql_query(query)
        if contacts_info:
            contacts_info_text.config(state="normal")
            contacts_info_text.delete(1.0, "end")
            info_dict = {}
            for row in contacts_info:
                for idx, field in enumerate(["ID", "Фамилия", "Имя", "Отчество", "Телефон", "Должность"]):
                    if field not in info_dict:
                        info_dict[field] = set()
                    info_dict[field].add(row[idx])
            for field, values in info_dict.items():
                contacts_info_text.insert("end", f"{field}: {', '.join(values)}\n")
            contacts_info_text.config(state="disabled")
        else:
            contacts_info_text.config(state="normal")
            contacts_info_text.delete(1.0, "end")
            contacts_info_text.insert("end", "Информация о выбранном сотруднике не найдена.")
            contacts_info_text.config(state="disabled")
    else:
        contacts_info_text.config(state="normal")
        contacts_info_text.delete(1.0, "end")
        contacts_info_text.config(state="disabled")
def del_contacts():
    try:
        selection = contacts_tree.selection()
        for item in selection:
            contacts_id = contacts_tree.item(item, 'values')[1]
            sql_del = f"""DELETE FROM "Контакты" WHERE "Контакты".Телефон='{contacts_id}';"""
            execute_sql_query2(sql_del)
            contacts_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame7():
    global contacts_tree, contacts_info_text
    contacts_columns = ("ID сотрудника", "Телефон")
    contacts_tree = create_table(frame7, contacts_columns)
    load_data(contacts_tree, sql_query7, create_table_query7)
    contacts_info_text = Text(frame7, wrap="word")
    contacts_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame7, command=contacts_info_text.yview)
    contacts_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame7, text="Удалить", command=del_contacts, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame7, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Контакты",contacts_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame7, text="Добавить", command=open_add_window_contacs, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame7, text="Изменить", command=open_update_window_contacs, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def bind_frame7_event_handlers():
    contacts_tree.bind("<<TreeviewSelect>>", show_contacts_info)
#-----Окно Рацион-------
sql_query17 = """SELECT * FROM "Рацион";"""
create_table_query17 = """
CREATE TABLE IF NOT EXISTS "Рацион" (
ID serial primary key,
"ID корма" integer,
"ID кормовых добавок" integer
);
"""
def show_ration_info(event):
    item = ration_tree.focus()
    values = ration_tree.item(item, 'values')
    if values:
        ration_id = values[0]
        query = f"""
SELECT 
    COALESCE(Рацион.ID::text, 'пусто') AS id,
    COALESCE(Корм.Название, 'пусто') AS "Название корма",
    COALESCE(Корм.Описание, 'пусто') AS "Описание корма",
    COALESCE(Корм.Цена::text, 'пусто') AS "Цена корма",
    COALESCE("Кормовые добавки".Название, 'пусто') AS "Название кормовых добавок",
    COALESCE("Кормовые добавки".Описание, 'пусто') AS "Описание кормовых добавок",
    COALESCE("Кормовые добавки".Цена::text, 'пусто') AS "Цена кормовых добавок"
FROM 
    Рацион
LEFT JOIN 
    "Корм" ON Корм.ID = "Рацион"."ID корма"
LEFT JOIN 
    "Кормовые добавки" ON "Кормовые добавки".ID = "Рацион"."ID кормовых добавок"
WHERE
    Рацион.ID = {ration_id};
        """
        ration_info = execute_sql_query(query)
        if ration_info:
            ration_info_text.config(state="normal")
            ration_info_text.delete(1.0, "end")
            info_dict = {}
            for row in ration_info:
                for idx, field in enumerate(["ID", "Название корма", "Описание корма", "Цена корма", "Название кормовых добавок", "Описание кормовых добавок", "Цена кормовых добавок"]):
                    if field not in info_dict:
                        info_dict[field] = set()
                    info_dict[field].add(row[idx])
            for field, values in info_dict.items():
                ration_info_text.insert("end", f"{field}: {', '.join(values)}\n")
            ration_info_text.config(state="disabled")
        else:
            ration_info_text.config(state="normal")
            ration_info_text.delete(1.0, "end")
            ration_info_text.insert("end", "Информация о выбранном сотруднике не найдена.")
            ration_info_text.config(state="disabled")
    else:
        ration_info_text.config(state="normal")
        ration_info_text.delete(1.0, "end")
        ration_info_text.config(state="disabled")
def del_rations():
            try:
                selection = ration_tree.selection()
                for item in selection:
                    ration_id = ration_tree.item(item, 'values')[0]
                    sql_del = f"""DELETE FROM "Рацион" WHERE "Рацион".ID='{ration_id}';
                    DELETE FROM "Животное и рацион" WHERE "Животное и рацион"."ID рациона"='{ration_id}';"""
                    execute_sql_query2(sql_del)
                    # "Животное и рацион"
                    init_frame16()
                    bind_frame16_event_handlers()
                    ration_tree.delete(item)
                    messagebox.showinfo("Успешно", "Данные были успешно удалены")
            except Exception as e:
                messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame17():
    global ration_tree, ration_info_text
    ration_columns = ("ID", "ID корма","ID кормовых добавок")
    ration_tree = create_table(frame17, ration_columns)
    load_data(ration_tree, sql_query17, create_table_query17)
    ration_info_text = Text(frame17, wrap="word")
    ration_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame17, command=ration_info_text.yview)
    ration_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame17, text="Удалить", command=del_rations, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame17, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Рацион",ration_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame17, text="Добавить", command=open_add_window_ration, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame17, text="Изменить", command=open_update_window_ration, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def bind_frame17_event_handlers():
    ration_tree.bind("<<TreeviewSelect>>", show_ration_info)
#------------Окно Корм--------
sql_query8 = """SELECT * FROM "Корм";"""
create_table_query8 = """
CREATE TABLE IF NOT EXISTS "Корм" (
ID serial primary key,
"Название" varchar(30),
"Описание" varchar(1000),
"Цена" integer
);
"""
def del_food():
    try:
        selection = food_tree.selection()
        for item in selection:
            food_id = food_tree.item(item, 'values')[0]
            sql_del = f""" UPDATE "Рацион"
                SET "ID корма"=0
                WHERE "ID корма" = {food_id};
                DELETE FROM "Животное и рацион" WHERE "Животное и рацион"."ID рациона" IN (SELECT "Рацион".ID FROM "Рацион" WHERE "Рацион"."ID корма"=0 and "Рацион"."ID кормовых добавок"=0);
                DELETE FROM "Рацион" WHERE "Рацион"."ID корма"=0 and "Рацион"."ID кормовых добавок"=0;
                                DELETE FROM "Корм" WHERE "Корм".ID={food_id};"""
            execute_sql_query2(sql_del)
            # "Животное и рацион"
            init_frame16()
            bind_frame16_event_handlers()
            # "Рацион"
            init_frame17()
            bind_frame17_event_handlers()
            food_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame8():
    global food_tree, food_info_text
    food_columns = ("ID", "Название","Описание","Цена")
    food_tree = create_table(frame8, food_columns)
    load_data(food_tree, sql_query8, create_table_query8)
    delete_button = Button(frame8, text="Удалить", command=del_food, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame8, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Корм",food_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame8, text="Добавить", command=open_add_window_food, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame8, text="Изменить", command=open_update_window_food, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
#--------------Окно Кормовые добавки-------
sql_query9 = """SELECT * FROM "Кормовые добавки";"""
create_table_query9 = """
CREATE TABLE IF NOT EXISTS "Кормовые добавки" (
ID serial primary key,
"Название" varchar(30),
"Описание" varchar(1000),
"Цена" integer
);
"""
def del_food_add():
    try:
        selection = food_add_tree.selection()
        for item in selection:
            food_add_id =  food_add_tree.item(item, 'values')[0]
            sql_del = f"""UPDATE "Рацион"
                SET "ID кормовых добавок"=0
                WHERE "ID кормовых добавок" ={food_add_id};
                DELETE FROM "Животное и рацион" WHERE "ID рациона" IN (SELECT "Рацион".ID FROM "Рацион" WHERE "ID корма" = 0 AND "ID кормовых добавок" = 0);
                DELETE FROM "Рацион" WHERE "Рацион"."ID корма"=0 and "Рацион"."ID кормовых добавок"=0;
                                DELETE FROM "Кормовые добавки" WHERE "Кормовые добавки".ID={food_add_id};
"""
            execute_sql_query2(sql_del)
            # "Животное и рацион"
            init_frame16()
            bind_frame16_event_handlers()
            # "Рацион"
            init_frame17()
            bind_frame17_event_handlers()
            food_add_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame9():
    global food_add_tree,food_add_info_text
    food_add_columns = ("ID", "Название","Описание","Цена")
    food_add_tree = create_table(frame9, food_add_columns)
    load_data(food_add_tree, sql_query9, create_table_query9)
    delete_button = Button(frame9, text="Удалить", command=del_food_add, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame9, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Кормовые добавки",food_add_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame9, text="Добавить", command=open_add_window_foodadd, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame9, text="Изменить", command=open_update_window_foodadd, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
#--------------Окно Зарплата--------
sql_query10 = """SELECT * FROM "Зарплата";"""
create_table_query10 = """
CREATE TABLE IF NOT EXISTS "Зарплата" (
"ID схемы" integer,
"Тип оплаты" varchar(30),
"Сумма" integer
);
"""
def del_salary():
    try:
        selection = salary_tree.selection()
        for item in selection:
            payment_id =  salary_tree.item(item, 'values')[0]
            type_payment = salary_tree.item(item, 'values')[1]
            sum_payment =salary_tree.item(item, 'values')[2]
            sql_del = f"""
                 DELETE FROM "Зарплата" WHERE "ID схемы" ={payment_id} and "Тип оплаты"='{type_payment}'and "Сумма"={sum_payment};
                 DELETE FROM "Схема оплаты" WHERE ID ={payment_id} and (SELECT COUNT(*) FROM "Зарплата" WHERE "ID схемы" ={payment_id}) = 0 ;"""
            execute_sql_query2(sql_del)
            # "Схема оплаты"
            init_frame13()
            bind_frame13_event_handlers()
            salary_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame10():
    global salary_tree,salary_info_text
    salary_columns = ("ID схемы", "Тип оплаты","Сумма")
    salary_tree = create_table(frame10, salary_columns)
    load_data(salary_tree, sql_query10, create_table_query10)
    delete_button = Button(frame10, text="Удалить", command=del_salary, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame10, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Зарплата",salary_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame10, text="Добавить", command=open_add_window_salary, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame10, text="Изменить", command=open_update_window_salary, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
#-------------Окно ВИД закупки----------
sql_query5 = """SELECT * FROM "Вид закупки";"""
create_table_query5 = """
CREATE TABLE IF NOT EXISTS "Вид закупки" (
"ID закупки" integer,
"ID животного" integer,
"ID корма" integer,
"ID кормовых добавок" integer,
"Кол-во корма" integer,
"Кол-во кормовых добавок" integer
);
"""
def del_viewpursh():
    try:
        selection = viewpursh_tree.selection()
        for item in selection:
            viewpursh_id =  viewpursh_tree.item(item, 'values')[0]
            id_animal = viewpursh_tree.item(item, 'values')[1]
            id_food =viewpursh_tree.item(item, 'values')[2]
            id_food_add = viewpursh_tree.item(item, 'values')[3]
            id_food_count = viewpursh_tree.item(item, 'values')[4]
            id_food_add_count = viewpursh_tree.item(item, 'values')[5]
            execute_sql_query2( f"""DELETE FROM "Вид закупки" WHERE "ID закупки" ={viewpursh_id} and "ID животного"='{id_animal}'and "ID корма"={id_food} and "ID кормовых добавок"={id_food_add} and "Кол-во корма"='{id_food_count}' and "Кол-во кормовых добавок"='{id_food_add_count}';
                 DELETE FROM "Закупка" WHERE ID ={viewpursh_id} and (SELECT COUNT(*) FROM "Вид закупки" WHERE "ID закупки" ={viewpursh_id}) = 0 ;""")
            # Закупка
            init_frame11()
            viewpursh_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame5():
    global viewpursh_tree, viewpursh_info_text
    viewpursh_columns = ("ID закупки", "ID животного", "ID корма", "ID кормовых добавок", "Кол-во корма","Кол-во кормовых добавок")
    viewpursh_tree = create_table(frame5, viewpursh_columns)
    load_data(viewpursh_tree, sql_query5, create_table_query5)
    viewpursh_info_text = Text(frame5, wrap="word")
    viewpursh_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame5, command=viewpursh_info_text.yview)
    viewpursh_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame5, text="Удалить", command=del_viewpursh, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame5, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Вид закупки", viewpursh_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame5, text="Добавить", command=open_add_window_view_purchase, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
def bind_frame5_event_handlers():
    viewpursh_tree.bind("<<TreeviewSelect>>", lambda event: show_pursh_info(event, viewpursh_tree, viewpursh_info_text))
# ---------------Окно ЗАКУПКИ------------
sql_query11 = """SELECT * FROM "Закупка";"""
create_table_query11 = """
CREATE TABLE IF NOT EXISTS "Закупка" (
ID serial primary key,
"ID сотрудника" integer,
"Дата" TIMESTAMP,
"Примечания" varchar(100)
);

"""
def show_pursh_info(event, tree, info_text):
    item = tree.focus()
    values = tree.item(item, 'values')
    if values:
        record_id = values[0]
        query = f"""
        SELECT 
            "Вид закупки"."ID закупки",
            COALESCE(Сотрудник.Фамилия, 'нет данных') AS Фамилия,
            COALESCE(Сотрудник.Имя, 'нет данных') AS Имя,
            COALESCE(Сотрудник.Отчество, 'нет данных') AS Отчество,
            Закупка.Дата AS Дата,
            COALESCE(Животное."Цена", 0) AS "Цена Животного",
            COALESCE(Порода."Вид животного", 'нет данных') AS "Вид животного",
            COALESCE(Корм.Название, 'нет данных') AS "Название корма",
            COALESCE("Вид закупки"."Кол-во корма", 0) AS "Кол-во корма",
            COALESCE(SUM("Вид закупки"."Кол-во корма" * Корм.Цена), 0) AS "Общая цена корма",
            COALESCE(Кормовые_добавки.Название, 'нет данных') AS "Название корм. доб.",
            COALESCE("Вид закупки"."Кол-во кормовых добавок", 0) AS "Кол-во кормовых добавок",
            COALESCE(SUM(Кормовые_добавки.Цена * "Вид закупки"."Кол-во кормовых добавок"), 0) AS "Общая цена корм. доб."
        FROM 
            "Вид закупки"
        LEFT JOIN 
            Животное ON "Вид закупки"."ID животного" = Животное.ID
        LEFT JOIN 
            "Закупка" ON "Вид закупки"."ID закупки" = "Закупка".ID
        LEFT JOIN 
            "Сотрудник" ON "Закупка"."ID сотрудника" = "Сотрудник".ID
        LEFT JOIN 
            "Корм" ON "Вид закупки"."ID корма" = "Корм".ID
        LEFT JOIN 
            "Порода" ON Животное."ID породы" = Порода.ID
        LEFT JOIN 
            "Кормовые добавки" AS Кормовые_добавки ON "Вид закупки"."ID кормовых добавок" = Кормовые_добавки.ID
        WHERE 
            "Вид закупки"."ID закупки" = {record_id}
        GROUP BY 
            "Вид закупки"."ID закупки",
            Сотрудник.Фамилия, 
            Сотрудник.Имя,
            Сотрудник.Отчество,
            Закупка.Дата,
            Животное."Цена",
            Порода."Вид животного",
            Корм.Название,
            "Вид закупки"."Кол-во корма",
            Кормовые_добавки.Название,
            "Вид закупки"."Кол-во кормовых добавок";
        """
        info = execute_sql_query(query)
        if info:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            fields = [
                "ID", "Фамилия", "Имя", "Отчество", "Дата",
                "Цена Животного", "Вид животного", "Название корма",
                "Кол-во корма", "Общая цена корма", "Название корм. доб.",
                "Кол-во кормовых добавок", "Общая цена корм. доб."
            ]
            info_dict = {field: set() for field in fields}
            for row in info:
                for idx, field in enumerate(fields):
                    info_dict[field].add(str(row[idx]))
            for field, values in info_dict.items():
                info_text.insert("end", f"{field}: {', '.join(values)}\n")
            info_text.config(state="disabled")
        else:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            info_text.insert("end", "Информация не найдена.")
            info_text.config(state="disabled")
    else:
        info_text.config(state="normal")
        info_text.delete(1.0, "end")
        info_text.config(state="disabled")
def init_frame11():
    global pursh_tree, pursh_info_text
    pursh_columns = ("ID", "ID сотрудника", "Дата", "Примечания")
    pursh_tree = create_table(frame11, pursh_columns)
    load_data(pursh_tree, sql_query11, create_table_query11)
    pursh_info_text = Text(frame11, wrap="word")
    pursh_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame11, command=pursh_info_text.yview)
    pursh_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame11, text="Удалить", command=del_pursh, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame11, text="Выгрузить данные", width=20, height=3,
                           command=lambda: select_text_file("Закупка", pursh_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame11, text="Добавить", command=open_add_window_purchase, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame11, text="Изменить", command=open_update_window_purchase, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def del_pursh():
    try:
        selection = pursh_tree.selection()
        for item in selection:
            pursh_id = pursh_tree.item(item, 'values')[0]
            execute_sql_query2(
                f"""DELETE FROM "Вид закупки" WHERE "ID закупки" ={pursh_id};
                  DELETE FROM "Закупка" WHERE ID ={pursh_id}""")
            # Вид Закупки
            init_frame5()
            bind_frame5_event_handlers()
            pursh_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def bind_frame11_event_handlers():
    pursh_tree.bind("<<TreeviewSelect>>", lambda event: show_pursh_info(event, pursh_tree, pursh_info_text))
#------------Окно ВИД реализации-------
sql_query6 = """SELECT * FROM  "Вид реализации";"""
create_table_query6 = """
CREATE TABLE IF NOT EXISTS "Вид реализации" (
"ID реализации" integer,
"ID животного" integer
);
"""
def show_viewreal_info(event, tree, info_text):
    item = tree.focus()
    values = tree.item(item, 'values')
    if values:
        viewreal_id = values[0]
        query = f"""
        SELECT 
            COALESCE("Вид реализации"."ID реализации",0) AS "ID реализации", 
            COALESCE(Сотрудник.Фамилия, 'нет данных') AS Фамилия,
            COALESCE(Сотрудник.Имя, 'нет данных') AS Имя,
            COALESCE(Сотрудник.Отчество, 'нет данных') AS Отчество,
            "Реализация"."Дата", 
            COALESCE(Ферма."Название фермы", 'нет данных') AS "Название фермы",
            COALESCE("Животное"."Цена", 0) AS "Цена животного",
            COALESCE(Порода."Вид животного", 'нет данных') AS "Вид животного",
            COALESCE(Животное."Пол",'нет данных') AS "Пол",
            Животное."Возраст",
            COALESCE(Порода."Название",'нет данных') AS "Название породы"
        FROM Животное 
            JOIN "Вид реализации" ON "Вид реализации"."ID животного" = Животное.ID 
            JOIN "Реализация" ON "Вид реализации"."ID реализации" = "Реализация"."id" 
            JOIN "Порода" ON Животное."ID породы" = Порода.ID
            JOIN "Ферма" ON Животное."ID фермы" = Ферма.ID
            JOIN Сотрудник ON "Реализация"."ID сотрудника" = Сотрудник.ID
        WHERE "Вид реализации"."ID реализации"={viewreal_id};
        """
        viewreal_info = execute_sql_query(query)
        if viewreal_info:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            fields = [
                "ID реализации", "Фамилия", "Имя", "Отчество", "Дата",
                "Название фермы","Цена животного", "Вид животного","Пол", "Возраст","Название породы"
            ]
            info_dict = {field: set() for field in fields}
            for row in viewreal_info:
                for idx, field in enumerate(fields):
                    info_dict[field].add(str(row[idx]))
            for field, values in info_dict.items():
                info_text.insert("end", f"{field}: {', '.join(values)}\n")
            info_text.config(state="disabled")
        else:
            info_text.config(state="normal")
            info_text.delete(1.0, "end")
            info_text.insert("end", "Информация о выбранном виде реализации не найдена.")
            info_text.config(state="disabled")
    else:
        info_text.config(state="normal")
        info_text.delete(1.0, "end")
        info_text.config(state="disabled")
def del_viewreal():
    try:
        selection = viewreal_tree.selection()
        for item in selection:
            viewreal_id = viewreal_tree.item(item, 'values')[0]
            id_animal = viewreal_tree.item(item, 'values')[1]
            execute_sql_query2( f"""DELETE FROM "Вид реализации" WHERE "ID реализации" ={viewreal_id} and "ID животного"={id_animal};
                 DELETE FROM "Реализация" WHERE ID ={viewreal_id} and (SELECT COUNT(*) FROM "Вид реализации" WHERE "ID реализации" ={viewreal_id}) = 0 ;""")
            # Реализация
            init_frame12()
            bind_frame12_event_handlers()
            viewreal_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame6():
    global viewreal_tree, viewreal_info_text
    viewreal_columns = ("ID реализации", "ID животного")
    viewreal_tree = create_table(frame6, viewreal_columns)
    load_data(viewreal_tree, sql_query6, create_table_query6)
    viewreal_info_text = Text(frame6, wrap="word")
    viewreal_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame6, command=viewreal_info_text.yview)
    viewreal_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame6, text="Удалить", command=del_viewreal, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame6, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Вид реализации", viewreal_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame6, text="Добавить", command=open_add_window_viewreal, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
def bind_frame6_event_handlers():
    viewreal_tree.bind("<<TreeviewSelect>>", lambda event:show_viewreal_info(event,viewreal_tree, viewreal_info_text))
#-------------Окно РЕАЛИЗАЦИИ---------
sql_query12 = """SELECT * FROM  "Реализация";"""
create_table_query12 = """
CREATE TABLE IF NOT EXISTS "Реализация" (
ID serial primary key,
"ID сотрудника" integer,
"Дата" TIMESTAMP
);
"""
def init_frame12():
    global real_tree, real_info_text
    real_columns = ("ID реализации", "ID сотрудника","Дата")
    real_tree = create_table(frame12, real_columns)
    load_data(real_tree, sql_query12, create_table_query12)
    real_info_text = Text(frame12, wrap="word")
    real_info_text.place(anchor='nw', rely=0.70, relwidth=0.8, relheight=0.30, x=20)
    scrollbar = Scrollbar(frame12, command=real_info_text.yview)
    real_info_text.config(yscrollcommand=scrollbar.set)
    delete_button = Button(frame12, text="Удалить", command=del_real, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame12, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Реализация", real_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame12, text="Добавить", command=open_add_window_real, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame12, text="Изменить", command=open_update_window_real, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
def del_real():
    try:
        selection = real_tree.selection()
        for item in selection:
            real_id = real_tree.item(item, 'values')[0]
            execute_sql_query2(
                f"""DELETE FROM "Вид реализации" WHERE "ID реализации" ={real_id};
                  DELETE FROM "Реализация" WHERE ID ={real_id}""")
            # Вид реализации
            init_frame6()
            bind_frame6_event_handlers()

            real_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def bind_frame12_event_handlers():
    real_tree.bind("<<TreeviewSelect>>", lambda event:show_viewreal_info(event,real_tree, real_info_text))
#---------Окно породы---------
sql_query1 = """SELECT * FROM "Порода";"""
create_table_query1 = """
CREATE TABLE IF NOT EXISTS "Порода" (
    ID serial primary key,
    "Название" varchar(30),
    "Описание" varchar(100),
    "Вид животного" varchar(30)
);

"""
def del_breed():
    try:
        selection=breed_tree.selection()
        for item in selection:
            breed_id = breed_tree.item(item, 'values')[0]
            sql_del = f"""DELETE FROM "Порода" WHERE "Порода".ID={breed_id};
            UPDATE "Животное"
                SET "ID породы"=0
                WHERE "ID породы" = {breed_id};"""
            # Животные
            init_frame1()
            bind_frame1_event_handlers()
            execute_sql_query2(sql_del)
            breed_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame2():
    global breed_tree, breed_info_text
    breed_columns = ("ID", "Название", "Описание", "Вид животного")
    breed_tree = create_table(frame2, breed_columns)
    load_data(breed_tree, sql_query1, create_table_query1)
    delete_button = Button(frame2, text="Удалить", command=del_breed, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame2, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Порода", breed_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame2, text="Добавить", command=open_add_window_breed, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame2, text="Изменить", command=open_update_window_breed, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
#------------Окно Фермы---------
sql_query3 = """SELECT * FROM "Ферма";"""
create_table_query3 = """
CREATE TABLE IF NOT EXISTS "Ферма" (
    ID serial primary key,
    "Название фермы" varchar(30),
    "Местоположение" varchar(50),
    "Площадь (Га)" integer
);
"""
def del_farm():
    try:
        selection=farm_tree.selection()
        for item in selection:
            farm_id = farm_tree.item(item, 'values')[0]
            sql_del = f"""  UPDATE "Животное"
                SET "ID фермы"=0
                WHERE "ID фермы" = {farm_id};
                UPDATE "Должность"
                SET "ID фермы"=0
                WHERE "ID фермы" = {farm_id};
                DELETE FROM "Ферма" WHERE "Ферма".ID={farm_id};"""
            execute_sql_query2(sql_del)
            # Животные
            init_frame1()
            bind_frame1_event_handlers()
            # "Должность"
            init_frame15()
            bind_frame15_event_handlers()
            farm_tree.delete(item)
            messagebox.showinfo("Успешно", "Данные были успешно удалены")
    except Exception as e:
        messagebox.showerror("Произошла ошибка", f"Произошла ошибка при удалении: {e}")
def init_frame3():
    global farm_tree, farm_info_text
    farm_columns = ("ID", "Название фермы", "Местоположение", "Площадь (Га)")
    farm_tree = create_table(frame3, farm_columns)
    load_data(farm_tree, sql_query3, create_table_query3)
    delete_button = Button(frame3, text="Удалить", command=del_farm, width=20, height=3)
    delete_button.place(anchor='ne', rely=0.0, relx=1.0, x=-20)
    delete_button = Button(frame3, text="Выгрузить данные", width=20, height=3,command=lambda: select_text_file("Ферма", farm_tree))
    delete_button.place(anchor='ne', rely=0.1, relx=1.0, x=-20)
    add_button = Button(frame3, text="Добавить", command=open_add_window_farm, width=20, height=3)
    add_button.place(anchor='ne', rely=0.2, relx=1.0, x=-20)
    update_button = Button(frame3, text="Изменить", command=open_update_window_farm, width=20, height=3)
    update_button.place(anchor='ne', rely=0.3, relx=1.0, x=-20)
#--------------Main---------------------
root = Tk()
root.title("Животноводческое сельскохозяйственное предприятие ")
root.geometry("1080x720")
menu_bar = Menu(root)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Архивировать", command=export_data_to_file)
edit_menu = Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Затраты",command=open_OTCHET_zatraty)
edit_menu.add_command(label="Прибыль(Реализация)",command=open_OTCHET_pribyl)
edit_menu.add_command(label="Динамика общей стоимости закупок и общей цены продаж",command=open_OTCHET_dinamika)
edit_menu.add_command(label="Численность животных",command=open_OTCHET_chislennost)
edit_menu.add_command(label="Распределение животных",command=open_OTCHET_raspredelenie)
menu_bar.add_cascade(label="База данных", menu=file_menu)
menu_bar.add_cascade(label="Отчет", menu=edit_menu)
root.config(menu=menu_bar)
notebook = ttk.Notebook(root)
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)
frame3 = ttk.Frame(notebook)
frame4 = ttk.Frame(notebook)
frame5 = ttk.Frame(notebook)
frame6 = ttk.Frame(notebook)
frame7 = ttk.Frame(notebook)
frame8 = ttk.Frame(notebook)
frame9 = ttk.Frame(notebook)
frame10 = ttk.Frame(notebook)
frame11 = ttk.Frame(notebook)
frame12 = ttk.Frame(notebook)
frame13 = ttk.Frame(notebook)
frame14 = ttk.Frame(notebook)
frame15 = ttk.Frame(notebook)
frame16 = ttk.Frame(notebook)
frame17 = ttk.Frame(notebook)
notebook.add(frame1, text="Животные")
notebook.add(frame2, text="Порода")
notebook.add(frame3, text="Ферма")
notebook.add(frame4, text="Сотрудник")
notebook.add(frame5, text="Вид Закупки")
notebook.add(frame6, text="Вид Реализации")
notebook.add(frame7, text="Контакты")
notebook.add(frame8, text="Корм")
notebook.add(frame9, text="Корм добавки")
notebook.add(frame10, text="Зарплата")
notebook.add(frame11, text="Закупка")
notebook.add(frame12, text="Реализация")
notebook.add(frame13, text="Схема оплаты")
notebook.add(frame14, text="График работы")
notebook.add(frame15, text="Должность")
notebook.add(frame16, text="Животное и рацион")
notebook.add(frame17, text="Рацион")
notebook.pack(expand=True, fill="both")
#Животные
init_frame1()
bind_frame1_event_handlers()
#Сотрудник
init_frame4()
bind_frame4_event_handlers()
#Вид Закупки
init_frame5()
bind_frame5_event_handlers()
#Вид реализации
init_frame6()
bind_frame6_event_handlers()
#Ферма
init_frame3()
#Порода
init_frame2()
#Контакты
init_frame7()
bind_frame7_event_handlers()
#Корм
init_frame8()
#Кормовые добавки
init_frame9()
#Зарплата
init_frame10()
#Закупка
init_frame11()
bind_frame11_event_handlers()
#Реализация
init_frame12()
bind_frame12_event_handlers()
#"Схема оплаты"
init_frame13()
bind_frame13_event_handlers()
#"График работы"
init_frame14()
bind_frame14_event_handlers()
#"Должность"
init_frame15()
bind_frame15_event_handlers()
#"Животное и рацион"
init_frame16()
bind_frame16_event_handlers()
#"Рацион"
init_frame17()
bind_frame17_event_handlers()
root.mainloop()



