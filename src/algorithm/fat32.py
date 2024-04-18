class Fat32:
    """
    Объект, работающий с образом fat32
    """

    def __init__(self, fat_path):
        # TODO написать корректное определение фс (считаем, что пока все гуд)
        self.image = open(fat_path, 'rb')
        self._bpb = self.extract_bpb_data(self.image)
        self._fat_table = self.save_fat_table(self.image, self._bpb)

    def extract_bpb_data(self, image):
        """
        Извлекает нужные данные из нулевого сектора bpb, сохраняет в словарь
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
        image.seek(0x43)
        ret['BS_VolID'] = int.from_bytes(image.read(4), 'little')
        ret['BS_VolLab'] = image.read(11).decode('ascii')
        ret['BS_FilSysType'] = image.read(8).decode('ascii')
        return ret

    def save_fat_table(self, image, bpb):
        """
        Возвращает считанную таблицу fat
        """
        pass
