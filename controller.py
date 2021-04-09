import os

import pulsectl

import pulse

class Controller:
    MUSIC_SINK = "music_in"
    COMM_SINK = "communication_in"
    AUX_SINK = "aux_in"
    SYSTEM_SINK = "system_in"
    MICROPHONE = "MICROPHONE"
    MAIN_MIX = "main_mix"

    def __init__(self):
        print("Init Controller")
        self.client = pulsectl.Pulse("volume-control")
        self.defaultSource = self.client.server_info().default_source_name
        self.defaultSink = self.client.server_info().default_sink_name
        self.defaultSinks = {}
        self.sinks = {}
        self.getSinks()
        self._initPulse()

    def _loadModules(self):
        self.sinks.update({self.MUSIC_SINK: pulse.createSink(self.client, self.MUSIC_SINK)})
        self.sinks.update({self.COMM_SINK: pulse.createSink(self.client, self.COMM_SINK)})
        self.sinks.update({self.AUX_SINK: pulse.createSink(self.client, self.AUX_SINK)})
        self.sinks.update({self.SYSTEM_SINK: pulse.createSink(self.client, self.SYSTEM_SINK)})

        self.sinks.update({pulse.monitorOf(self.MUSIC_SINK): pulse.createLoopback(self.client,
                                                                                  pulse.monitorOf(self.MUSIC_SINK),
                                                                                  self.defaultSink)})
        self.sinks.update({pulse.monitorOf(self.COMM_SINK): pulse.createLoopback(self.client,
                                                                                 pulse.monitorOf(self.COMM_SINK),
                                                                                 self.defaultSink)})
        self.sinks.update({pulse.monitorOf(self.AUX_SINK): pulse.createLoopback(self.client,
                                                                                pulse.monitorOf(self.AUX_SINK),
                                                                                self.defaultSink)})
        self.sinks.update({pulse.monitorOf(self.SYSTEM_SINK): pulse.createLoopback(self.client,
                                                                                   pulse.monitorOf(self.SYSTEM_SINK),
                                                                                   self.defaultSink)})

        self.client.sink_default_set(self.SYSTEM_SINK)

        print(self.sinks)

    def _moveSinks(self, music: list):
        print("##### SINK INPUTS #####")
        input_sinks = self.client.sink_input_list()
        print(input_sinks)
        for inputSink in input_sinks:
            print(inputSink)
            if inputSink.name == "Spotify":
                print("Moving Spotify to music sink")
                self.client.sink_input_move(inputSink.index, music.index)

    def _initPulse(self):
        self._loadModules()

        music = self.client.get_sink_by_name(self.MUSIC_SINK)
        comm = self.client.get_sink_by_name(self.COMM_SINK)
        aux = self.client.get_sink_by_name(self.AUX_SINK)
        system = self.client.get_sink_by_name(self.SYSTEM_SINK)

        print("Music: {} | Communication: {} | Aux: {} | System: {}".format(music.index, comm.index,
                                                                            aux.index, system.index))

        self._moveSinks(music)

    def restart(self):
        print("Restarting controller")
        self.unloadModules()
        self.getSinks()
        self._loadModules()

    def getSinks(self):
        sinks = self.client.sink_list()
        for sink in sinks:
            self.defaultSinks.update({sink.name: sink.description})

        print(self.defaultSinks)

    def _move(self, sink: int, to_sink: str):
        index_sink = self.client.get_sink_by_name(to_sink).index
        print(sink, index_sink)
        self.client.sink_input_move(sink,
                                    index_sink)

    def setSink(self, sink: str):
        self.defaultSink = sink
        input_sinks = self.client.sink_input_list()
        for inputSink in input_sinks:
            if (self.MUSIC_SINK in inputSink.name
                    or self.AUX_SINK in inputSink.name
                    or self.COMM_SINK in inputSink.name
                    or self.SYSTEM_SINK in inputSink.name):
                self._move(inputSink.index, sink)

    def unloadModules(self):
        os.system("pacmd unload-module module-null-sink")
        # os.system("pacmd unload-module module-combine-sink")
        os.system("pacmd unload-module module-loopback")

    def setVolume(self, sink_name: str, volume: int):
        if sink_name != "MICROPHONE":
            self.client.volume_set_all_chans(self.client.get_sink_by_name(sink_name), volume / 100)
        else:
            self.setMicVolume(volume)

    def setMicVolume(self, volume: int):
        self.client.volume_set_all_chans(self.client.get_source_by_name(self.defaultSource),
                                         volume / 100)

    def shutdown(self):
        self.unloadModules()
        self.client.close()
