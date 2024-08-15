import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class NumericEntry(Gtk.Entry):
    """
    Represents a text entry widget with built-in numeric input filtering.
    """

    def __init__(self):
        """
        Initializes a NumericEntry object.
        """

        super().__init__()

        self.last_correct_input = ''

        self.connect('changed', self.filter_input)

    def split_input(self, user_input, cursor_position, deleting):
        """
        Splits the input string into three parts: before the change,
        the change itself, and after the change.

        Args:
            user_input (str): The input string.
            cursor_position (int): The current cursor position.
            deleting (bool): True if the user is deleting, False if inserting.

        Returns:
            tuple: A tuple containing (before_change, change, after_change).
        """

        delta_length = len(user_input) - len(self.last_correct_input)
        change_index = cursor_position if deleting else cursor_position - delta_length

        before_change = self.last_correct_input[:change_index]
        change = '' if deleting else user_input[change_index:cursor_position]
        after_change = self.last_correct_input[change_index - delta_length:] if deleting else self.last_correct_input[change_index:]

        return change_index, before_change, change, after_change

    def numeric_filter(self, user_input):
            """
            Ensures that the entry's text only contains digits, a
            single decimal point (.), and optionally a minus sign (-) at the
            beginning.

            Args:
                user_input (str): The input to filter.
            """

            cursor_position = self.get_position()
            deleting = len(user_input) < len(self.last_correct_input)

            change_index, before_change, change, after_change = self.split_input(user_input, cursor_position, deleting)

            dot_allowed = '.' not in self.last_correct_input
            minus_allowed = '-' not in self.last_correct_input and change_index == 0

            filtered_input = before_change

            if change.isdigit() or (change == '.' and dot_allowed) or (change == '-' and minus_allowed):
                filtered_input += change

            filtered_input += after_change

            if filtered_input != user_input:
                self.update_input_and_cursor(filtered_input, cursor_position, user_input)

            self.last_correct_input = filtered_input

    def update_input_and_cursor(self, filtered_input, cursor_position, user_input):
        """
        Updates the entry text and cursor position.

        Args:
            filtered_input (str): The new filtered input.
            cursor_position (int): The current cursor position.
            user_input (str): The old input before filtering.
        """

        self.handler_block_by_func(self.filter_input)
        self.set_text(filtered_input)
        new_cursor_position = max(min(cursor_position - (len(user_input) - len(filtered_input)), len(filtered_input)), 0)
        self.set_position(new_cursor_position)
        self.handler_unblock_by_func(self.filter_input)

    @staticmethod
    def is_incorrect(user_input):
        """
        Checks if the user's input is incorrect.

        Args:
            user_input (str): The input to check.

        Returns:
            True if input is incorrect, False otherwise.
        """

        if user_input.count('.') > 1:
            return True

        if '-' in user_input and not user_input.startswith('-'):
            return True

        for index, char in enumerate(user_input):
            if not char.isdigit() and (char not in '.-' or (char == '-' and index != 0)):
                return True

        return False

    @staticmethod
    def error_style(func):
        """
        Decorator to add/remove the 'error' class when incorrect data is entered.

        Args:
            func: The function to which the decorator is applied.

        Returns:
            wrapper: A wrapper function that checks the entered data
                     and adds/removes the "error" class.
        """

        def wrapper(self, *args, **kwargs):
            user_input = self.get_text()
            unwritten_floats = ['.', '-', '-.']

            if self.is_incorrect(user_input) or user_input in unwritten_floats:
                self.add_css_class('error')

            func(*args, **kwargs)

            def check_and_remove_error():
                filtered_input = self.get_text()
                if not self.is_incorrect(filtered_input) and filtered_input not in unwritten_floats:
                    self.remove_css_class('error')
                return False

            GLib.timeout_add(300, check_and_remove_error)
        return wrapper

    @error_style
    def filter_input(self, *args):
        """
        Delays the filtering logic until after the user has finished typing.

        Args:
            *args: Additional arguments passed to the 'changed' signal.
        """

        user_input = self.get_text()
        GLib.idle_add(self.numeric_filter, user_input)
