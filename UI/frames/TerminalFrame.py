from asciimatics.widgets import Frame, Layout, Text, Button, MultiColumnListBox, Widget,VerticalDivider
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import NextScene
from asciimatics.parsers import AnsiTerminalParser, Parser
from asciimatics.screen import Canvas
from asciimatics.event import KeyboardEvent
import subprocess
import threading

class SimpleCommandModel:
    def __init__(self):
        self.command = ""
        self.stdout = lambda x: None
        self.onChange = False
        self.SUCCRESS = ""
        self.ERRORS = ""

    def run(self):
        if self.command:
            try:
                result = subprocess.run(self.command, shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
                self.SUCCRESS = output
                self.onChange = True
                if self.stdout:
                    self.stdout(output)
            except Exception as e:
                error_msg = str(e)
                self.ERRORS = error_msg
                self.onChange = True
                if self.stdout:
                    self.stdout(error_msg)

class TerminalWidget(Widget):
    def __init__(self, name: str, height, title: str, model):
        super(TerminalWidget, self).__init__(name)
        self.title = title
        self._model = model
        self._required_height = height
        self._canvas: Canvas = None
        self._cursor_x, self._cursor_y = 0, 0
        self._show_cursor = True
        self._map = {}
        self._dataIn = ''
        self.out = []
        self._current_colours = None
        self._value = []  # queue of values
        self._parser = AnsiTerminalParser()
        for k, v in [
            (Screen.KEY_LEFT, self.on_kleft),
            (Screen.KEY_RIGHT, self.on_kright),
            (Screen.KEY_UP, self.on_key_up),
            (Screen.KEY_DOWN, self.on_key_down),
            (Screen.KEY_PAGE_UP, self.on_page_up),
            (Screen.KEY_PAGE_DOWN, self.on_page_down),
            (Screen.KEY_HOME, "khome"),
            (Screen.KEY_END, self.on_scape),
            (Screen.KEY_DELETE, self.on_delete),
            (Screen.KEY_BACK, self.on_back)
        ]:
            self._map[k] = v
        self._map[Screen.KEY_TAB] = "\t".encode()

    def on_key_up(self):
        if self._cursor_y != 0:
            self._cursor_y -= 1

    def on_key_down(self):
        if self._cursor_y != self._canvas.height:
            self._cursor_y += 1

    def on_scape(self):
        self._cursor_y += 1

    def on_page_up(self):
        self._canvas.scroll(-1)

    def on_page_down(self):
        self._canvas.scroll(1)

    def on_kleft(self):
        self._cursor_x -= 1

    def on_kright(self):
        self._cursor_x += 1

    def on_delete(self):
        self._print_at(text=' ' * self._canvas.width, x=0, y=self._cursor_y)
        self.prompit(start_y=self._cursor_y)
        self._cursor_x = 4

    def on_back(self):
        self._print_at(text=' ', x=self._cursor_x-1, y=self._cursor_y)
        self._cursor_x -= 1

    def set_layout(self, x, y, offset, w, h):
        super(TerminalWidget, self).set_layout(x, y, offset, w, h)
        self._canvas = Canvas(self._frame.canvas, h, w, x=x, y=y)

    def update(self, frame_no):
        self._canvas.refresh()
        if frame_no % 10 < 5 and self._show_cursor:
            origin = self._canvas.origin
            x = self._cursor_x + origin[0]
            y = self._cursor_y + origin[1] - self._canvas.start_line
            details = self._canvas.get_from(self._cursor_x, self._cursor_y)
            if details:
                char, colour, attr, bg = details
                attr |= Screen.A_REVERSE
                self._frame.canvas.print_at(chr(char), x, y, colour, attr, bg)

    def _print_at(self, text, x, y):
        self._canvas.print_at(
            text,
            x, y,
            colour=self._current_colours[0], attr=self._current_colours[1], bg=self._current_colours[2])

    def prompit(self, start_y):
        self._canvas.print_at(text='>>>', x=0, y=start_y)

    def reset(self):
        self._canvas = Canvas(self._frame.canvas, self._h, self._w, x=self._x, y=self._y)
        self._cursor_x, self._cursor_y = 0, 0
        self._current_colours = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        self._canvas.centre(text=self.title, y=0)
        self.prompit(start_y=1)
        self._cursor_x = 4
        self._cursor_y = 1

    def required_height(self, offset, width):
        return self._required_height

    @property
    def frame_update_count(self):
        return 5

    @property
    def dataIn(self):
        return self._dataIn

    @dataIn.setter
    def dataIn(self, arg):
        self._dataIn = arg
        if arg:
            self._add_stream(arg)

    def _add_stream(self, value):
        lines = value.split("\n")
        for i, line in enumerate(lines):
            self._parser.reset(line, self._current_colours)
            for offset, command, params in self._parser.parse():
                if command == Parser.DISPLAY_TEXT:
                    if self._cursor_x + len(params) > self._w:
                        part_1 = params[:self._w - self._cursor_x]
                        part_2 = params[self._w - self._cursor_x:]
                        self._print_at(part_1, self._cursor_x, self._cursor_y)
                        self._print_at(part_2, 0, self._cursor_y + 1)
                        self._cursor_x = len(part_2)
                        self._cursor_y += 1
                        if self._cursor_y - self._canvas.start_line >= self._h:
                            self._canvas.scroll()
                    else:
                        self._print_at(params, self._cursor_x, self._cursor_y)
                        self._cursor_x += len(params)
                elif command == Parser.CHANGE_COLOURS:
                    self._current_colours = params
                elif command == Parser.NEXT_TAB:
                    self._cursor_x = (self._cursor_x // 8) * 8 + 8
                elif command == Parser.MOVE_RELATIVE:
                    self._cursor_x += params[0]
                    self._cursor_y += params[1]
                    if self._cursor_y < self._canvas.start_line:
                        self._canvas.scroll(self._cursor_y - self._canvas.start_line)
                elif command == Parser.MOVE_ABSOLUTE:
                    if params[0] is not None:
                        self._cursor_x = params[0]
                    if params[1] is not None:
                        self._cursor_y = params[1] + self._canvas.start_line
                elif command == Parser.DELETE_LINE:
                    if params == 0:
                        self._print_at(" " * (self._w - self._cursor_x), self._cursor_x, self._cursor_y)
                    elif params == 1:
                        self._print_at(" " * self._cursor_x, 0, self._cursor_y)
                    elif params == 2:
                        self._print_at(" " * self._w, 0, self._cursor_y)
                elif command == Parser.DELETE_CHARS:
                    for x in range(self._cursor_x, self._w):
                        if x + params < self._w:
                            cell = self._canvas.get_from(x + params, self._cursor_y)
                        else:
                            cell = (ord(" "),
                                    self._current_colours[0],
                                    self._current_colours[1],
                                    self._current_colours[2])
                        self._canvas.print_at(
                            chr(cell[0]), x, self._cursor_y, colour=cell[1], attr=cell[2], bg=cell[3])
                elif command == Parser.SHOW_CURSOR:
                    self._show_cursor = params
                elif command == Parser.CLEAR_SCREEN:
                    self._canvas.clear_buffer(
                        self._current_colours[0], self._current_colours[1], self._current_colours[2])
            if i != len(lines) - 1:
                self._cursor_x = 0
                self._cursor_y += 1
                if self._cursor_y - self._canvas.start_line >= self._h:
                    self._canvas.scroll()

    def get_line(self, start, cursor):
        string = ''
        for x in range(start, cursor):
            code, fg, attr, bg = self._canvas.get_from(x=x, y=self._cursor_y)
            string += chr(code)
        return string

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, arg):
        if arg != '' and isinstance(arg, str):
            self._value.append(arg)

    def process_event(self, event):
        if self._cursor_y - self._canvas.start_line >= self._h:
            self._canvas.scroll()
        if isinstance(event, KeyboardEvent):
            if event.key_code > 0:
                if event.key_code == 13:
                    self.value = self.get_line(start=4, cursor=self._cursor_x)
                    if self.value:
                        for cmd in self.value:
                            self._model.command = cmd
                            threading.Thread(target=self._model.run).start()
                    self._cursor_x = 4
                    self.on_scape()
                    self.prompit(start_y=self._cursor_y)
                else:
                    self._add_stream(chr(event.key_code))
            elif event.key_code in self._map:
                req = self._map.get(event.key_code)
                if callable(req):
                    req()
        return event

class TerminalFrame(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         title="Integrated Terminal",
                         can_scroll=False,
                         reduce_cpu=True)
        self.model = model
        self.cmd_model = SimpleCommandModel()
        self.cmd_model.stdout = self._display_output
        self.suggestions = []

        self.model.attach(self)

        layout = Layout([70, 10,20])#, #fill_frame=True)
        self.add_layout(layout)
        self.terminal = TerminalWidget('terminal', height=Widget.FILL_FRAME, title='EchoMaze Shell', model=self.cmd_model)
        layout.add_widget(self.terminal, 0)
        self.suggestions_list = MultiColumnListBox(
            height=5,
            columns=[0],
            options=[],
            name="suggestions",
            on_select=self._on_suggestion_select
        )
        layout.add_widget(VerticalDivider(),1)
        layout.add_widget(self.suggestions_list, 2)
        layout.add_widget(Button("Suggest Commands", self._load_suggestions), 2)
        layout.add_widget(Button("Clear", self._clear_terminal), 2)
        layout.add_widget(Button("Close", self._close), 2)
    
        self.fix()
        self._load_suggestions()
    
        self.fix()
        self._load_suggestions()

    def observerUpdate(self, **kwargs):
        if 'selected_ip' in kwargs:
            self._load_suggestions()

    def _on_suggestion_select(self):
        selected = self.suggestions_list.value
        if selected is not None and selected < len(self.suggestions):
            # Instead of setting command, perhaps print to terminal
            self.terminal._add_stream(self.suggestions[selected] + '\n')

    def _load_suggestions(self):
        ip = self.model.selected_ip
        if ip:
            self.suggestions = []
            # Get suggestions from model
            specific = self.model.get_suggestions_for_ip(ip)
            generic = self.model.get_generic_suggestions_for_ip(ip)
            for sug in specific + generic:
                if hasattr(sug, 'linux') and sug.linux:
                    self.suggestions.append(sug.linux)
                elif hasattr(sug, 'desc'):
                    self.suggestions.append(sug.desc)
                elif isinstance(sug, str):
                    self.suggestions.append(sug)
            # If no suggestions, add some defaults based on ports
            
        else:
            self.suggestions = ["Select an IP to get pivoting suggestions"]
        self._update_suggestions()

    def _update_suggestions(self):
        options = [(sug, i) for i, sug in enumerate(self.suggestions)]
        self.suggestions_list.options = options

    def _display_output(self, output):
        self.terminal.dataIn = output

    def _clear_terminal(self):
        self.terminal.reset()

    def process_event(self, event):
        """
        nota: l: En los sistemas basados en terminal, las teclas de control se mapean 
        a los primeros 26 caracteres de la tabla ASCII. Por lo tanto, Ctrl+A es 1, Ctrl+B es 2,
        Ctrl+C es 3, y así sucesivamente
        """
        if isinstance(event, KeyboardEvent):
            # Ctrl+C tiene el código de tecla 3
            if event.key_code == 18:
                self._clear_terminal()
                return None  # Devolver None indica que el evento fue procesado
            
            # Ctrl+Q tiene el código de tecla 17
            elif event.key_code == 17:
                self._close()
                return None
            
            # Ctrl+S tiene el código de tecla 19
            elif event.key_code == 19:
                self._on_suggestion_select()
                return None

        return super().process_event(event)

    def _close(self):
        self.model.detach(self)
        raise NextScene('main')