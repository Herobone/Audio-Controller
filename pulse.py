from pulsectl import Pulse
from typing import List


def createSink(client: Pulse, name):
    return client.module_load(name="module-null-sink",
                              args="sink_name={} sink_properties=device.description={}".format(name, name))


def createCombiner(client: Pulse, name, slaves: List[str]):
    client.module_load(name="module-combine-sink",
                       args="sink_name={} sink_properties=device.description={} slaves={}".format(name, name,
                                                                                                  ",".join(slaves)))


def createLoopback(client: Pulse, loopFrom, to=None):
    if to is None:
        to = client.server_info().default_sink_name

    return client.module_load(name="module-loopback",
                              args="source={} sink={}".format(loopFrom, to))


def createSource(client: Pulse, name):
    client.module_load(name="module-null-source",
                       args="source_name={} source_properties=device.description={}".format(name, name))


def monitorOf(sink: str):
    return sink + ".monitor"
