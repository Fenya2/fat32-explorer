from src.algorithm.fat32 import Fat32

from src.cui.command_parser import CommandParser

# if __name__ == '__main__':
#     image_path = input('Enter image with fat32 path:')
#     fs = Fat32()
#     try:
#         fs.open(image_path)
#     except Exception as e:
#         print('incorrect path')
#         print(e)
#         quit(1)

#     parser = CommandParser(fs)
#     try:
#         parser.run()
#     except Exception as e:
#         print(e)
#     finally:
#         fs.close()
