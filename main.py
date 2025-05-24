import os, threading
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.app import App
from kivy.lang import Builder as build
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ObjectProperty, ColorProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.settings import SettingsWithSidebar
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from pydub import AudioSegment
from pydub.playback import play

# Config.set("kivy", "log_enable", "0")  # Disable logging
# Config.set("kivy", "log_level", "error")  # Only show critical errors
# Config.set("kivy", "log_maxfiles", "-1")  # Prevent log file creation
# Logger.disabled = True

left_keys = 'QWERASDFZXCV'
right_keys = 'UIOPJKL;M,./'


class EditableSpinner(BoxLayout):
    min_value = NumericProperty(0)
    max_value = NumericProperty(59)
    text = StringProperty("")
    hint = StringProperty("")
    # Cache the dropdown so it is created only once (lowest memory footprint)
    dropdown = ObjectProperty(None, allownone=True)

    def open_dropdown(self):
        """Open the dropdown list when the TextInput gains focus."""
        if not self.dropdown:
            self.dropdown = DropDown(auto_dismiss=False)
            self.load_dropdown(self.dropdown)
        self.dropdown.open(self.ids.textinput)
    
    def load_dropdown(self, dropdown):
        dropdown.clear_widgets()
        t = self.ids.textinput.text
        for i in range(int(t) if t.isnumeric() else self.min_value, self.max_value + 1):
            btn = Button(text=f"{i:02d}", size_hint_y=None, height=dp(44))
            # When a value is selected, update TextInput and dismiss.
            btn.bind(on_release=lambda btn: self.select_value(btn.text))
            dropdown.add_widget(btn)

    def dismiss_dropdown(self):
        """Dismiss the dropdown if the TextInput loses focus."""
        if self.dropdown:
            self.dropdown.dismiss()

    def select_value(self, value):
        """Update the TextInput with the selected value and dismiss dropdown."""
        self.text = value
        self.ids.textinput.text = value
        if self.dropdown:
            self.dropdown.dismiss()


class IconButton(ButtonBehavior, Image):
    def on_press(self):
        self.opacity = .5

    def on_release(self):
        self.opacity = 1


class Player(ToggleButton):
    timer = NumericProperty(600) #Seconds
    pause = BooleanProperty(True) #Pause Checker
    affect = ObjectProperty(None)
    bg_color = ColorProperty((0,0,0,0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_time()
        self.bind(
            timer = self.show_time,
            pause = self.on_pause,
            disabled = self.on_disabled
        )

    def on_disabled(self, *a):
        root = App.get_running_app().root
        affect = self.affect
        if affect:
            affect.disabled = self.disabled
        if root:
            root.started = False
            root.paused = True
            root.toggle_pause()

    def on_press(self):
        self.opacity = .5

    def on_release(self):
        self.root.switch(self)
        self.pause = True

    def on_pause(self, *args):
        if not self.pause:
            Clock.schedule_interval(self.play, .1)
            self.opacity = 1
        else:
            Clock.unschedule(self.play)

    def play(self, *args): self.timer -= .1

    def show_time(self, *args, **kwargs):
        hours = self.timer // 3600
        mins = str(int(self.timer % 3600 // 60))
        secs = self.timer % 60

        if self.timer <= 0: self.text = '0'
        else:
            self.text = (str(int(hours)) + ':' if hours else '') + ('0' * (2 - len(mins)) + mins + ':' if float(mins) or hours else '') + ('0' if secs < 10 else '') + (str(round(secs, 2)))


class TimerPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = App.get_running_app().config

    def apply_timer(self):
        try:
            hours, minutes, seconds = self.ids.spinner_hours, self.ids.spinner_minutes, self.ids.spinner_seconds
            hours = int('0' + hours.text)# or int('0' + hours.hint)
            minutes = int('0' + minutes.text)# or int('0' + minutes.hint)
            seconds = int('0' + seconds.text)# or int('0' + seconds.hint)

        except:pass

        else:
            time = 3600*hours + 60*minutes + seconds
            if time > 0:
                self.config.set('Timing', 'Time', str(3600*hours + 60*minutes + seconds))
                self.config.write()

        finally:self.dismiss()

    def load_preset_time(self):
        sh, sm, ss = self.ids.spinner_hours, self.ids.spinner_minutes, self.ids.spinner_seconds
        n = self.config.getint('Timing', 'time')
        hours = n//3600
        mins = n%3600//60
        secs = n%60
        sh.hint = f"{'0' if not hours//10 else ''}{hours}"
        sm.hint = f"{'0' if not mins//10 else ''}{mins}"
        ss.hint = f"{'0' if not secs//10 else ''}{secs}"

    def on_pre_open(self):
        self.load_preset_time()

    def on_pre_dismiss(self):
        root = App.get_running_app().root
        if root.started:
            root.paused = False
            root.toggle_pause()
        else:
            root.configure()

class Player1(Player):bg_color = ColorProperty((.5,0,0,1))
class Player2(Player):bg_color = ColorProperty((0,0,.5,1))


class Clocker(FloatLayout):
    time = NumericProperty(10)
    font_size = NumericProperty(20)
    increment = NumericProperty(0)

    font = StringProperty('')

    hover_rect = ListProperty([0,0,0,0])

    bg_color = ColorProperty((0,0,0,1))
    hover_color = ColorProperty((.5,.5,.5,1))

    paused = BooleanProperty(True)

    audio = ObjectProperty(None, allownone=True)
    hover = ObjectProperty(None, allownone=True)
    timer = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = App.get_running_app().config
        self.audio = AudioSegment.from_wav('assets/tick.wav')
        self.configure()

        one, two = self.ids.one, self.ids.two
        one.affect, two.affect = two, one
        self.affected = one
        self.started = False

        self.bind(hover = self.on_hover)
        Window.bind(
            mouse_pos = self.on_mouse_pos,
            on_key_down = self.on_key_down
        )

    def configure(self, *args):
        one, two = self.ids.one, self.ids.two
    
    #   Colors
        self.bg_color = self.config.get('Colors', 'Background')
        self.hover_color = self.config.get('Colors', 'hover-color')
        one.bg_color = self.config.get('Colors', 'Player1')
        two.bg_color = self.config.get('Colors', 'Player2')
        one.color = two.color = self.config.get('Colors', 'Font-color')

        for child in self.ids.deadzone.children:
            child.color = self.config.get('Colors', 'icon-color')

        if self.config.getboolean('Increments', 'allow-increments'):
            self.increment = self.config.getint('Increments', 'increment-by')
        else: self.increment = 0

    
    #   Timing
        one.timer = two.timer = self.config.getint('Timing', 'Time')
    
    #   Fontsize
        one.font_size = two.font_size = self.config.getint('text', 'font-size')

    def on_hover(self, me, hover):
        if hover is not None: self.hover_rect = list(hover.pos) + list(hover.size)

    def on_key_down(self, window, keycode, scancode, text, modifiers):
        one, two = self.ids.one, self.ids.two
        
        # Convert key to uppercase for matching
        if text != None:
            if text.upper() in left_keys:
                if one.state == 'normal':
                    one.state = 'down'
                    two.state = 'normal'
                    one.on_release()
            elif text.upper() in right_keys:
                if two.state == 'normal':
                    two.state = 'down'
                    one.state = 'normal'
                    two.on_release()
            else:pass
                # print(f"Blocked key: {text.upper()}")

    def on_mouse_pos(self, win, pos):
        for child in self.ids.deadzone.children:
            if child.__class__ == Widget: continue
            if child.collide_point(*pos):
                self.hover = child
                break
        else: self.hover = None

    def open_settings(self):
        self.ids.one.pause = self.ids.two.pause = self.paused = True
        App.get_running_app().open_settings()

    def play(self):
        if not self.ids.sound.mute: threading.Thread(target = play, args=(self.audio,)).start()

    def reset(self):
        one, two = self.ids.one, self.ids.two
        one.opacity = two.opacity = 1
        one.pause = two.pause = self.paused = True
        self.configure()

    def set_timer(self):
        one, two = self.ids.one, self.ids.two
        one.pause = two.pause = self.paused = True
        if not self.timer:
            self.timer = TimerPopup(background_color = self.bg_color, title_color=one.color, separator_color=two.color)
            self.bind(bg_color = self.timer.setter('background_color'))
            one.bind(color = self.timer.setter('title_color'))
            two.bind(color = self.timer.setter('separator_color'))
        self.timer.open()

    def switch(self, player):
        try:
            self.play()
            t1, t2 = self.ids.one.timer, self.ids.two.timer
            case1 = self.started and not player.pause
            if not self.started and t1 != 0 and t2 != 0:
                self.started = True
                self.paused = False
            elif t1 == 0 or t2 == 0:
                self.reset()
                self.started = True
                self.paused = False
            
            if self.paused == True and t1 > 0 and t2 > 0: self.paused = False

            if self.started and not self.paused:
                self.affected = player.affect
                self.affected.pause = False
            if case1: player.timer += self.increment
        except:pass
        player.opacity = .5

    def toggle_pause(self):
        one, two = self.ids.one, self.ids.two
        if not self.started:
            if one.timer > 0 and two.timer > 0: self.started = True
            else:self.paused = True

        if self.paused:
            one.pause = two.pause = self.paused = True
        else:
            self.affected.pause = self.paused
            self.affected.affect.on_press()


class ChessClock(App):
    settings_cls = SettingsWithSidebar
    icon = 'assets/icon.ico'
    use_kivy_settings = False
    def build(self):
        return Clocker()

    def build_config(self, config):
        config.setdefaults(
            'Colors', {
                'Player1': '#7f0000ff',
                'Player2': '#00007fff',
                'Background': '#000000ff',
                'Font-color': '#ffffffff',
                'hover-color': '#808080ff',
                'icon-color': '#ffffffff'
                },
        )
        config.setdefaults(
            'Increments', {
                'allow-increments': True,
                'increment-by': 2
            }
        )
        config.setdefaults(
            'Timing', {
                'Time':600
            }
        )
        config.setdefaults(
            'text', {
                'font-size': 50,
            }
        )

    def build_settings(self, settings):
        settings.add_json_panel('App', self.config, data=open('assets/settings.json', "r").read())

    def get_application_config(self):
        app_dir = os.path.join(self.user_data_dir, "config") 

        if not os.path.exists(app_dir):
            os.makedirs(app_dir)

        return os.path.join(app_dir, "my_app.ini")

    def on_config_change(self, config, section, key, value):
        self.root.configure()

build.load_file('assets/main.kv')
ChessClock().run()