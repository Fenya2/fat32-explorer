from tabulate import tabulate
import shlex


class CommandParser:
    """
    Парсер команд пользователя для взаимодействия с программой.
    Принимает в конструкторе открытый Fat32 объект и при вызове метода
    run() в бесконечном цикле просит ввода команд от пользователя
    """

    def __init__(self, fs):
        self.fs = fs

    def run(self):
        while True:
            command = input('$ ').split()
            if len(command) == 0:
                continue
            match command[0]:
                case 'pwd':
                    self._pwd()
                case 'cd':
                    self._cd(command)
                case 'ls':
                    self._ls()
                case 'cat':
                    self._cat(command)
                case 'exit':
                    break
                case 'help':
                    self._help()
                case _:
                    print('incorrect command. Type "help" for help.')

    def _help(self):
        """
        print help
        """
        print('help message')

    def _cd(self, args):
        """
        Change directory
        """
        if len(args) != 1:
            print('Incorrect syntax. Usage: cd <directory>')
            return
        try:
            # Используем shlex.split для правильного разбора строки с учетом кавычек
            directory = shlex.split(args[0])[0]
            self.fs.cd(directory)
        except Exception as e:
            print(f'Error: {e}')

    def _cat(self, command):
        """
        Разбирает команду cat от пользователя, форматирует и выводит
        вывод от fs
        """
        if len(command) != 2:
            print('incorrect syntax. Type "help" for help')
            return
        try:
            print(self.fs.cat(command[1]).decode('utf-8'))
        except ValueError as e:
            print(e)

    def _pwd(self):
        """
        Выводит текущую рабочую директорию
        """
        print(self.fs.pwd())

    def _ls(self):
        """
        Выводит отформатированный список файлов в текущей директории
        """
        files = self.fs.ls()
        headers = ["Type", "Name", "Size"]
        data = [(file['type'], file['name'], file['size']) for file in files]
        print(tabulate(data, headers=headers, tablefmt="plain"))
