# Введение
Программа с графическим интерфейсом - обозреватель файловой системы [fat32](https://ru.wikipedia.org/wiki/FAT).



# Требования
- [python3](https://www.python.org/downloads/)



# Установка
## linux
1. Клонировать репозиторий
```bash
git clone git@github.com:Fenya2/python-task.git
```

2. Перейти в директорию с проектом
```bash
cd ./python-task/
```

3. *(опционально)* Создать виртуальное окружение python и активировать его
```bash
python3 -m venv ./.venv
source ./.venv/bin/activate
```

4. Установить зависимости проекта
```bash
pip3 intall -r ./requirements.txt
```

5. Запустить программу
```bash
python3 ./run.py
```


## windows
1. Клонировать репозиторий
```
git clone git@github.com:Fenya2/python-task.git
```

2. Перейти в директорию с проектом
```
cd .\python-task\
```

3. *(опционально)* Создать виртуальное окружение python и активировать его
```powershell
python -m venv .\.venv
.\.venv\Scripts\activate
```

4. Установить зависимости проекта
```powershell
pip install -r .\requirements.txt
```

5. Запустить программу
```powershell
python .\run.py
```

***
***

# ТЗ
## Программа должна
- обозревать директории в файловой системе fat32 (файлы и другие директории)
- просматривать содержимое файлов с метаинформацией о каждом:
    - размер файла (в байтах)
    - дата и время создания файла
    - дата и время последнего изменения файла


# Тестирование
> ВНИМАНИЕ: Для тестирования необходимы тестовые файлы (с образами, кластерами и т.д.). Так как они довольно большие, они лежат в [архиве](https://drive.google.com/drive/folders/1J6Yq9kYr8EbLpzG9aj_9P4hHpB_40BXo?usp=sharing), который надо распаковать в tests/resources/ (относительно корня проекта)

> Также для корректной работы тестов необходимо примонтировать раздел в volume.fat32 (лежит в архиве) к mount_point/ (относительно корня проекта)

## unittest
Запускать следующей командой из корня проекта:
### linux
```bash
python3 -m unittest discover -v -s ./tests/algorithm/ -p "test_*.py"
```
### windows
```powershell
python -m unittest discover -v -s .\tests\algorithm\ -p "test_*.py"
```

## coverage
Выполнять следующими командами из корня проекта:
1. Запустить скрипт, анализирующий покрытие проекта тестами
### linux
```bash
coverage run --source ./src/algorithm/ -m unittest discover -q -s ./tests/algorithm/ -p "test_*.py"
```
### windows
```powershell
coverage run --source .\src\algorithm\ -m unittest discover -q -s .\tests\algorithm\ -p "test_*.py"
```
2. Посмотреть отчет
```bash
coverage report
```

## flake8
Запускать из корня проекта следующей командой
```bash
flake8 src tests
```

## In total
Можно запустить скрипт в корне проекта,
который выполнит проверки выше автоматически
```bash
python3 test_script.py
```
