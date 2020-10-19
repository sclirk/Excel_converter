from django.shortcuts import redirect, render
from .models import Document
from .forms import DocumentForm
import psycopg2
import pandas as pd
from .excel_converter import Convert
import os

myConnection = psycopg2.connect(dbname="127.0.0.1",
                                user='root',
                                passwd='1111',
                                db='execute_schema')  # Коннектор к бд

myConnection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

def read_all_database():  # Функция чтения всех данных с заданных колонок
    column_names = [
        'ID',
        'bank_id',
        'opening_passive',
        'opening_actived',
        'outgoing_passive',
        'outgoing_actived',
        'debit',
        'credit'
    ]

    output = '''
        SELECT  MAIN.id as {}, 
                MAIN.bank_id as {},
                A.passive as {}, 
                A.actived as {},
                B.passive as {}, 
                B.actived as {},
                C.debit as {}, 
                C.credit as {}
        FROM turnover_sheet.bank_id as MAIN
        JOIN turnover_sheet.opening_balance as A ON MAIN.id=A.id
        JOIN turnover_sheet.outgoing_balance as B ON MAIN.id=B.id
        JOIN turnover_sheet.turnover as C ON MAIN.id=C.id;
    '''.format(*column_names)  # Единый запрос в бд, 'multi = True' - не работает

    cursor = myConnection.cursor()
    cursor.execute(output)
    opb_fethll = cursor.fetchall()  # Предоставляет все данных из бд

    items = []

    for column in opb_fethll:
        item = {}
        for i, c in enumerate(column_names):
            item[c] = column[i]
        items.append(item)  # Дополнение списка значениями из бд

    context = {
        'items': items,
        'column_names': column_names
    }  # Передача данных по форме в html файл

    return context


def my_view(request):
    message = 'Upload Excel file'

    doc_name = request.GET.get('docname', None)  # Получение названия документа из загруженных в бд файлов

    if doc_name is not None:
        local_excel_path = './media/' + doc_name  # Путь к файлу с его именем
        local_csv_path = os.path.splitext(local_excel_path)[0] + '.csv'  # Разделение файла на его название и тип файла,
        # переименование в .csv
        Convert(excel_file_path=local_excel_path, csv_file_path=local_csv_path)
        # Замена пути для csv файла

        db_writer = ExcelConverter(csv_file_path=local_csv_path)
        db_writer.delete_old_rows()
        db_writer.dataframe()
        # Чтение и перезапись данных в БД

        context = read_all_database()

        context['link'] = '/media/{}'.format(os.path.splitext(doc_name)[0] + '.csv')
        # Создание ссылки на чтение файлов с разными

        return render(request, 'convert.html', context)

    if request.method == 'POST':
        newdoc = Document(docfile=request.FILES['docfile'])
        newdoc.save()
        # Сохранение выбранного пользователем документа в базу
        return redirect('my-view')

    else:
        form = DocumentForm()  # Подсказка для выбора файла, если тот не был выбрал

    documents = Document.objects.all()
    # Отображение объектов из базы загруженных

    context = {'documents': documents, 'form': form, 'message': message}
    # Передача форм, базы и сообщения в html файл
    return render(request, 'list.html', context)


class ExcelConverter:
    def __init__(self, csv_file_path='C:/Users/spectra/Desktop/Excel_file.csv'):
        self.myConnection = psycopg2.connect(dbname="127.0.0.1",
                                             user='root',
                                             passwd='1111',
                                             db='execute_schema')
        self.myConnection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.myConnection.cursor()
        self.data = pd.read_csv(csv_file_path, encoding='cp1251')
        self.nan_value = float("NaN")
        self.delete_turnover = "DELETE FROM turnover_sheet.opening_balance; "
        self.delete_out_balance = "DELETE FROM turnover_sheet.outgoing_balance; "
        self.delete_in_balance = "DELETE FROM turnover_sheet.turnover"
        self.delete_bank_id = "DELETE FROM turnover_sheet.bank_id"
        self.id = 0
        self.df = pd.DataFrame(self.data, columns=['Название банка', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3',
                                                   ' ', "Unnamed: 5", 'Unnamed: 6']).drop(list(range(7)))

    def delete_old_rows(self):
        # Очистка старых значений
        self.cursor.execute(self.delete_turnover)
        self.myConnection.commit()
        self.cursor.execute(self.delete_out_balance)
        self.myConnection.commit()
        self.cursor.execute(self.delete_in_balance)
        self.myConnection.commit()
        self.cursor.execute(self.delete_bank_id)
        self.myConnection.commit()

    def dataframe(self):
        self.df.rename(columns={'Название банка': 'ID', 'Unnamed: 1': 'in_sald_act', 'Unnamed: 2': 'in_sald_pass',
                                'Unnamed: 3': 'debit', ' ': 'credit', 'Unnamed: 5': 'out_sald_act',
                                'Unnamed: 6': 'out_sald_pass'}, inplace=True)
        # Переименование полученных колон под нужный excel файл

        self.df.replace("", self.nan_value, inplace=True)
        self.df.dropna(subset=["in_sald_act"], inplace=True)
        self.df.drop(self.df.loc[self.df['ID'] == "БАЛАНС"].index, inplace=True)
        # Пропуск пустых строк
        
        for row in self.df.itertuples():
          # Поиск строк в датафрейме и вставка значений в них
            self.id += 1
            update_bank_id = "INSERT INTO turnover_sheet.bank_id (ID, bank_id)" \
                             " VALUES (%s, %s);"
            update_bank_id_execute = (self.id, row.ID)
            self.cursor.execute(update_bank_id, update_bank_id_execute)
            self.myConnection.commit()
            update_out_sald = "INSERT INTO turnover_sheet.outgoing_balance (ID, actived, passive)" \
                              " VALUES (%s, %s, %s);"
            out_sald_execute = (self.id, row.out_sald_act, row.out_sald_pass)
            self.cursor.execute(update_out_sald, out_sald_execute)
            self.myConnection.commit()
            update_in_sald = "INSERT INTO turnover_sheet.opening_balance (ID, actived, passive)" \
                             " VALUES (%s, %s, %s);"
            in_sald_execute = (self.id, row.in_sald_act, row.in_sald_pass)
            self.cursor.execute(update_in_sald, in_sald_execute)
            self.myConnection.commit()
            update_turnover = "INSERT INTO turnover_sheet.turnover (ID, debit, credit)" \
                              " VALUES (%s, %s, %s);"
            turnover_execute = (self.id, row.debit, row.credit)
            self.cursor.execute(update_turnover, turnover_execute)
            self.myConnection.commit()
            # Вставка значений, multi не работает

            
