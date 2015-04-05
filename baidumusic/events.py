#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

from inspect import ismethod
from new import instancemethod
import re
import sys
import threading
import time
import weakref
import traceback

from logger import Logger

class Nothing(object):
    pass

_NONE = Nothing() # used by event for a safe None replacement

class _WeakMethod(object):
    """Represent a weak bound method, i.e. a method doesn't keep alive the
    object that it is bound to. It uses WeakRef which, used on its own,
    produces weak methods that are dead on creation, not very useful.
    Typically, you will use the getRef() function instead of using
    this class directly. """

    def __init__(self, method, notifyDead = None):
        """
            The method must be bound. notifyDead will be called when
            object that method is bound to dies.
        """
        assert ismethod(method)
        if method.im_self is None:
            raise ValueError, "We need a bound method!"
        if notifyDead is None:
            self.objRef = weakref.ref(method.im_self)
        else:
            self.objRef = weakref.ref(method.im_self, notifyDead)
        self.fun = method.im_func
        self.cls = method.im_class

    def __call__(self):
        if self.objRef() is None:
            return None
        else:
            return instancemethod(self.fun, self.objRef(), self.cls)

    def __eq__(self, method2):
        if not isinstance(method2, _WeakMethod):
            return False
        return      self.fun      is method2.fun \
                and self.objRef() is method2.objRef() \
                and self.objRef() is not None


    def __hash__(self):
        return hash(self.fun)

    def __repr__(self):
        dead = ''
        if self.objRef() is None:
            dead = '; DEAD'
        obj = '<%s at %s%s>' % (self.__class__, id(self), dead)
        return obj

    def refs(self, weakRef):
        """Return true if we are storing same object referred to by weakRef."""
        return self.objRef == weakRef

def _getWeakRef(obj, notifyDead=None):
    """
        Get a weak reference to obj. If obj is a bound method, a _WeakMethod
        object, that behaves like a WeakRef, is returned, if it is
        anything else a WeakRef is returned. If obj is an unbound method,
        a ValueError will be raised.
    """
    if ismethod(obj):
        createRef = _WeakMethod
    else:
        createRef = weakref.ref

    if notifyDead is None:
        return createRef(obj)
    else:
        return createRef(obj, notifyDead)

class Event(object):
    """
        Represents an Event
    """
    def __init__(self, signal, obj, data, time):
        """
            signal: the 'signal' or 'name' for this Event [string]
            obj: the object emitting the Event [object]
            data: some piece of data relevant to the Event [object]
        """
        self.signal = signal
        self.object = obj or _NONE
        self.data = data
        self.time = time
        
class Callback(object):
    """
        Represents a callback
    """
    def __init__(self, function, time, args, kwargs):
        """
            @param function: the function to call
            @param time: the time this callback was added
        """
        self.valid = True
        self.wfunction = _getWeakRef(function, self.vanished)
        self.time = time
        self.args = args
        self.kwargs = kwargs

    def vanished(self, ref):
        self.valid = False
        

class EventManager(Logger):
    """
        Manages all Events
    """
    def __init__(self, use_logger=False, logger_filter=None):
        self.callbacks = {}
        self.use_logger = use_logger
        self.logger_filter = logger_filter

        # RLock is needed so that event callbacks can themselves send
        # synchronous events and add or remove callbacks
        self.lock = threading.RLock()

    def emit(self, signal, data=None, obj=None):
        """
            Emits an Event, calling any registered callbacks.

            event: the Event to emit [Event]
        """
        event = Event(signal, obj, data, time.time())
        
        with self.lock:
            callbacks = set()
            for tcall in set([_NONE, event.signal]):
                for ocall in set([_NONE, event.object]):
                    try:
                        callbacks.update(self.callbacks[tcall][ocall])
                    except KeyError:
                        pass

            # now call them
            for cb in callbacks:
                try:
                    if not cb.valid:
                        try:
                            self.callbacks[event.signal][event.object].remove(cb)
                        except (KeyError, ValueError):
                            pass
                    elif event.time >= cb.time:
                        if self.use_logger and (not self.logger_filter or \
                                re.search(self.logger_filter, event.signal)):
                                self.logdebug("Attempting to call "
                                    "%(function)s in response "
                                    "to %(event)s." % {
                                        'function': cb.wfunction(),
                                        'event': event.signal})

                        cb.wfunction().__call__(event.object, event.data, *cb.args, **cb.kwargs)
                            
                except Exception:
                    # something went wrong inside the function we're calling
                    traceback.print_exc(file=sys.stdout)
                    self.logdebug("Event callback exception caught!")
                    
        if self.use_logger:
            if not self.logger_filter or re.search(self.logger_filter,
                event.signal):
                self.logdebug("Sent '%(signal)s' event from "
                    "'%(object)s' with data '%(data)s'." %
                        {'signal' : event.signal, 'object' : repr(event.object),
                        'data' : repr(event.data)})

    def connect(self, signal, function, obj=None, *args, **kwargs):
        """
            Registers a callback.
            You should always specify at least one of signal or object.

            @param function: The function to call [function]
            @param signal: The 'signal' or 'name' of event to listen for. Defaults
                to any. [string]
            @param obj: The object to listen to events from. Defaults
                to any. [string]
        """
        
        with self.lock:
            # add the specified categories if needed.
            if not self.callbacks.has_key(signal):
                self.callbacks[signal] = weakref.WeakKeyDictionary()
            if obj is None:
                obj = _NONE
            try:
                callbacks = self.callbacks[signal][obj]
            except KeyError:
                callbacks = self.callbacks[signal][obj] = []

            # add the actual callback
            callbacks.append(Callback(function, time.time(), args, kwargs))

        if self.use_logger:
            if not self.logger_filter or re.search(self.logger_filter, signal):
                self.logdebug("Added callback %s for [%s, %s]" %
                        (function, signal, obj))

    def disconnect(self, signal, function, obj=None):
        """
            Unsets a callback

            The parameters must match those given when the callback was
            registered. (minus any additional args)
        """
        if obj is None:
            obj = _NONE
        remove = []

        with self.lock:
            try:
                callbacks = self.callbacks[signal][obj]
                for cb in callbacks:
                    if cb.wfunction() == function:
                        remove.append(cb)
            except KeyError:
                return
            except TypeError:
                return

            for cb in remove:
                callbacks.remove(cb)

        if self.use_logger:
            if not self.logger_filter or re.search(self.logger_filter, signal):
                self.logdebug("Removed callback %s for [%s, %s]" %
                        (function, signal, obj))

                
event_manager = EventManager()                

