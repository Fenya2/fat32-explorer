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
            self.assertEqual(0xa16dd33d, bpb['BS_VolID'])
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
            bpb = fs.extract_bpb_data(image)
            root_address = fs.get_root(bpb)
            self.assertEqual(0x204000, root_address)

    def test_get_cluster(self):
        with open('tests/resources/volume.fat32', 'rb') as image:
            bpb = fs.extract_bpb_data(image)
            root_address = fs.get_root(bpb)
            self.assertEqual(0x204000, root_address)

