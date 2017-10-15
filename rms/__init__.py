from multiprocessing import Process, Condition, Semaphore
from multiprocessing.sharedctypes import RawValue, RawArray
import ctypes
import numpy as np
from functools import *
import threading

class Module(Process):
    def __init__(self, interface, reads=[], writes=[]):
        Process.__init__(self)
        self._reads = reads
        self._writes = writes
        self.interface = interface
        for variable in self._reads:
            self.interface.gate(variable).addConsumer()
        for variable in self._writes:
            self.interface.gate(variable).addProducer()

    def run(self):
        self.setup()

        while True:
            for variable in self._reads:
                self.interface.gate(variable).awaitProducer()

            result = self.iterate()

            for variable in self._reads:
                self.interface.gate(variable).consume()

            for variable in self._writes:
                self.interface.gate(variable).produce()

            for variable in self._writes:
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
        lookup = { (mapping[variable] if variable in mapping.keys() else variable) : index for variable, index in self._lookup.items() }
        return Interface(self._objects, self._gates, lookup)

    def use(self, namespace):
        n = len(namespace) + 1
        lookup = { (variable[n:] if variable.startswith(namespace + ".") else variable) : index for variable, index in self._lookup.items() }
        return Interface(self._objects, self._gates, lookup)

    def wrap(self, namespace):
        lookup = { (namespace + "." + variable) : index for variable, index in self._lookup.items() }
        return Interface(self._objects, self._gates, lookup)

    def link(self, origin, target):
        self._gates[self._lookup[origin]] = self._gates[self._lookup[target]]

class Gate:
    def __init__(self):
        self.consumers = 0
        self.producers = 0
        self.producerSemaphore = Semaphore(value=0)
        self.consumerSemaphore = Semaphore(value=0)

    def addConsumer(self):
        self.consumers += 1

    def addProducer(self):
        self.producers += 1

    def awaitProducer(self):
        for i in range(self.producers):
            self.producerSemaphore.acquire()

    def produce(self):
        for i in range(self.consumers):
            self.producerSemaphore.release()

    def awaitConsumers(self):
        for i in range(self.consumers):
            self.consumerSemaphore.acquire()

    def consume(self):
        for i in range(self.producers):
            self.consumerSemaphore.release()

    def unlock(self, name):
        self._locks[name].release()

typemap = {
    "float" : ctypes.c_double,
    "int" : ctypes.c_int64,
    "uint8" : ctypes.c_uint8,
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
