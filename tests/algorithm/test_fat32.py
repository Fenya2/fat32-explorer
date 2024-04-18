import unittest
from src.algorithm.fat32 import Fat32


class Test_(unittest.TestCase):
    def test_bpb(self):
        """
        Проверяет, что корректно извлеклись данные из сектора bpb
        """
        fs = Fat32('tests/resources/volume.fat32')
        self.assertEqual(0x200, fs._bpb['BPB_BytsPerSec'])
        self.assertEqual(8, fs._bpb['BPB_SecPerClus'])
        self.assertEqual(0x20, fs._bpb['BPB_RsvdSecCnt'])
        self.assertEqual(2, fs._bpb['BPB_NumFATs'])
        self.assertEqual(0xffffc, fs._bpb['BPB_TotSec32'])
        self.assertEqual(0x400, fs._bpb['BS_DrvNum'])
        self.assertEqual(0x68cddf, fs._bpb['BS_VolID'])
        self.assertEqual('NO NAME    ', fs._bpb['BS_VolLab'])
        self.assertEqual('FAT32   ', fs._bpb['BS_FilSysType'])
