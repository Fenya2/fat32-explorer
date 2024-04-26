def get_bpb(image):
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


def get_fat_address(bpb):
    """
    Возвращает адрес таблицы fat (первой)
    """
    return bpb['BPB_RsvdSecCnt'] * bpb['BPB_BytsPerSec']


def get_root_address(bpb):
    """
    Возвращает адрес корневого каталога
    """
    return (
        bpb['BPB_RsvdSecCnt']
        + bpb['BS_DrvNum'] * bpb['BPB_NumFATs']
        + (bpb['BPB_RootClus'] - 2) * bpb['BPB_SecPerClus']) * bpb['BPB_BytsPerSec']


def get_cluster_address(clID, bpb):
    """
    Возвращает адрес кластера с указанным номером
    """
    return get_root_address(bpb) + (clID - 2) * \
        bpb['BPB_SecPerClus'] * bpb['BPB_BytsPerSec']


def get_cluster(clID, image, bpb):
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
    ALL - выделенный кластер #TODO
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


def get_file_clusters(clusterID, image, bpb):
    """
    Возвращает список кластеров, принадлежащих файлу с начальным кластером
    cluster id, пробегая по таблице fat
    """
    clusters = []
    cur_cl = clusterID
    while get_cluster_state(cur_cl) == 'LINK':
        clusters.append(cur_cl)
        cur_cl = fat_of(cur_cl)
    return clusters


def ls_dir(directory_clusters: list, image, bpb):
    """
    Возвращает список файлов с информацией о них в указанной директории
    (список кластеров, принадлежащих директории)
    """
    file_entries = []
    for clusterID in directory_clusters:
        cluster = get_cluster(clusterID, image, bpb)
        file_entries += get_file_entries_in(cluster)
    # TODO здесь надо "склеивать" LFN с их SFN (срезы)
    pass


def get_file_entries_in(cluster: bytes):
    """
    Возвращает список файловых записей в кластере принадлежащем директории
    (байты) (неудаленных)
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
    if entry_is_end(entry):
        return 'end'
    if entry_is_removed(entry):
        return 'rm'

    match define_file_entry(entry):
        case 'sfn':
            return parse_sfn_entry(entry)
        case 'lfn':
            return parse_sfn_entry(entry)
        case _:
            return None


def entry_is_end(entry: bytes):
    """
    Проверяет, что записей после текущей больше нет (включая ее) больше нет
    в кластере директории
    """
    return entry[0] == 0x00


def entry_is_removed(entry: bytes):
    """
    Проверяет, удален ли файл с переданной файловой записью
    """
    return entry[0] == 0xe5 or entry[0] == 0x05


def define_file_entry(entry: bytes):
    """
    Определяет тип файловой записи по ее сигнатуре
    (подразумевается, что файл не удален)
    Возвращает 'sfn' или 'lfn'.
    """
    return 'lfn' if entry[0xb] == 0xf else 'sfn'


def parse_lfn_entry(entry: bytes):
    """
    Разбирает файловую запись типа LFN.
    Возвращает словарь с заполненными полями
    Складывает части названия файла
    - type: 'lfn'
    - name_part: часть имени файла
    """
    # TODO
    lfn = {'type': 'lfn'}
    raise ValueError("nee write")
    return lfn


def parse_sfn_entry(entry: bytes):
    """
    Разбирает файловую запись типа SFN.
    Возвращает словарь с заполненными полями
    entry: sfn
    name: имя в DOS(8.3) формате.
    type: 'dir' или 'file'
    clusterID: начальный номер кластера файла
    size: размер файла
    # TODO дописать еще атрибутов
    """
    sfn = {'entry': 'sfn'}
    sfn['name'] = get_name_from_sfn(entry[0:11])
    sfn['type'] = get_attr_from_sfn(entry[11])
    sfn['clusterID'] = get_clusterID_from_sfn(entry)
    sfn['size'] = get_size_from_sfn(entry[28:32])
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
