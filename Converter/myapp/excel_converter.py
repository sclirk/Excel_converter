import pandas as pd


class Convert:
    def __init__(self,
                 excel_file_path='D:/test_task_2/media/documents'
                                 '/Excel_file.xls',
                 csv_file_path='D:/test_task_2/media/Converted_files/Excel_file.csv'):
        read_file = pd.read_excel(excel_file_path, encoding='windows-1251')
        read_file.to_csv(csv_file_path, encoding='windows-1251', index=None, header=True)


# Конвертер файла в .csv формат с указанной кодировкой "windows-1251"
