import src.algorithm.fat32 as fs


if __name__ == '__main__':
    with open('tests/resources/volume.fat32', 'rb') as image:
        bpb = fs.get_bpb(image)

        # print(fs.get_cluster(2, image, bpb))
        directory_clusters = fs.get_file_clusters(11, image, bpb)
        # print(fs.ls_dir(directory_clusters, image, bpb))
        print(fs.get_cluster_address(11, bpb))
