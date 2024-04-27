from src.algorithm.fat32 import Fat32


if __name__ == '__main__':
    try:
        fs = Fat32()
        fs.open('tests/resources/volume.fat32')
        print(fs.ls('/combal/practice/labs'))
    finally:
        fs.close()
