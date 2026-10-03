import tkinter as tk
import os
import socket
import shlex


class ShellEmulator:
    """Класс эмулятора командной строки."""

    def __init__(self, root):
        """Инициализация окна"""

        self.root = root

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

        try:
            parts = shlex.split(command_line)
        except ValueError as error:
            self.print_output(f"Ошибка разбора команды: {error}")
            return

        command = parts[0]
        arguments = parts[1:]

        if command == "ls":
            self.command_ls(arguments)

        elif command == "cd":
            self.command_cd(arguments)

        elif command == "exit":
            self.command_exit(arguments)

        else:
            self.print_output(f"Ошибка: неизвестная команда '{command}'")

    def command_ls(self, arguments):
        """Заглушка команды ls."""

        if arguments:
            self.print_output(f"Команда: ls")
            self.print_output(f"Аргументы: {arguments}")
        else:
            self.print_output("Команда: ls")
            self.print_output("Аргументы: отсутствуют")

    def command_cd(self, arguments):
        """Заглушка команды cd."""

        if arguments:
            self.print_output(f"Команда: cd")
            self.print_output(f"Аргументы: {arguments}")
        else:
            self.print_output("Команда: cd")
            self.print_output("Аргументы: отсутствуют")

    def command_exit(self, arguments):
        """Команда выхода."""

        if arguments:
            self.print_output("Ошибка: команда exit не принимает аргументы")
            return

        self.root.destroy()


def main():
    """Запуск программы"""

    root = tk.Tk()
    ShellEmulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
