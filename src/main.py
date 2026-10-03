import tkinter as tk
import argparse
import os
import socket
import shlex


class ShellEmulator:
    """Класс эмулятора командной строки."""

    def __init__(self, root, vfs_path, script_path):
        """Инициализация окна"""

        self.root = root

        self.vfs_path = os.path.abspath(vfs_path)
        self.script_path = os.path.abspath(script_path)

        username = os.getlogin()
        hostname = socket.gethostname()

        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        self.root.geometry("800x500")

        self.output = tk.Text(
            root,
            bg="black",
            fg="white",
            insertbackground="white",
            font=("Consolas", 11)
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.config(state=tk.DISABLED)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill=tk.X)

        self.prompt = tk.Label(
            self.input_frame,
            text="$ ",
            bg="black",
            fg="white",
            font=("Consolas", 11)
        )
        self.prompt.pack(side=tk.LEFT)

        self.entry = tk.Entry(
            self.input_frame,
            bg="black",
            fg="white",
            insertbackground="white",
            font=("Consolas", 11)
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.entry.bind("<Return>", self.execute_command)

        self.entry.focus()

        self.print_output("Параметры запуска:")
        self.print_output(
            f"VFS: {self.vfs_path}"
        )
        self.print_output(
            f"Startup script: {self.script_path}"
        )

        self.print_output("")

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

        success = self.process_command(command_line)

        return success

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

        elif command == "exit":
            return self.command_exit(arguments)

        else:
            self.print_output(f"Ошибка: неизвестная команда '{command}'")
            return False

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
        required=True,
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

    if not os.path.isdir(args.vfs):
        print(f"Ошибка: VFS не существует: {args.vfs}")
        return False

    if not os.path.isfile(args.script):
        print(f"Ошибка: стартовый скрипт не найден: {args.script}")
        return False
    return True


def main():
    """Запуск программы"""

    args = parse_arguments()

    print(f"VFS: {os.path.abspath(args.vfs)}")
    print(f"Startup script: {os.path.abspath(args.script)}")

    if not validate_arguments(args):
        return

    root = tk.Tk()

    ShellEmulator(
        root,
        args.vfs,
        args.script
    )

    root.mainloop()


if __name__ == "__main__":
    main()
