import src.algorithm.fat32 as fs


if __name__ == '__main__':
    with open('tests/resources/volume.fat32', 'rb') as image:
        bpb = fs.get_bpb(image)

        print(fs.get_cluster(2, image, bpb))
        print(fs.get_cluster_address(4, bpb))
        print(fs.get_fat_address(bpb))
        print(fs.get_root_address(bpb))
