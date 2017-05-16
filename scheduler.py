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
        self.bw_client.subscribe(self.slot, self.on_message)
        while True:
            print "sleeping"
            # thread.start_new_thread(self.publish, (), {'kwargs': {'temperature': 10, 'relative_humidity': 5, 'heating_setpoint':11.0, 'cooling_setpoint': 5.0, 'override':False, 'fan':False, 'mode': 3, 'state': 3, 'time': time.time() * 1e9}})
            # print "published"
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
        self.bw_client.publish(self.signal, payload_objects =(po,))

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
signal = "scratch.ns/services/s.schedule/schedule1/i.xbos.thermostat/signal/info"
slot = "scratch.ns/services/s.schedule/schedule1/i.xbos.thermostat/slot/state"
ssu_list = [SSU_Natural(), SSU_Social(), SSU_Custom()]
schedule = Scheduler(signal, slot, ssu_list)
# schedule.run()
thread.start_new_thread(schedule.run, (), {})

signal2 = "scratch.ns/services/s.schedule/schedule2/i.xbos.thermostat/signal/info"
slot2 = "scratch.ns/services/s.schedule/schedule2/i.xbos.thermostat/slot/state"
ssu_list2 = [SSU_Social(), SSU_Custom()]
schedule2 = Scheduler(signal2, slot2, ssu_list2)
# thread.start_new_thread(schedule2.run, (), {})

while True:
    time.sleep(1000)
