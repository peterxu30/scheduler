from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
import copy
import msgpack
import Queue
import sys
import thread
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

        self.last_received_schedule = {'kwargs': {
            'temperature': None, 
            'relative_humidity': None, 
            'heating_setpoint': None, 
            'cooling_setpoint': None, 
            'override': None, 
            'fan': None, 
            'mode': None, 
            'state': None, 
            'time': time.time() * 1e9}}

    def run(self):
        print "scheduler running"
        self.bw_client.subscribe(self.slot, self.on_message)
        while True:
            #For time-based SSUs. Sends a signal every hour. Publishing will fail if initial SSU is not strictly time-based.
            msg = copy.deepcopy(self.last_received_schedule)
            msg['kwargs']['time'] = time.time() * 1e9
            thread.start_new_thread(self.publish, (), msg)
            time.sleep(3600)
            print "sleeping"

    def publish(self, **kwargs):
        try:
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
        except Exception as e:
            print "Failed to publish message", e

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
                    self.last_received_schedule = {'kwargs': tstat_data}
                    thread.start_new_thread(self.publish, (), self.last_received_schedule)
        except Exception as e:
            print e

#main
signal = "scratch.ns/services/s.schedule/schedule1/i.xbos.thermostat/signal/info"
slot = "scratch.ns/services/s.schedule/schedule1/i.xbos.thermostat/slot/state"
ssu_list = [SSU_Natural(), SSU_Social(), SSU_Custom()]
schedule = Scheduler(signal, slot, ssu_list)
thread.start_new_thread(schedule.run, (), {})

signal2 = "scratch.ns/services/s.schedule/schedule2/i.xbos.thermostat/signal/info"
slot2 = "scratch.ns/services/s.schedule/schedule2/i.xbos.thermostat/slot/state"
ssu_list2 = [SSU_Social(), SSU_Custom()]
schedule2 = Scheduler(signal2, slot2, ssu_list2)
thread.start_new_thread(schedule2.run, (), {})

while True:
    time.sleep(1000)
