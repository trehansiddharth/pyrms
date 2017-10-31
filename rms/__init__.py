from multiprocessing import Process, Condition, Lock, Semaphore
from multiprocessing.sharedctypes import RawValue, RawArray
import ctypes
import numpy as np
from functools import *
import threading

class Module(Process):
    def __init__(self, interface, reads=[], writes=[]):
        Process.__init__(self)
        self._reads = {}
        self._writes = {}
        self.interface = interface
        for variable in reads:
            self._reads[variable] = self.interface.gate(variable).addConsumer()
        for variable in writes:
            self._writes[variable] = self.interface.gate(variable).addProducer()

    def run(self):
        self.setup()

        while True:
            for variable, i in self._reads.items():
                self.interface.gate(variable).awaitProducer(i)

            result = self.iterate()

            for variable, i in self._reads.items():
                self.interface.gate(variable).consume(i)

            for variable, i in self._writes.items():
                self.interface.gate(variable).produce()

            for variable, i in self._writes.items():
                self.interface.gate(variable).awaitConsumers()

    def startAsThread(self):
        thread = threading.Thread(target=self.run)
        thread.start()

class Interface:
    def __init__(self, objects={}, gates=None, lookup=None):
        if objects is None:
            self._objects = []
        elif type(objects) == type({}):
            self._objects = [value for _, value in objects.items()]
        elif type(objects) == type([]):
            self._objects = objects
        self._lookup = lookup or { variable : index for index, variable in enumerate(objects) }
        self._gates = gates or [Gate() for _ in self._objects]

    def __getitem__(self, variable):
        return self._objects[self._lookup[variable]]

    def __add__(self, other):
        n = len(self._objects)
        objects = self._objects + other._objects
        gates = self._gates + other._gates
        lookup = self._lookup.copy()
        lookup.update({ variable : n + index for variable, index in other._lookup.items() })
        return Interface(objects, gates, lookup)

    def __iadd__(self, other):
        n = len(self._objects)
        self._objects += other._objects
        self._gates += other._gates
        self._lookup.update({ variable : n + index for variable, index in other._lookup.items() })
        return self

    def gate(self, variable):
        return self._gates[self._lookup[variable]]

    def remap(self, mapping):
        lookup = {}
        for variable, index in self._lookup.items():
            if variable in mapping.keys():
                lookup[mapping[variable]] = index
            elif variable not in lookup.keys():
                lookup[variable] = index
        return Interface(self._objects, self._gates, lookup)

    def use(self, namespace):
        n = len(namespace) + 1
        lookup = {}
        for variable, index in self._lookup.items():
            if variable.startswith(namespace + "."):
                lookup[variable[n:]] = index
            elif variable not in lookup.keys():
                lookup[variable] = index
        return Interface(self._objects, self._gates, lookup)

    def wrap(self, namespace):
        lookup = {}
        for variable, index in self._lookup.items():
            if variable not in lookup.keys():
                lookup[namespace + "." + variable] = index
        return Interface(self._objects, self._gates, lookup)

    def link(self, origin, target):
        self._gates[self._lookup[origin]] = self._gates[self._lookup[target]]

class Gate:
    def __init__(self):
        self.consumers = []
        self.producers = []
        self.producing = False

    def addConsumer(self):
        self.consumers += [Semaphore(value=0)]
        self.producers += [Semaphore(value=0)]
        return len(self.consumers) - 1

    def addProducer(self):
        if self.producing:
            raise ValueError
        else:
            self.producing = True
            return 0

    def awaitProducer(self, i):
        if self.producing:
            self.producers[i].acquire()

    def produce(self):
        for lock in self.producers:
            lock.release()

    def awaitConsumers(self):
        for lock in self.consumers:
            lock.acquire()

    def consume(self, i):
        if self.producing:
            self.consumers[i].release()

typemap = {
    "float" : ctypes.c_double,
    "float64" : ctypes.c_double,
    "int" : ctypes.c_int64,
    "uint8" : ctypes.c_uint8,
    "uint16" : ctypes.c_uint16,
    "uint32" : ctypes.c_uint32,
    "uint64" : ctypes.c_uint64,
    "bool" : ctypes.c_byte }

def shared_value(default, dtype="float"):
    if dtype in typemap.keys():
        return RawValue(typemap[dtype], default)
    else:
        raise ValueError

def shared_ndarray(shape, dtype="float"):
    if dtype in typemap.keys():
        arr = RawArray(typemap[dtype], int(np.product(shape)))
        return np.ctypeslib.as_array(arr, shape=shape).reshape(shape)
    else:
        raise ValueError
