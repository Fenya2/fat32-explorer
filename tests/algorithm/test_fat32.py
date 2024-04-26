import unittest
import src.algorithm.fat32 as fs


class Test_(unittest.TestCase):
    def test_get_bpb(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            self.assertEqual(0x200, bpb['BPB_BytsPerSec'])
            self.assertEqual(8, bpb['BPB_SecPerClus'])
            self.assertEqual(0x20, bpb['BPB_RsvdSecCnt'])
            self.assertEqual(2, bpb['BPB_NumFATs'])
            self.assertEqual(0x1ffff8, bpb['BPB_TotSec32'])
            self.assertEqual(0x800, bpb['BS_DrvNum'])
            self.assertEqual(0x0a40330b, bpb['BS_VolID'])
            self.assertEqual('NO NAME    ', bpb['BS_VolLab'])
            self.assertEqual('FAT32   ', bpb['BS_FilSysType'])
            self.assertEqual(2, bpb['BPB_RootClus'])

    def test_get_fat_address(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            fat_addr = fs.get_fat_address(bpb)
            self.assertEqual(0x4000, fat_addr)

    def test_get_root(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            root_address = fs.get_root_address(bpb)
            self.assertEqual(0x204000, root_address)

    def test_get_cluster_address(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            root_cls = bpb['BPB_RootClus']
            self.assertEqual(0x204000, fs.get_cluster_address(root_cls, bpb))
            self.assertEqual(0x206000, fs.get_cluster_address(4, bpb))

    def test_get_cluster_state(self):
        """
        Проверяет, как проверяется состояние кластера по таблице fat
        """
        self.assertEqual(fs.get_cluster_state(0x0FFFFFF8), 'EOF')
        self.assertEqual(fs.get_cluster_state(0x0FFFFFFF), 'EOF')
        self.assertEqual(fs.get_cluster_state(0x0FFFFFF7), 'BAD')
        self.assertEqual(fs.get_cluster_state(0x0FFFFFF6), 'RES')
        self.assertEqual(fs.get_cluster_state(0x00000002), 'ALL')
        self.assertEqual(fs.get_cluster_state(0x00000000), 'FREE')
        self.assertEqual(fs.get_cluster_state(0x00000701), 'LINK')

    def test_get_name_from_sfn(self):
        """
        Проверяет, что правильно формируется строка по полю DIR_Name в sfn
        """
        DIR_Name = b'DOSFILE TXT'
        self.assertEqual('DOSFILE.TXT', fs.get_name_from_sfn(DIR_Name))
        DIR_Name = b'DOSDIR     '
        self.assertEqual('DOSDIR', fs.get_name_from_sfn(DIR_Name))

    def test_get_attr_from_sfn(self):
        """
        Проверяет, что правильно определяется тип файла по его записи sfn
        """
        self.assertEqual('dir', fs.get_attr_from_sfn(0x10))
        self.assertEqual('file', fs.get_attr_from_sfn(0x20))

    def test_get_clusterID_from_sfn(self):
        """
        Проверяет, что корректно определяется номер начального кластера файла
        по его файловой записи
        """
        sfn = b',O5.1L-\x146:6\x14\x00\xb1\x1b\xb9b:b:\x00\x00\xa5\xb9b:\x04\x00\x04\x00\x00\x00'
        self.assertEqual(4, fs.get_clusterID_from_sfn(sfn))
        sfn = b',O5,14\x14\x14\x14\x14\x14\n\x00];\xb9b:b:\x00\x00{\xbab:\x03\x00\x00\x00\x00\x00'
        self.assertEqual(3, fs.get_clusterID_from_sfn(sfn))
        # TODO написать тест на кластеры с большим номером

    def test_get_size_from_sfn(self):
        """
        Проверяет, что корректно достается размер файла по полю в sfn
        """
        self.assertEqual(4, fs.get_size_from_sfn(bytes([4, 00, 00, 00])))
        self.assertEqual(11, fs.get_size_from_sfn(bytes([0x0b, 00, 00, 00])))

    def test_parse_sfn_entry_file(self):
        """
        Проверяет, что корректно разбирается файловая запись типа sfn
        (файл)
        """
        sfn = bytes([
            0x46, 0x31, 0x30, 0x42,
            0x59, 0x54, 0x45, 0x53,
            0x54, 0x58, 0x54, 0x20,
            0x00, 0x2a, 0x26, 0x0d,
            0x9a, 0x58, 0x9a, 0x58,
            0x00, 0x00, 0x26, 0x0d,
            0x9a, 0x58, 0x06, 0x00,
            0x0b, 0x00, 0x00, 0x00
        ])

        exp = {
            'entry': 'sfn',
            'name': 'F10BYTES.TXT',
            'type': 'file',
            'clusterID': 6,
            'size': 0xB
        }

        act = fs.parse_sfn_entry(sfn)
        print(act)
        self.assertDictEqual(exp, act)

    def test_parse_sfn_entry_directory(self):
        """
        Проверяет, что корректно разбирается файловая запись типа sfn
        (директория)
        """
        sfn = bytes([
            0x44, 0x4f, 0x53, 0x44,
            0x49, 0x52, 0x32, 0x20,
            0x20, 0x20, 0x20, 0x10,
            0x00, 0x44, 0x73, 0x03,
            0x99, 0x58, 0x99, 0x58,
            0x00, 0x00, 0x73, 0x03,
            0x99, 0x58, 0x05, 0x00,
            0x00, 0x00, 0x00, 0x00
        ])

        exp = {
            'entry': 'sfn',
            'name': 'DOSDIR2',
            'type': 'dir',
            'clusterID': 5,
            'size': 0
        }

        act = fs.parse_sfn_entry(sfn)
        print(act)
        self.assertDictEqual(exp, act)
