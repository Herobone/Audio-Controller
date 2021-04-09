#!/usr/bin/python3
import sys

import pulsectl
from PyQt5 import QtWidgets

from controller import Controller
from gui import GUI


class AudioController:

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.controller = Controller()
        self.gui = GUI(self.controller)

    def mainLoop(self):
        print("Program running")
        self.gui.start()
        sys.exit(self.app.exec_())

    def shutdown(self):
        self.gui.stop()

        self.controller.shutdown()

    def run(self):
        try:
            self.mainLoop()
        except SystemExit:
            print("Killed")
            self.shutdown()
        except KeyboardInterrupt:
            print("Closing")
            self.shutdown()
        except pulsectl.pulsectl.PulseError as e:
            print("Error during Execution")
            print(type(e))
            print(e)
            self.controller.unloadModules()
        else:
            self.controller.unloadModules()


if __name__ == '__main__':
    audioController = AudioController()
    audioController.run()
