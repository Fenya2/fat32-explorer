import src.algorithm.fat32 as fs


if __name__ == '__main__':
    with open('tests/resources/volume.fat32', 'rb') as image:
        bpb = fs.get_bpb(image)
        file = fs.get_file(11, image, bpb)
        print(file)
        print(len(file))
