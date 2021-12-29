
import numpy as np
from collections import deque

# todo: some quick tricks to see if keyboard effects work properly and a small demonstration of the effect. currently doesnt support multiple ripple waves

# event with 200 ripples cpu usage is pretty low
class Ripple:
    ii = None
    jj = None

    def __init__(self, pos_i, pos_j, arr_shape):
        self.pos_i = pos_i
        self.pos_j = pos_j
        self.current_r = 0.00001
        self.arr_shape = arr_shape

        # precompute for all ripples
        if Ripple.ii is None and Ripple.jj is None:
            Ripple.ii, Ripple.jj = np.meshgrid(range(self.arr_shape[0]), range(self.arr_shape[1]), indexing='ij')

        # precompute for this ripple
        self.ii = Ripple.ii - self.pos_i
        self.jj = Ripple.jj - self.pos_j
        self.sumii2jj2 = self.ii**2 + self.jj**2

    def step(self):
        scale = self.current_r * 1.5 # ripple wave length
        output = np.exp( -np.abs(self.sumii2jj2 - self.current_r**2) / scale )
        #output *= 1 / self.current_r # decrease wave magnitute over time v1
        #output *= 1 / np.sqrt(self.current_r) # decrease wave magnitute over time v2
        #output *= 1 / self.current_r**0.8 # decrease wave magnitute over time v3
        output *= 3 / self.current_r**0.8 # decrease wave magnitute over time v4
        
        output = output.reshape((self.arr_shape[0], self.arr_shape[1], 1))
        self.current_r += 0.7 # speed
        return output

    def is_visible(self):
        return self.current_r < 20 # magic number :S


class CustomEffect:
    def __init__(self, arr, driver):
        self.arr = arr * 0
        self.driver = driver
        self.keyboard_mapper = KeyboardMapper(self.keyboard_cb)
        self.ripple_list = deque()

    def keyboard_cb(self, code, state, position):
        # state=0 (press), state=1 (release), state=2 (hold)
        if position is not None and state == 0:
            i, j = position
            self.ripple_list.append( Ripple(i, j, self.arr.shape) )

    def update(self):
        self.arr = self.arr * 0
        #print("ripple_list size:", len(self.ripple_list))

        output = None
        for ripple in self.ripple_list:
            if ripple.is_visible():
                if output is None:
                    output = ripple.step()
                else:
                    output += ripple.step()

        if len(self.ripple_list) > 0:
            if not self.ripple_list[0].is_visible():
                self.ripple_list.popleft()

        if output is not None:
            output = np.clip(output, 0.0, 1.0)
            self.arr[:,:,:] = output

        return self.arr

    def get_fps(self):
        return 20

    def is_enabled(self):
        return True

    def on_exit(self):
        pass



#################################################################################################################



import inputs
import threading
class KeyboardMapper:
    def __init__(self, callback):
        self.selected_device = None
        self.callback_function = None
        self.is_enabled = True
        self.thread_list = []
        self.spinner = None

        NOKEY = None # There is a led but no key
        # "KEY_ " prefix are removed for default_map and will be added in process_map()
        #  Note: FN key doesnt work with this method
        self.default_map=[#|  0        |  1     |  2     |  3        |  4       |  5     |  6     |  7     |  8     |  9     |  10       |  11        |  12         |  13          |  14         |  15      |  16      |  17         |
                           ["ESC"      , "F1"   , "F2"   , "F3"      , "F4"     , "F5"   , "F6"   , "F7"   , "F8"   , "F9"   , "F10"     , "F11"      , "F12"       , "PAUSE"      , "SYSRQ"     , "DELETE" , "KPMINUS", "KPPLUS"    ], # 0
                           ["GRAVE"    , "1"    , "2"    , "3"       , "4"      , "5"    , "6"    , "7"    , "8"    , "9"    , "0"       , "MINUS"    , "EQUAL"     , None         , "BACKSPACE" , "NUMLOCK", "KPSLASH", "KPASTERISK"], # 1
                           ["TAB"      , None   , "Q"    , "W"       , "E"      , "R"    , "T"    , "Y"    , "U"    , "I"    , "O"       , "P"        , "LEFTBRACE" , "RIGHTBRACE" , "ENTER"     , "KP7"    , "KP8"    , "KP9"       ], # 2
                           ["CAPSLOCK" , None   , "A"    , "S"       , "D"      , "F"    , "G"    , "H"    , "J"    , "K"    , "L"       , "SEMICOLON", "APOSTROPHE", "BACKSLASH"  , NOKEY       , "KP4"    , "KP5"    , "KP6"       ], # 3
                           ["LEFTSHIFT", NOKEY  , "102ND", "Z"       , "X"      , "C"    , "V"    , "B"    , "N"    , "M"    , "COMMA"   , "DOT"      , "SLASH"     , "RIGHTSHIFT" , "UP"        , "KP1"    , "KP2"    , "KP3"       ], # 4
                           ["LEFTCTRL" , None   , None   , "LEFTMETA", "LEFTALT", None   , None   , "SPACE", None   , None   , "RIGHTALT", "COMPOSE"  , "RIGHTCTRL" , "LEFT"       , "DOWN"      , "RIGHT"  , "KP0"    , "KPDOT"     ]  # 5
                         ]
        self.default_map_inv = {}
        self.process_map()

        self.listen_for_magic_key()
        self.register_callback(callback)

    def process_map(self):
        rows = len(self.default_map)
        cols = len(self.default_map[0])
        for i in range(rows):
            for j in range(cols):
                keycode = self.default_map[i][j]
                if keycode is not None:
                    self.default_map_inv["KEY_" + keycode] = (i,j)

    # Listens all input devices, sets selected_device to which gets left or right ctrl stroke first
    def listen_for_magic_key(self):
        for device in inputs.devices:
            if device.device_type == "kbd":
                thread = threading.Thread(target=self.listen_for_magic_key_entrypoint_, args=(device,))
                self.thread_list.append(thread)
                thread.start()

    def listen_for_magic_key_entrypoint_(self, device):
        print("Listening magic key from device:", device, )
        while self.selected_device is None:
            events = device.read()
            if events:
                for event in events:
                    if self.selected_device is None and (event.code == "KEY_LEFTCTRL" or event.code == "KEY_RIGHTCTRL"):
                        print("Magic key ({}) detected from device: {}".format(event.code, device.name))
                        self.selected_device = device
                        self.spinner = threading.Thread(target=self.spinner_entrypoint_, args=(self.selected_device,))
                        self.spinner.start()

    def spinner_entrypoint_(self, selected_device):
        while self.is_enabled:
            events = selected_device.read()
            if events:
                for event in events:
                    if event.ev_type == "Key":
                        position = None
                        if event.code in self.default_map_inv:
                            position = self.default_map_inv[event.code]
                        self.callback_function(event.code, event.state, position)

    def register_callback(self, callback):
        self.callback_function = callback

    def exit(self):
        self.is_enabled = False

#def event_cb(code, state, position):
#    print(code, state, position)
#keyboard_mapper = KeyboardMapper(event_cb)



#################################################################################################################



"""
# KEY MAPPINGS ARE FOUND WITH STELLARIS 15 GEN3 USING THIS CODE
import numpy as np
class CustomEffect:
    def __init__(self, arr, driver):
        self.arr = arr
        self.driver = driver
        self.i = 0
        self.j = 15   # SELECT COLUMN HERE
    def update(self):
        self.arr = self.arr * 0
        self.arr[self.i, self.j] = np.array([1.0, 1.0, 1.0])
        self.i = (self.i + 1) % 6
        return self.arr
    def get_fps(self):
        return 1
    def is_enabled(self):
        return True
    def on_exit(self):
        pass
"""