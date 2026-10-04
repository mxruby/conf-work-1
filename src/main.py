import shutil
import tkinter as tk
import argparse
import os
import socket
import shlex


class VFSNode:
    """
    Узел виртуальной файловой системы.

    Узел может быть:
    - директорией;
    - файлом.
    """

    def __init__(self, name, is_directory=True):
        self.name = name
        self.is_directory = is_directory

        self.children = {} if is_directory else {}


class VirtualFileSystem:
    """
    Виртуальная файловая система, полностью находящаяся в памяти.
    """

    def __init__(self):
        self.root = VFSNode("/")

    def load_from_disk(self, path):
        """
        Загружает физическую директорию в память.
        После загрузки дальнейшие операции с VFS
        не изменяют физические файлы.
        """

        self.root = VFSNode("/")

        self._load_directory(
            self.root,
            path
        )

    def _load_directory(self, parent_node, physical_path):
        """
        Рекурсивно загружает директорию.
        """

        try:
            entries = os.listdir(physical_path)

        except OSError as error:
            raise RuntimeError(
                f"Не удалось прочитать VFS: {error}"
            )

        for entry in entries:
            full_path = os.path.join(
                physical_path,
                entry
            )

            if os.path.isdir(full_path):

                node = VFSNode(
                    entry,
                    is_directory=True
                )

                parent_node.children[entry] = node

                self._load_directory(
                    node,
                    full_path
                )

            else:

                node = VFSNode(
                    entry,
                    is_directory=False
                )

                parent_node.children[entry] = node

    def get_node(self, path_parts):
        """
        Находит узел по пути относительно корня VFS.
        """

        current = self.root

        for part in path_parts:

            if part == "":
                continue

            if part not in current.children:
                return None

            current = current.children[part]

        return current


class ShellEmulator:
    """Класс эмулятора командной строки."""

    def __init__(self, root, vfs_path=None, script_path=None):
        """Инициализация окна"""

        self.root = root
        self.vfs_path = os.path.abspath(vfs_path) if vfs_path else None
        self.script_path = os.path.abspath(script_path) if script_path else None
        self.vfs = VirtualFileSystem()
        self.current_path = []
        if self.vfs_path:
            self.vfs.load_from_disk(self.vfs_path)
        username = os.getlogin()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        self.root.geometry("800x500")
        self.output = tk.Text(root, bg="black", fg="white", insertbackground="white", font=("Consolas", 11))
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.config(state=tk.DISABLED)
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill=tk.X)
        self.prompt = tk.Label(self.input_frame, text="$ ", bg="black", fg="white", font=("Consolas", 11))
        self.prompt.pack(side=tk.LEFT)
        self.entry = tk.Entry(self.input_frame, bg="black", fg="white", insertbackground="white", font=("Consolas", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.execute_command)
        self.entry.focus()
        self.print_output("Параметры запуска:")
        if self.vfs_path:
            self.print_output(f"VFS: {self.vfs_path}")
        else:
            self.print_output("VFS: по умолчанию (только в памяти)")
        if self.script_path:
            self.print_output(f"Startup script: {self.script_path}")
        else:
            self.print_output("Startup script: отсутствует")
        self.print_output("")
        if self.script_path:
            self.run_startup_script()

    def print_output(self, text):
        """Вывод текста в консоль."""

        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def execute_command(self, event=None):
        """Обработка введённой команды."""

        command_line = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if not command_line:
            return

        self.print_output(f"$ {command_line}")

        self.process_command(command_line)

    def process_command(self, command_line):
        """Разбирает команду и выполняет её."""

        try:
            parts = shlex.split(command_line)
        except ValueError as error:
            self.print_output(f"Ошибка разбора команды: {error}")
            return False
        if not parts:
            return True

        command = parts[0]
        arguments = parts[1:]

        if command == "ls":
            return self.command_ls(arguments)
        elif command == "cd":
            return self.command_cd(arguments)
        elif command == "vfs-init":
            return self.command_vfs_init(arguments)
        elif command == "exit":
            return self.command_exit(arguments)
        else:
            self.print_output(f"Ошибка: неизвестная команда '{command}'")
            return False

    def normalize_path(self, path):
        """Работа с путями VFS"""

        if path.startswith("/"):
            result = []

        else:
            result = self.current_path.copy()

        for part in path.split("/"):

            if part == "" or part == ".":
                continue

            if part == "..":

                if result:
                    result.pop()

            else:
                result.append(part)

        return result

    def command_ls(self, arguments):
        """Заглушка команды ls."""

        self.print_output("Команда: ls")

        if arguments:
            self.print_output(f"Аргументы: {arguments}")
        else:
            self.print_output("Аргументы: отсутствуют")

        return True

    def command_cd(self, arguments):
        """Заглушка команды cd."""

        self.print_output("Команда: cd")
        if arguments:
            self.print_output(f"Аргументы: {arguments}")
        else:
            self.print_output("Аргументы: отсутствуют")

        return True

    def command_exit(self, arguments):
        """Команда выхода."""

        if arguments:
            self.print_output("Ошибка: команда exit не принимает аргументы")
            return False

        self.print_output("Завершение работы эмулятора...")

        self.root.destroy()

        return True

    def command_vfs_init(self, arguments):
        """Инициализация VFS по умолчанию."""

        if arguments:
            self.print_output("Ошибка: vfs-init не принимает аргументы")
            return False

        self.vfs = VirtualFileSystem()
        self.current_path = []
        if self.vfs_path:
            try:
                if os.path.exists(self.vfs_path):
                    for entry in os.listdir(self.vfs_path):
                        full_path = os.path.join(self.vfs_path, entry)
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                else:
                    os.makedirs(self.vfs_path, exist_ok=True)
            except OSError as error:
                self.print_output(f"Ошибка очистки физической VFS: {error}")
                return False
        self.print_output("VFS инициализирована заново.")
        return True

    def run_startup_script(self):
        """Выполняет команды из стартового скрипта."""

        self.print_output("Выполнение скрипта...")
        try:
            with open(self.script_path, "r", encoding="utf-8") as script:
                for line_number, line in enumerate(script, start=1):
                    command_line = line.strip()
                    if not command_line:
                        continue

                    self.print_output(f"$ {command_line}")
                    success = self.process_command(command_line)
                    if not success:
                        self.print_output("")
                        self.print_output(f"Стартовый скрипт остановлен на строке {line_number}.")
                        return

        except FileNotFoundError:
            self.print_output("Ошибка: стартовый скрипт не найден.")
            return

        except OSError as error:
            self.print_output(f"Ошибка чтения стартового скрипта: {error}")
            return

        self.print_output("Скрипт выполнен.")


def parse_arguments():
    """Парсинг аргументов командной строки."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--vfs",
        required=False,
        help="Путь к физическому расположению VFS"
    )

    parser.add_argument(
        "--script",
        required=True,
        help="Путь к стартовому скрипту"
    )

    return parser.parse_args()


def validate_arguments(args):
    """Проверяет существование VFS и стартового скрипта."""

    if args.vfs and not os.path.isdir(args.vfs):
        print(f"Ошибка: VFS не существует: {args.vfs}")
        return False

    if not os.path.isfile(args.script):
        print(f"Ошибка: стартовый скрипт не найден: {args.script}")
        return False
    return True


def main():
    """Запуск программы"""

    args = parse_arguments()

    if args.vfs:
        print(f"VFS: {os.path.abspath(args.vfs)}")
    else:
        print("VFS: по умолчанию (в памяти)")

    if args.script:
        print(f"Startup script: {os.path.abspath(args.script)}")
    else:
        print("Startup script: отсутствует")
    if not validate_arguments(args):
        return

    root = tk.Tk()
    try:
        ShellEmulator(
            root,
            args.vfs,
            args.script
        )
        root.mainloop()
    except RuntimeError as error:
        print(f"Ошибка VFS: {error}")


if __name__ == "__main__":
    main()
