import threading
import traceback

from PyQt5 import QtWidgets
from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool
from typing import Tuple

from PyQt5.QtWidgets import QMainWindow

import mainWindow
import sys

from controller import Controller
from midi import MIDIController


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    volumeChange = pyqtSignal(str, int)
    auxKnobChange = pyqtSignal(tuple)
    buttonPress = pyqtSignal(int)


class MidiWorker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(MidiWorker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['volume_change_callback'] = self.signals.volumeChange
        self.kwargs['aux_knob_change_callback'] = self.signals.volumeChange
        self.kwargs['button_press_callback'] = self.signals.volumeChange

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class GUI(QMainWindow):
    def __init__(self, controller: Controller, *args, **kwargs):
        super(GUI, self).__init__()
        self.ui = mainWindow.Ui_MainWindow()
        self.controller = controller
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.running = threading.Event()

        self.args = args
        self.kwargs = kwargs

        self.kwargs["running"] = self.running

        self.midiWorker = MidiWorker(MIDIController, *self.args,
                                     **self.kwargs)  # Any other args, kwargs are passed to the run function

    def closeEvent(self, event):
        close = QtWidgets.QMessageBox.question(self,
                                               "QUIT",
                                               "Are you sure want to close the audio controller?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if close == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def start(self):
        self.ui.setupUi(self)
        self._setupActions()
        self.show()

        self.midiWorker.signals.volumeChange.connect(self.setVolume)

        # Execute
        self.threadpool.start(self.midiWorker)

    def stop(self):
        self.running.set()
        pass

    def setVolume(self, sink_name: str, volume: int):
        self.controller.setVolume(sink_name, volume)
        if sink_name == Controller.SYSTEM_SINK:
            self.ui.slider_volume_channel_3.setValue(volume)
        elif sink_name == Controller.AUX_SINK:
            self.ui.slider_volume_channel_4.setValue(volume)
        elif sink_name == Controller.COMM_SINK:
            self.ui.slider_volume_channel_1.setValue(volume)
        elif sink_name == Controller.MUSIC_SINK:
            self.ui.slider_volume_channel_2.setValue(volume)
        elif sink_name == Controller.MICROPHONE:
            self.ui.slider_volume_channel_0.setValue(volume)

    def setVolumeMic(self, volume: int):
        self.controller.setMicVolume(volume)

    def setVolumeSystem(self, volume: int):
        self.controller.setVolume(Controller.SYSTEM_SINK, volume)

    def setVolumeAux(self, volume: int):
        self.controller.setVolume(Controller.AUX_SINK, volume)

    def setVolumeMusic(self, volume: int):
        self.controller.setVolume(Controller.MUSIC_SINK, volume)

    def setVolumeComm(self, volume: int):
        self.controller.setVolume(Controller.COMM_SINK, volume)

    def mainSinkChange(self):
        sink = self.ui.main_sink_combo_selector.currentData()
        print(sink)
        self.controller.setSink(sink)

    def _setupActions(self):
        idx, current_idx = 0, 0
        for name in self.controller.defaultSinks.keys():
            if name == self.controller.defaultSink:
                idx = current_idx

            self.ui.main_sink_combo_selector.addItem(self.controller.defaultSinks[name], name)
            current_idx += 1

        self.ui.main_sink_combo_selector.setCurrentIndex(idx)

        self.ui.restart_engine_button.clicked.connect(self.controller.restart)
        self.ui.slider_volume_channel_0.valueChanged.connect(self.setVolumeMic)
        self.ui.slider_volume_channel_1.valueChanged.connect(self.setVolumeComm)
        self.ui.slider_volume_channel_2.valueChanged.connect(self.setVolumeMusic)
        self.ui.slider_volume_channel_3.valueChanged.connect(self.setVolumeSystem)
        self.ui.slider_volume_channel_4.valueChanged.connect(self.setVolumeAux)
        self.ui.main_sink_combo_selector.currentIndexChanged.connect(self.mainSinkChange)
