CLUSTER_TAGS = {
    'ENDOFCLS':   0x0FFFFFFF,
    'ALLOCATED':  0xFFFFFFF2,
    'RESERVED':   0x0FFFFFF6,
    'BAD':        0xFFFFFFF2,
    'TABLE_SIGN': 0x0FFFFFF8
}


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
    Возвращает адрес таблицы fat
    """
    return bpb['BPB_RsvdSecCnt'] * bpb['BPB_BytsPerSec']


def get_cluster(clID, image, bpb):
    """
    Возвращает содержимое кластера с переданным номером
    """
    cl_addr = get_root_address(bpb) + (clID - 2) * \
        bpb['BPB_SecPerClus'] * bpb['BPB_BytsPerSec']
    image.seek(cl_addr)
    return image.read(bpb['BPB_SecPerClus'] * bpb['BPB_BytsPerSec'])


def fat_of(clID, image, bpb):
    """
    Возвращает значение в таблице fat для указанного кластера
    """
    image.seek(get_fat_address(bpb) + 4 * clID)
    return int.from_bytes(image.read(4), 'little')


def get_root_address(bpb):
    """
    Возвращает адрес корневого каталога
    """
    return (
        bpb['BPB_RsvdSecCnt']
        + bpb['BS_DrvNum'] * bpb['BPB_NumFATs']
        + (bpb['BPB_RootClus'] - 2) * bpb['BPB_SecPerClus']) * bpb['BPB_BytsPerSec']


def get_file(clusterID, image, bpb):
    """
    Возвращает файл, с начальным кластером clusterID, пробегая по
    таблице fat
    """
    cur_cl = clusterID
    file = b''
    while not any(cur_cl == i for i in CLUSTER_TAGS.values()):
        file += get_cluster(cur_cl, image, bpb)
        cur_cl = fat_of(cur_cl, image, bpb)
    return file


def ls_dir(directory):
    """
    Возвращает список файлов с информацией о них в указанной директории
    (байты)
    """
    file_entries = get_file_entries_in(directory)
    # здесь надо "склеивать" LFN с их SFN (срезы)
    pass


def get_file_entries_in(directory):
    """
    Возвращает список файловых записей в директории (считается,
    что передан файл директории)
    """
    entries = []
    for i in range(0, len(directory), 32):
        entry = get_file_entry(directory[i:i+32])
        if entry is None:
            break
        entries.append(entry)
    return entries


def get_file_entry(entry):
    """
    Возвращает разобранную файловую запись (в виде словаря). Если переданные
    32 байта не запись, возвращает None
    """
    match define_file_entry(entry):
        case 'SFN':
            return parse_SFN
        case 'LFN':
            return parse_LFN
        case _:
            return None


def define_file_entry(entry):
    """
    Определяет тип файловой записи по ее сигнатуре
    Возвращает 'SFN', 'LFN' или None соответственно
    """
    pass


def parse_LFN(entry):
    """
    Разбирает файловую запись типа LFN.
    Возвращает словарь с заполненными полями
    """
    pass


def parse_SFN(entry):
    """
    Разбирает файловую запись типа SFN.
    Возвращает словарь с заполненными полями
    """
    pass
