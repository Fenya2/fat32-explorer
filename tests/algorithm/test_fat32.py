import unittest
import src.algorithm.fat32 as fs
from datetime import datetime, date, time


class Test_(unittest.TestCase):
    def test_Fat32_cd(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            fat = fs.Fat32()
            fat.open('tests/resources/volume.fat32')
            fat.cd('TESTDIR')
            self.assertEqual('/TESTDIR', fat.pwd())
            self.assertEqual(fs.get_file_clusters(
                332, image, bpb),
                fat.cur_directory_clusters
            )
            fat.cd('..')
            self.assertEqual('/', fat.pwd())
            self.assertEqual(fs.get_file_clusters(
                2, image, bpb),
                fat.cur_directory_clusters
            )

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

    def test_get_cluster(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            act = fs.get_cluster(339, image, bpb)
            image.seek(fs.get_cluster_address(339, bpb))
            exp = image.read(4096)
            self.assertEqual(exp, act)

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
        self.assertDictEqual(exp, act)

    def test_get_file_clusters(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            exp = [330, 331]
            act = fs.get_file_clusters(330, image, bpb)
            self.assertEqual(exp,  act)

    def test_get_file(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            file_entry = {
                'clusterID': 330,
                'name': 'Alexei_file.txt',
                'size': 6513,
                'type': 'file'
            }
            bpb = fs.get_bpb(image)
            act_file = fs.get_file(file_entry, image, bpb)
            with open('mount_point/Alexei_file.txt', 'rb') as video:
                exp_file = video.read()
            self.assertEqual(exp_file, act_file)

    def test_get_file_with_start_cluster(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            act_file = fs.get_file_with_start_cluster(533, 4202598, image, bpb)
            with open('mount_point/VIDEO.MOV', 'rb') as video:
                exp_file = video.read()
            self.assertEqual(exp_file, act_file)

    def test_fat_of(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            exp = 1210
            act = fs.fat_of(1209, image, bpb)
            self.assertEqual(exp, act)
            exp = 'EOF'
            act = fs.get_cluster_state(fs.fat_of(1559, image, bpb))
            self.assertEqual(exp, act)

    def test_ls_dir(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.get_bpb(image)
            act = fs.ls_dir(
                fs.get_file_clusters(339, image, bpb), image, bpb)
            self.assertEqual(194, len(act))

            act = fs.ls_dir(
                fs.get_file_clusters(2, image, bpb), image, bpb)
            exp = [
                {'clusterID': 321, 'name': 'K', 'size': 0, 'type': 'dir'},
                {'clusterID': 332, 'name': 'TESTDIR', 'size': 0, 'type': 'dir'},
                {'clusterID': 339, 'name': 'BIGDIR', 'size': 0, 'type': 'dir'},
                {'clusterID': 533, 'name': 'VIDEO.MOV',
                    'size': 4202598, 'type': 'file'},
                {'clusterID': 330, 'name': 'Alexei_file.txt',
                    'size': 6513, 'type': 'file'},
                {'clusterID': 0,
                    'name': 'file with very very big filename to test that lfn entries folds '
                    'correctly i think this enough but i type some chars more',
                    'size': 0,
                    'type': 'file'}
            ]

            self.assertEqual(len(exp), len(act))
            for i in range(len(exp)):
                self.assertDictEqual(exp[i], act[i])

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
        self.assertDictEqual(exp, act)

    def test_parse_lfn_entry(self):
        """
        Проверяет, что корректно разбирает файловая запись типа lfn
        """
        lfn = [
            bytes([
                0x01, 0x61, 0x00, 0x62,
                0x00, 0x63, 0x00, 0x64,
                0x00, 0x65, 0x00, 0x0f,
                0x00, 0xca, 0x66, 0x00,
                0x67, 0x00, 0x68, 0x00,
                0x69, 0x00, 0x6a, 0x00,
                0x6b, 0x00, 0x00, 0x00,
                0x6c, 0x00, 0x6d, 0x00
            ]),

            bytes([
                0x41, 0x54, 0x00, 0x45,
                0x00, 0x53, 0x00, 0x54,
                0x00, 0x44, 0x00, 0x0f,
                0x00, 0x34, 0x4f, 0x00,
                0x53, 0x00, 0x4e, 0x00,
                0x41, 0x00, 0x4d, 0x00,
                0x45, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xff, 0xff
            ])
        ]

        exp = [
            {
                'entry': 'lfn',
                'name_part': b'a\x00b\x00c\x00d\x00e\x00f\x00g\x00h\x00i\x00j\x00k\x00l\x00m\x00'
            },
            {
                'entry': 'lfn',
                'name_part': b'T\x00E\x00S\x00T\x00D\x00O\x00S\x00N\x00A\x00M\x00E\x00\x00\x00\xff\xff'
            }
        ]

        for i in range(len(lfn)):
            act = fs.parse_lfn_entry(lfn[i])
            self.assertDictEqual(exp[i], act)

    def test_get_files_from_file_entries(self):
        file_entries = [
            {'clusterID': 321, 'entry': 'sfn',
                'name': 'K', 'size': 0, 'type': 'dir'},
            {'clusterID': 332,
             'entry': 'sfn',
             'name': 'TESTDIR',
             'size': 0,
             'type': 'dir'},
            {'entry': 'lfn',
             'name_part': b'x\x00t\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
             b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
            {'entry': 'lfn',
             'name_part': b'A\x00l\x00e\x00x\x00e\x00i\x00_\x00f\x00i\x00l\x00e\x00.\x00'
             b't\x00'},
            {'clusterID': 330,
             'entry': 'sfn',
             'name': 'ALEXEI~1.TXT',
             'size': 6513,
             'type': 'file'},
            {'entry': 'lfn',
             'name_part': b'o\x00r\x00e\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'
             b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
            {'entry': 'lfn',
             'name_part': b' \x00s\x00o\x00m\x00e\x00 \x00c\x00h\x00a\x00r\x00s\x00 \x00'
             b'm\x00'},
            {'entry': 'lfn',
             'name_part': b'g\x00h\x00 \x00b\x00u\x00t\x00 \x00i\x00 \x00t\x00y\x00p\x00'
             b'e\x00'},
            {'entry': 'lfn',
             'name_part': b'i\x00n\x00k\x00 \x00t\x00h\x00i\x00s\x00 \x00e\x00n\x00o\x00'
             b'u\x00'},
            {'entry': 'lfn',
             'name_part': b'o\x00r\x00r\x00e\x00c\x00t\x00l\x00y\x00 \x00i\x00 \x00t\x00'
             b'h\x00'},
            {'entry': 'lfn',
             'name_part': b't\x00r\x00i\x00e\x00s\x00 \x00f\x00o\x00l\x00d\x00s\x00 \x00'
             b'c\x00'},
            {'entry': 'lfn',
             'name_part': b't\x00 \x00t\x00h\x00a\x00t\x00 \x00l\x00f\x00n\x00 \x00e\x00'
             b'n\x00'},
            {'entry': 'lfn',
             'name_part': b'l\x00e\x00n\x00a\x00m\x00e\x00 \x00t\x00o\x00 \x00t\x00e\x00'
             b's\x00'},
            {'entry': 'lfn',
             'name_part': b'y\x00 \x00v\x00e\x00r\x00y\x00 \x00b\x00i\x00g\x00 \x00f\x00'
             b'i\x00'},
            {'entry': 'lfn',
             'name_part': b'f\x00i\x00l\x00e\x00 \x00w\x00i\x00t\x00h\x00 \x00v\x00e\x00'
             b'r\x00'},
            {'clusterID': 0,
             'entry': 'sfn',
             'name': 'FILEWI~1',
             'size': 0,
             'type': 'file'}
        ]

        exp = [
            {'clusterID': 321, 'name': 'K', 'size': 0, 'type': 'dir'},
            {'clusterID': 332, 'name': 'TESTDIR', 'size': 0, 'type': 'dir'},
            {'clusterID': 330, 'name': 'Alexei_file.txt',
                'size': 6513, 'type': 'file'},
            {'clusterID': 0,
                'name': 'file with very very big filename to test that lfn entries folds '
                'correctly i think this enough but i type some chars more',
                'size': 0,
                'type': 'file'}
        ]

        act = fs.get_files_from_file_entries(file_entries)

        self.assertEqual(len(exp), len(act))
        for i in range(len(exp)):
            self.assertDictEqual(exp[i], act[i])

    def test_extract_name_from_lfns(self):
        lfns = [
            {'entry': 'lfn',
             'name_part': b'o\x00r\x00e\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'
             b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
            {'entry': 'lfn',
                'name_part': b' \x00s\x00o\x00m\x00e\x00 \x00c\x00h\x00a\x00r\x00s\x00 \x00'
             b'm\x00'},
            {'entry': 'lfn',
                'name_part': b'g\x00h\x00 \x00b\x00u\x00t\x00 \x00i\x00 \x00t\x00y\x00p\x00'
             b'e\x00'},
            {'entry': 'lfn',
                'name_part': b'i\x00n\x00k\x00 \x00t\x00h\x00i\x00s\x00 \x00e\x00n\x00o\x00'
             b'u\x00'},
            {'entry': 'lfn',
                'name_part': b'o\x00r\x00r\x00e\x00c\x00t\x00l\x00y\x00 \x00i\x00 \x00t\x00'
             b'h\x00'},
            {'entry': 'lfn',
                'name_part': b't\x00r\x00i\x00e\x00s\x00 \x00f\x00o\x00l\x00d\x00s\x00 \x00'
             b'c\x00'},
            {'entry': 'lfn',
                'name_part': b't\x00 \x00t\x00h\x00a\x00t\x00 \x00l\x00f\x00n\x00 \x00e\x00'
             b'n\x00'},
            {'entry': 'lfn',
                'name_part': b'l\x00e\x00n\x00a\x00m\x00e\x00 \x00t\x00o\x00 \x00t\x00e\x00'
             b's\x00'},
            {'entry': 'lfn',
                'name_part': b'y\x00 \x00v\x00e\x00r\x00y\x00 \x00b\x00i\x00g\x00 \x00f\x00'
             b'i\x00'},
            {'entry': 'lfn',
                'name_part': b'f\x00i\x00l\x00e\x00 \x00w\x00i\x00t\x00h\x00 \x00v\x00e\x00'
             b'r\x00'}
        ]
        exp = 'file with very very big filename to test that lfn entries folds correctly i think this enough but i type some chars more'
        act = fs.extract_name_from_lfns(lfns)
        self.assertEqual(exp, act)

    def test_get_file_entries_in(self):
        """
        Читает кластер директории, проверяет корректность считывания файловых
        записей
        """
        with open('tests/resources/test_cluster.dat', 'rb') as image:
            cluster = image.read()
        act = fs.get_file_entries_in(cluster)
        exp = [{'clusterID': 332, 'entry': 'sfn', 'name': '.', 'size': 0, 'type': 'dir'},
               {'clusterID': 0, 'entry': 'sfn',
                   'name': '..', 'size': 0, 'type': 'dir'},
               {'clusterID': 333,
                'entry': 'sfn',
                'name': 'LFNFILE.DAT',
                'size': 2,
                'type': 'file'},
               {'entry': 'lfn',
                'name_part': b's\x00f\x00n\x00f\x00i\x00l\x00e\x00.\x00d\x00a\x00'
                b't\x00\x00\x00\xff\xff'},
               {'clusterID': 334,
                'entry': 'sfn',
                'name': 'SFNFILE.DAT',
                'size': 3,
                'type': 'file'},
               {'entry': 'lfn',
                'name_part': b'i\x00o\x00n\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'
                b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
               {'entry': 'lfn',
                'name_part': b't\x00e\x00n\x00d\x00e\x00d\x00_\x00e\x00x\x00t\x00e\x00n\x00'
                b's\x00'},
               {'entry': 'lfn',
                'name_part': b'_\x00l\x00o\x00n\x00g\x00_\x00n\x00a\x00m\x00e\x00.\x00e\x00'
                b'x\x00'},
               {'entry': 'lfn',
                'name_part': b'l\x00f\x00n\x00_\x00f\x00i\x00l\x00e\x00_\x00w\x00i\x00t\x00'
                b'h\x00'},
               {'clusterID': 335,
                'entry': 'sfn',
                'name': 'LFN_FI~1.EXT',
                'size': 4,
                'type': 'file'},
               {'clusterID': 0, 'entry': 'sfn',
                'name': 'EMPTY', 'size': 0, 'type': 'file'},
               {'entry': 'lfn',
                'name_part': b'e\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
                b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
               {'entry': 'lfn',
                'name_part': b'e\x00m\x00p\x00t\x00y\x00_\x00l\x00f\x00n\x00_\x00f\x00i\x00'
                b'l\x00'},
               {'clusterID': 0,
                'entry': 'sfn',
                'name': 'EMPTY_~1',
                'size': 0,
                'type': 'file'},
               {'clusterID': 336, 'entry': 'sfn',
                'name': 'DOSDIR', 'size': 0, 'type': 'dir'},
               {'entry': 'lfn',
                'name_part': b'l\x00f\x00n\x00d\x00i\x00r\x00\x00\x00\xff\xff\xff\xff\xff\xff'
                b'\xff\xff\xff\xff\xff\xff'},
               {'clusterID': 337, 'entry': 'sfn',
                'name': 'LFNDIR', 'size': 0, 'type': 'dir'},
               {'entry': 'lfn',
                'name_part': b'l\x00o\x00n\x00g\x00_\x00n\x00a\x00m\x00e\x00\x00\x00'
                b'\xff\xff\xff\xff\xff\xff'},
               {'entry': 'lfn',
                'name_part': b'l\x00f\x00n\x00_\x00f\x00i\x00r\x00_\x00w\x00i\x00t\x00h\x00'
                b'_\x00'},
               {'clusterID': 338,
                'entry': 'sfn',
                'name': 'LFN_FI~1',
                'size': 0,
                'type': 'dir'}]
        self.assertEqual(len(exp), len(act))
        for i in range(len(exp)):
            self.assertDictEqual(exp[i], act[i])

    def test_define_file_entry(self):
        """
        Проверяет, что корректно определяется тип файловой записи
        """
        for i in range(0xff):
            if i == 0xf:
                self.assertEquals('lfn', fs.define_file_entry(i))
                continue
            self.assertEquals('sfn', fs.define_file_entry(i))

    def test_entry_is_removed(self):
        """
        Проверяет, удален ли файл с переданной файловой записью,
        смотря на первый символ имени
        """
        for i in range(0xff):
            if i == 0xe5:
                self.assertEqual(True, fs.entry_is_removed(i))
                continue
            self.assertEqual(False, fs.entry_is_removed(i))

    def test_entry_is_end(self):
        """
        Проверяет, что корректно определяется конец файловых записей в
        файле директории по первому байту имени
        """
        self.assertEqual(True, fs.entry_is_end(0x00))
        for i in range(1, 0xff):
            self.assertEqual(False, fs.entry_is_end(i))

    def test_get_file_entry(self):
        """
        Проверяет, что правильно разбирается файловая запись любого типа,
        либо эта запись удалена и об этом сообщается, либо она последняя
        и об этом сообщается
        """
        lfn = [
            bytes([
                0x43, 0x31, 0x00, 0x32,
                0x00, 0x33, 0x00, 0x34,
                0x00, 0x35, 0x00, 0x0f,
                0x00, 0xca, 0x36, 0x00,
                0x37, 0x00, 0x38, 0x00,
                0x39, 0x00, 0x30, 0x00,
                0x00, 0x00, 0x00, 0x00,
                0xff, 0xff, 0xff, 0xff
            ]),

            bytes([
                0x31, 0x32, 0x33, 0x34,
                0x35, 0x20, 0x20, 0x20,
                0x44, 0x41, 0x54, 0x20,
                0x00, 0x79, 0xab, 0x5b,
                0x9a, 0x58, 0x9a, 0x58,
                0x00, 0x00, 0xab, 0x5b,
                0x9a, 0x58, 0x0a, 0x00,
                0x06, 0x00, 0x00, 0x00
            ]),
        ]

        exp = [
            {
                'entry': 'lfn',
                'name_part': b'1\x002\x003\x004\x005\x006\x007\x008\x009\x000\x00\x00\x00\xff\xff\xff\xff'
            },
            {
                'entry': 'sfn',
                'name': '12345.DAT',
                'type': 'file',
                'clusterID': 10,
                'size': 6
            }
        ]

        for i in range(len(lfn)):
            act = fs.get_file_entry(lfn[i])
            self.assertDictEqual(exp[i], act)

        lfn = [
            b'\x00' * 32,
            bytes([
                0xe5, 0x32, 0x33, 0x34,
                0x35, 0x20, 0x20, 0x20,
                0x44, 0x41, 0x54, 0x20,
                0x00, 0x79, 0xab, 0x5b,
                0x9a, 0x58, 0x9a, 0x58,
                0x00, 0x00, 0xab, 0x5b,
                0x9a, 0x58, 0x0a, 0x00,
                0x06, 0x00, 0x00, 0x00
            ])
        ]

        exp = ['end', 'rm']

        for i in range(len(lfn)):
            act = fs.get_file_entry(lfn[i])
            self.assertEqual(exp[i], act)

    def test_get_time_from_sfn(self):
        exp = time(14, 8, 54)
        act = fs.get_time_from_sfn(b'\x1b\x71')
        self.assertEqual(exp, act)

        exp = time(2, 42, 36)
        act = fs.get_time_from_sfn(b'\x52\x15')
        self.assertEqual(exp, act)

        exp = time(9, 18, 12)
        act = fs.get_time_from_sfn(b'\x46\x4a')
        self.assertEqual(exp, act)

        exp = time(5, 40, 50)
        act = fs.get_time_from_sfn(b'\x19\x2d')
        self.assertEqual(exp, act)

    def test_get_date_from_sfn(self):
        exp = date(year=2015, month=7, day=20)
        act = fs.get_date_from_sfn(b'\xf4\x46')
        self.assertEqual(exp, act)

        exp = date(year=2024, month=5, day=7)
        act = fs.get_date_from_sfn(b'\xa7\x58')
        self.assertEqual(exp, act)

        exp = date(year=2024, month=4, day=30)
        act = fs.get_date_from_sfn(b'\x9e\x58')
        self.assertEqual(exp, act)
