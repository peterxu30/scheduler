from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
import msgpack
import thread
import sys
import time

from ssu_instances import *
from ssu import SSU_Link

class Scheduler(object):
    
    def __init__(self, signal, slot, ssus):
        self.signal = signal
        self.slot = slot
        self.ssu_list = SSU_Link.create_ssu_list(ssus)

        self.bw_client = Client()
        self.bw_client.setEntityFromEnviron()
        self.bw_client.overrideAutoChainTo(True)

    def run(self):
        print "scheduler running"
        self.bw_client.subscribe(self.signal, self.on_message)
        while True:
            print "sleeping"
            time.sleep(10000)

    def publish(self, **kwargs):
        kwargs = kwargs.get('kwargs')
        sched = self.generate_schedule(kwargs.get('temperature'),
            kwargs.get('relative_humidity'),
            kwargs.get('heating_setpoint'),
            kwargs.get('cooling_setpoint'),
            kwargs.get('override'),
            kwargs.get('fan'),
            kwargs.get('mode'),
            kwargs.get('state'),
            kwargs.get('time'))
        self.publish_schedule(*sched)

    def generate_schedule(self, temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time):
        data = (temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time)
        curr = self.ssu_list
        while curr is not None:
            data = curr.ssu.generate_schedule(*data)
            curr = curr.rest

        heating_setpt, cooling_setpt = data[2], data[3]

        if temp <= heating_setpt:
            mode = 1
        elif temp >= cooling_setpt:
            mode = 2

        return float(heating_setpt), float(cooling_setpt), override, mode, fan

    def publish_schedule(self, heating_setpt, cooling_setpt, override, mode, fan):
        assert isinstance(heating_setpt, float)
        assert isinstance(cooling_setpt, float)
        assert isinstance(override, bool)
        assert isinstance(mode, int)
        assert isinstance(fan, bool)

        t = {'heating_setpoint': heating_setpt, 'cooling_setpoint': cooling_setpt, 'override': override, 'mode': mode, 'fan': fan}
        po = PayloadObject((2,1,1,0), None, msgpack.packb(t))
        print t
        self.bw_client.publish(self.slot, payload_objects =(po,))

    def on_message(self, bw_message):
        print "msg received"
        try:
            for po in bw_message.payload_objects:
                if po.type_dotted == (2,1,1,0):
                    tstat_data = msgpack.unpackb(po.content)
                    thread.start_new_thread(self.publish, (), {'kwargs': tstat_data})
        except Exception as e:
            print e

#main
signal = "scratch.ns/services/s.vthermostat/vthermostat/i.xbos.thermostat/signal/info"
slot = "scratch.ns/services/s.vthermostat/vthermostat/i.xbos.thermostat/slot/state"
ssu_list = [SSU_Natural(), SSU_Social(), SSU_Custom()]
schedule = Scheduler(signal, slot, ssu_list)
schedule.run()
