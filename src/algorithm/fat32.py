from datetime import datetime, date, time
from bitarray import bitarray


class Fat32:
    """
    Класс, позволяющий обозревать файловую систему fat32.
    Хранит рабочий каталог и список файлов в нем. Основные 4 команды(методы):
    - cd <dir> - сменить рабочий каталог
    - ls - просмотреть файлы в текущем каталоге
    - сat <file> - просмотреть содержимое файла
    - pwd - вывести путь к рабочему каталогу, относительно корневого
    """

    def __init__(self):
        self.image = None
        self.bpb = None
        self.cur_path = None
        self.cur_directory_clusters = None
        self.cur_directory_files = None

    def open(self, filepath):
        """
        Открывает файл с размеченной на нем fat32,
        устанавливает рабочий каталог на корневой, сохраняет его кластеры
        """
        self.image = open(filepath, 'rb')
        self.bpb = get_bpb(self.image)
        self.cur_path = []
        self.cur_directory_clusters = get_file_clusters(
            self.bpb['BPB_RootClus'],
            self.image,
            self.bpb
        )

    def close(self):
        """
        Закрывает файл с fat32
        """
        if self.image is not None:
            self.image.close()

    def ls(self):
        """
        Возвращает список файлов в текущей директории из атрибута, если
        их уже читали, иначе, берет из фс
        """
        if self.cur_directory_files is None:
            self.cur_directory_files = ls_dir(
                self.cur_directory_clusters,
                self.image,
                self.bpb
            )
        return self.cur_directory_files

    def cd(self, dir_name: str):
        """
        Меняет текущую директорию на директорию, лежащую в текущей.
        Если такой директории нет, поднимает исключение.
        Рассматриваются 3 случая:
        1 - переход в . - текущий каталог - ничего не делает
        2 - переход в родительский каталог (..)
            2.1 - родительский каталог является корневым
            2.2 - родительский каталог не является корневым
        3 - остальные случаи
        Во всех случаях, кроме первого чистит "кеш" файлов в текущей директории
        """
        file = self._find_in_cur_dir_file_with_name(dir_name)
        if file['type'] != 'dir':
            raise ValueError("This file is not directory")
        if file['name'] == '.':  # если текущий
            return
        self.cur_directory_files = None
        if file['name'] == '..':  # если родительский
            if file['clusterID'] == 0:  # если родительский - корневой
                self.cur_path = []
                self.cur_directory_clusters = get_file_clusters(
                    self.bpb['BPB_RootClus'],
                    self.image,
                    self.bpb
                )
            else:  # если родительский - не корневой
                self.cur_directory_clusters = get_file_clusters(
                    file['clusterID'],
                    self.image,
                    self.bpb
                )
                self.cur_path.pop()
        else:  # если не родительский
            self.cur_directory_clusters = get_file_clusters(
                file['clusterID'],
                self.image,
                self.bpb
            )
            self.cur_path.append(file['name'])

    def cat(self, file_name: str):
        """
        возвращает содержимое файла c именем file в текущей директории.
        Если файла с таким именем нет, поднимает исключение
        """
        file = self._find_in_cur_dir_file_with_name(file_name)
        if file['type'] != 'file':
            raise ValueError("This file is not file. it's directory")
        return get_file(file, self.image, self.bpb)

    def pwd(self):
        """
        Возвращает текущий рабочий каталог
        """
        return '/'+'/'.join(self.cur_path)

    def _find_in_cur_dir_file_with_name(self, name: str):
        """
        находит в текущей директории файл с переданным именем. Если файл
        не находится, поднимает исключение. Иначе возвращает этот файл
        """
        for file in self.ls():
            if file['name'] == name:
                return file
        raise ValueError('No such file or directory')


def get_bpb(image) -> dict:
    """
    Извлекает нужные данные из нулевого сектора bpb, сохраняет в словарь
    и возвращает его
    """
    ret = {}
    image.seek(0xb)
    ret['BPB_BytsPerSec'] = int.from_bytes(image.read(2), 'little')
    ret['BPB_SecPerClus'] = int.from_bytes(image.read(1))
    ret['BPB_RsvdSecCnt'] = int.from_bytes(image.read(2), 'little')
    ret['BPB_NumFATs'] = int.from_bytes(image.read(1))
    image.seek(0x20)
    ret['BPB_TotSec32'] = int.from_bytes(image.read(4), 'little')
    ret['BS_DrvNum'] = int.from_bytes(image.read(2), 'little')
    image.seek(0x2c)
    ret['BPB_RootClus'] = int.from_bytes(image.read(2), 'little')
    image.seek(0x43)
    ret['BS_VolID'] = int.from_bytes(image.read(4), 'little')
    ret['BS_VolLab'] = image.read(11).decode('ascii')
    ret['BS_FilSysType'] = image.read(8).decode('ascii')
    return ret


def get_fat_address(bpb) -> int:
    """
    Возвращает адрес таблицы fat (первой)
    """
    return bpb['BPB_RsvdSecCnt'] * bpb['BPB_BytsPerSec']


def get_root_address(bpb) -> int:
    """
    Возвращает адрес корневого каталога
    """
    return (
        bpb["BPB_RsvdSecCnt"]
        + bpb["BS_DrvNum"] * bpb["BPB_NumFATs"]
        + (bpb["BPB_RootClus"] - 2) * bpb["BPB_SecPerClus"]
    ) * bpb["BPB_BytsPerSec"]


def get_cluster_address(clID, bpb) -> int:
    """
    Возвращает адрес кластера с указанным номером
    """
    return get_root_address(bpb) + (clID - 2) * \
        bpb['BPB_SecPerClus'] * bpb['BPB_BytsPerSec']


def get_cluster(clID, image, bpb) -> bytes:
    """
    Возвращает содержимое кластера с переданным номером
    """
    cl_addr = get_cluster_address(clID, bpb)
    image.seek(cl_addr)
    return image.read(bpb['BPB_SecPerClus'] * bpb['BPB_BytsPerSec'])


def fat_of(clID, image, bpb):
    """
    Возвращает значение в таблице fat для указанного кластера
    """
    image.seek(get_fat_address(bpb) + 4 * clID)
    return int.from_bytes(image.read(4), 'little')


def get_cluster_state(fatContent):
    """
    По значению из таблицы fat возвращает состояние кластера:
    EOF - конец файла
    BAD - битый или потерянный кластер
    RES - зарезервированный кластер
    ALL - выделенный кластер
    FREE - свободный кластер
    LINK - ссылка на следующий кластер
    """
    if fatContent >= 0x0FFFFFF8:
        return 'EOF'
    if fatContent == 0x0FFFFFF7:
        return 'BAD'
    if fatContent == 0x0FFFFFF6:
        return 'RES'
    if fatContent == 0x00000002:
        return 'ALL'
    if fatContent == 0x00000000:
        return 'FREE'
    return 'LINK'


def get_file(file: dict, image, bpb) -> bytes:
    """
    Возвращает содержимое файла по его информации из директории
    (по сути перегруженный get_file_with_start_cluster)
    """
    return get_file_with_start_cluster(
        file['clusterID'],
        file['size'],
        image,
        bpb)


def get_file_with_start_cluster(
        clusterID: int, size: int, image, bpb) -> bytes:
    """
    Возвращает содержимое файла с стартовым кластером clusterID и размером size
    """
    file_clusters = get_file_clusters(clusterID, image, bpb)
    data = b''
    for cluster in file_clusters:
        data += get_cluster(cluster, image, bpb)
    return data[0:size]


def get_file_clusters(clusterID, image, bpb):  # TODO test exist need one more
    """
    Возвращает список кластеров, принадлежащих файлу с начальным кластером
    cluster id, пробегая по таблице fat
    """
    clusters = [clusterID]
    cur_cl = fat_of(clusterID, image, bpb)
    while get_cluster_state(cur_cl) == 'LINK':
        clusters.append(cur_cl)
        cur_cl = fat_of(cur_cl, image, bpb)
    return clusters


def ls_dir(directory_clusters: list, image, bpb: dict):
    """
    Возвращает список файлов (словарей) с информацией о них
    в указанной директории (список кластеров, принадлежащих директории)
    структура файла:
    name: имя
    type: 'dir' или 'file'
    clusterID: начальный номер кластера файла
    size: размер файла
    """
    # получение файловых записей всей директории
    file_entries = []
    for clusterID in directory_clusters:
        cluster = get_cluster(clusterID, image, bpb)
        file_entries += get_file_entries_in(cluster)

    return get_files_from_file_entries(file_entries)


def get_files_from_file_entries(file_entries: list):
    """
    Возвращает список файлов по переданному списку файловых записей
    (должен быть корректным) ("схлопывает" lfn и sfn записи вместе")
    name: имя файла (строка)
    type: 'dir' или 'file'
    clusterID: начальный номер кластера файла
    size: размер файла
    """
    files = []
    common_lfns = []
    for entry in file_entries:
        if entry['entry'] == 'sfn':
            if common_lfns:
                entry['name'] = extract_name_from_lfns(common_lfns)
                common_lfns = []
            del entry['entry']
            files.append(entry)
        elif entry['entry'] == 'lfn':
            common_lfns.append(entry)
        else:
            raise ValueError("not recognized entry type")
    return files


def extract_name_from_lfns(lfns: list):
    """
    Возвращает сформированное имя из списка переданных lfn-записей
    (считается, что они предшествуют своей sfn-записи)
    """
    byte_name = b''
    for lfn in reversed(lfns):
        byte_name += lfn['name_part']
    name = str(byte_name, 'utf16')
    zero_index = name.find('\u0000')
    if zero_index == -1:
        return name
    return name[0:zero_index]


def get_file_entries_in(cluster: bytes):
    """
    Возвращает список файловых записей в кластере, принадлежащем директории
    (неудаленных)
    """
    entries = []
    for i in range(0, len(cluster), 32):
        entry = get_file_entry(cluster[i:i+32])
        if entry == 'end':
            break
        if entry == 'rm':
            continue
        entries.append(entry)
    return entries


def get_file_entry(entry: bytes):
    """
    Возвращает разобранную файловую запись (Если это корректная неудаленная
    запись LFN или SFN. Если SFN, то файл или директория) в виде словаря.
    Если запись удалена или это конец директории, возвращает 'rm' или 'end'
    соответственно.
    """
    if entry_is_end(entry[0]):
        return 'end'
    if entry_is_removed(entry[0]):
        return 'rm'

    match define_file_entry(entry[0xb]):
        case 'sfn':
            return parse_sfn_entry(entry)
        case 'lfn':
            return parse_lfn_entry(entry)
        case _:
            return None


def entry_is_end(entry: int):
    """
    Проверяет, что записей после текущей больше нет (включая ее) больше нет
    в кластере директории
    """
    return entry == 0x00


def entry_is_removed(name_first_byte: int):
    """
    Проверяет, удален ли файл с переданной файловой записью,
    смотря на первый символ имени
    """
    return name_first_byte == 0xe5


def define_file_entry(attribute: int):
    """
    Определяет тип файловой записи по ее атрибуту
    (подразумевается, что файл не удален)
    Возвращает 'sfn' или 'lfn'.
    """
    return 'lfn' if attribute == 0xf else 'sfn'


def parse_lfn_entry(entry: bytes):
    """
    Разбирает файловую запись типа LFN.
    Возвращает словарь с заполненными полями:
    - entry: 'lfn'
    - name_part: байты - части имени
    """
    lfn = {'entry': 'lfn'}
    lfn['name_part'] = entry[1:11] + entry[14:26] + entry[28:32]
    return lfn


def parse_sfn_entry(entry: bytes):
    """
    Разбирает файловую запись типа SFN.
    Возвращает словарь с заполненными полями
    entry: sfn
    name: имя в DOS(8.3) формате
    type: 'dir' или 'file'
    clusterID: начальный номер кластера файла
    size: размер файла
    date_cr: дата создания файла (дата и время)
    date_wr: дата последнего изменения файла
    # TODO дописать еще атрибутов
    """
    sfn = {'entry': 'sfn'}
    sfn['name'] = get_name_from_sfn(entry[0:11])
    sfn['type'] = get_attr_from_sfn(entry[11])
    sfn['clusterID'] = get_clusterID_from_sfn(entry)
    sfn['size'] = get_size_from_sfn(entry[28:32])
    sfn['date_cr'] = get_datetime_from_sfn(entry[14:18])
    sfn['date_wr'] = get_datetime_from_sfn(entry[22:26])
    return sfn


def get_name_from_sfn(DIR_Name: bytes):
    """
    Возвращает строку из поля name записи sfn
    """
    name = DIR_Name[0:8].decode('ascii').strip()
    extension = DIR_Name[8:11].decode('ascii').strip()
    return f'{name}.{extension}' if extension != '' else name


def get_attr_from_sfn(entry: int):
    """
    Разбирает поле атрибутов (1 байт) в записи sfn
    """
    # TODO правильное ли определение? мб использовать маску?
    return 'dir' if entry == 0x10 else 'file'


def get_clusterID_from_sfn(entry: bytes):
    """
    Возвращает номер начального кластера для файла с переданной sfn
    """
    return int.from_bytes(entry[26:28] + entry[20:22], 'little')


def get_size_from_sfn(size_field: bytes):
    """
    Возвращает размер файла по полю в его файловой записи
    """
    return int.from_bytes(size_field, 'little')


def get_datetime_from_sfn(datetime: bytes) -> datetime:
    """
    Возвращает дату и время (создания или последнего изменения)
    по переданным 4 байтам записи sfn (2 на время (DIR_CrtTime/DIR_WrtTime),
    2 на дату(DIR_CrtDate/DIR_WrtDate))
    """
    # time = get_time_from_sfn(datetime[0:2])
    # date = get_date_from_sfn(datetime[2:4])
    # return datetime.combine(date, time)


def get_date_from_sfn(date_field: bytes) -> date:
    """
    Возвращает дату создания/последнего_изменения файла по 2 переданным
    байтам
    """
    pass


def get_time_from_sfn(time_field: bytes) -> time:
    """
    Возвращает время создания/последнего_изменения файла по 2 переданным
    байтам (по гринвичу)
    """
    bits = bitarray(endian='little')
    bits.frombytes(time_field)
    bits.reverse()
    print(bits)
    hours = bitarray('000') + bits[0:5]
    print(hours)
    hours = int.from_bytes(hours.tobytes())
    minutes = bitarray('00') + bits[5:11]
    print(minutes)
    minutes = int.from_bytes(minutes.tobytes())
    seconds = bitarray('000') + bits[11:16]
    print(seconds)
    seconds = int.from_bytes(seconds.tobytes()) * 2
    return time(hours, minutes, seconds)
