import shutil
import tkinter as tk
import argparse
import os
import socket
import shlex
import copy


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
        elif command == "whoami":
            return self.command_whoami(arguments)
        elif command == "find":
            return self.command_find(arguments)
        elif command == "echo":
            return self.command_echo(arguments)
        elif command == "vfs-init":
            return self.command_vfs_init(arguments)
        elif command == "mv":
            return self.command_mv(arguments)
        elif command == "cp":
            return self.command_cp(arguments)
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

    def find_recursive(self, node, current_path, target_name=None):
        """Рекурсивный поиск в VFS."""

        results = []

        if target_name is None or node.name == target_name:
            results.append(
                "/" + "/".join(current_path)
            )

        if node.is_directory:
            for name, child in node.children.items():
                results.extend(
                    self.find_recursive(
                        child,
                        current_path + [name],
                        target_name
                    )
                )

        return results

    def get_parent_node(self, path_parts):
        """Возвращает родительскую директорию для указанного пути."""

        if not path_parts:
            return None

        parent_path = path_parts[:-1]

        return self.vfs.get_node(parent_path)

    def command_ls(self, arguments):
        """Вывод содержимого директории VFS."""

        if len(arguments) > 1:
            self.print_output("Ошибка: ls принимает не более одного аргумента")
            return False

        if arguments:
            path_parts = self.normalize_path(arguments[0])
        else:
            path_parts = self.current_path

        node = self.vfs.get_node(path_parts)

        if node is None:
            self.print_output("Ошибка: директория не найдена")
            return False

        if not node.is_directory:
            self.print_output("Ошибка: указанный путь не является директорией")
            return False

        if not node.children:
            self.print_output("(пусто)")
            return True

        items = []

        for name, child in sorted(node.children.items()):
            if child.is_directory:
                items.append(name + "/")
            else:
                items.append(name)

        self.print_output(" ".join(items))

        return True

    def command_cd(self, arguments):
        """Изменение текущей директории VFS."""

        if len(arguments) > 1:
            self.print_output("Ошибка: cd принимает не более одного аргумента")
            return False

        if not arguments:
            self.current_path = []
            return True

        path_parts = self.normalize_path(arguments[0])
        node = self.vfs.get_node(path_parts)

        if node is None:
            self.print_output("Ошибка: директория не найдена")
            return False

        if not node.is_directory:
            self.print_output("Ошибка: указанный путь не является директорией")
            return False

        self.current_path = path_parts
        return True

    def command_whoami(self, arguments):
        """Вывод имени текущего пользователя."""

        if arguments:
            self.print_output("Ошибка: whoami не принимает аргументы")
            return False

        username = os.getlogin()

        self.print_output(username)

        return True

    def command_echo(self, arguments):
        """Вывод переданных аргументов."""

        self.print_output(" ".join(arguments))

        return True

    def command_find(self, arguments):
        """Поиск файлов и директорий в VFS."""

        if len(arguments) > 2:
            self.print_output("Ошибка: find принимает не более двух аргументов")
            return False

        if arguments:
            start_path = self.normalize_path(arguments[0])
        else:
            start_path = self.current_path

        start_node = self.vfs.get_node(start_path)

        if start_node is None:
            self.print_output("Ошибка: указанный путь не найден")
            return False

        if len(arguments) == 2:
            target_name = arguments[1]
        else:
            target_name = None

        results = self.find_recursive(
            start_node,
            start_path,
            target_name
        )

        if not results:
            self.print_output("Ничего не найдено.")
            return True

        for result in results:
            self.print_output(result)

        return True

    def command_mv(self, arguments):
        """Перемещает файл или директорию внутри VFS."""

        if len(arguments) != 2:
            self.print_output("Ошибка: mv требует два аргумента")
            return False
        source_path = self.normalize_path(arguments[0])
        destination_path = self.normalize_path(arguments[1])
        source_node = self.vfs.get_node(source_path)
        if source_node is None:
            self.print_output("Ошибка: исходный объект не найден")
            return False
        if not source_path:
            self.print_output("Ошибка: нельзя переместить корень VFS")
            return False
        source_parent = self.get_parent_node(source_path)
        if source_parent is None:
            self.print_output("Ошибка: родительская директория не найдена")
            return False
        source_name = source_path[-1]
        destination_node = self.vfs.get_node(destination_path)
        if destination_node is not None:
            if destination_node.is_directory:
                if source_name in destination_node.children:
                    self.print_output("Ошибка: объект с таким именем уже существует")
                    return False
                destination_node.children[source_name] = source_node
            else:
                self.print_output("Ошибка: назначение не является директорией")
                return False
        else:
            destination_parent = self.get_parent_node(destination_path)
            if destination_parent is None:
                self.print_output("Ошибка: родительская директория назначения не найдена")
                return False
            new_name = destination_path[-1]
            if new_name in destination_parent.children:
                self.print_output("Ошибка: объект с таким именем уже существует")
                return False
            source_node.name = new_name
            destination_parent.children[new_name] = source_node
        del source_parent.children[source_name]
        return True

    def command_cp(self, arguments):
        """Копирует файл или директорию внутри VFS."""

        if len(arguments) != 2:
            self.print_output("Ошибка: cp требует два аргумента")
            return False
        source_path = self.normalize_path(arguments[0])
        destination_path = self.normalize_path(arguments[1])
        source_node = self.vfs.get_node(source_path)
        if source_node is None:
            self.print_output("Ошибка: исходный объект не найден")
            return False
        if not source_path:
            self.print_output("Ошибка: нельзя скопировать корень VFS")
            return False
        destination_node = self.vfs.get_node(destination_path)
        if destination_node is not None:
            if destination_node.is_directory:
                new_name = source_node.name
                if new_name in destination_node.children:
                    self.print_output("Ошибка: объект с таким именем уже существует")
                    return False
                copied_node = copy.deepcopy(source_node)
                destination_node.children[new_name] = copied_node
            else:
                self.print_output("Ошибка: назначение не является директорией")
                return False
        else:
            destination_parent = self.get_parent_node(destination_path)
            if destination_parent is None:
                self.print_output("Ошибка: родительская директория назначения не найдена")
                return False
            new_name = destination_path[-1]
            if new_name in destination_parent.children:
                self.print_output("Ошибка: объект с таким именем уже существует")
                return False
            copied_node = copy.deepcopy(source_node)
            copied_node.name = new_name
            destination_parent.children[new_name] = copied_node
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
