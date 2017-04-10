from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
import msgpack
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
        print "Scheduler running"
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
            sched = curr.ssu.generate_schedule(*data)
            curr = curr.rest

        heating_setpt, cooling_setpt = data[2], data[3]

        if temp <= heating_setpt:
            mode = 1
        elif temp >= cooling_setpt:
            mode = 2

        print heating_setpt, cooling_setpt, override, mode, fan
        return heating_setpt, cooling_setpt, override, mode, fan

    def publish_schedule(self, heating_setpt, cooling_setpt, override, mode, fan):
        t = {'heating_setpoint': heating_setpt, 'cooling_setpoint': cooling_setpt, 'override': override, 'mode': mode, 'fan': fan}
        po = PayloadObject((2,1,1,0), None, msgpack.packb(t))
        print "about to publish", t
        # self.bw_client.publish(slot, payload_objects =(po,))
        print "published", t

    def on_message(self, bw_message):
        print "msg received"
        for po in bw_message.payload_objects:
            if po.type_dotted == (2,1,1,0):
                tstat_data = msgpack.unpackb(po.content)
                self.publish(kwargs=tstat_data)

#main
signal = "scratch.ns/services/s.vthermostat/vthermostat/i.xbos.thermostat/signal/info"
slot = "scratch.ns/services/s.vthermostat/vthermostat/i.xbos.thermostat/slot/state"
ssu_list = [SSU_Natural(), SSU_Social(), SSU_Custom()]
schedule = Scheduler(signal, slot, ssu_list)
schedule.run()
