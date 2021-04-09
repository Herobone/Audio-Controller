import threading
from typing import Callable

import mido
from mido.ports import BaseInput
from mido.backends.backend import Backend
from mido.messages import Message

from controller import Controller

midoBackend: Backend = mido


class MIDIController:
    def __init__(self, volume_change_callback, aux_knob_change_callback, button_press_callback, running: threading.Event):
        self.inputDevice: BaseInput
        self.inputDevice = midoBackend.open_input(midoBackend.get_input_names()[0])
        self.channelMap = [0, 0, 0, 0, 0]
        self.volumeChange: Callable[[str, int], None] = volume_change_callback.emit
        self.knobChange: Callable[[int, int], None] = aux_knob_change_callback.emit
        self.buttonPress: Callable[[int], None] = button_press_callback.emit
        self.running = running
        self.loop()

    def loop(self):
        while not self.running.isSet():
            msg: Message = self.inputDevice.receive()
            if msg.type == "control_change":
                self.processCC(msg)

    def auxVolumeChange(self, value: int):
        self.volumeChange(Controller.AUX_SINK, value)

    def systemVolumeChange(self, value: int):
        self.volumeChange(Controller.SYSTEM_SINK, value)

    def musicVolumeChange(self, value: int):
        self.volumeChange(Controller.MUSIC_SINK, value)

    def commVolumeChange(self, value: int):
        self.volumeChange(Controller.COMM_SINK, value)

    def micVolumeChange(self, value: int):
        self.volumeChange("MICROPHONE", value)

    def processCC(self, msg: Message):
        if msg.control == 25:
            self.auxVolumeChange(msg.value)
        if msg.control == 19:
            self.systemVolumeChange(msg.value)
        if msg.control == 13:
            self.musicVolumeChange(msg.value)
        if msg.control == 7:
            self.commVolumeChange(msg.value)
        if msg.control == 1:
            self.micVolumeChange(msg.value)
