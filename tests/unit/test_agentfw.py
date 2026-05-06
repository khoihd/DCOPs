# BSD-3-Clause License
#
# Copyright 2017 Orange
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import threading
import types
import unittest

from pydcop.infrastructure.computations import Message
from pydcop.infrastructure.agents import Agent
from pydcop import infrastructure



class AgentFwTest(unittest.TestCase):

    def test_sendmsg_counts(self):
        comm1 = infrastructure.communication.InProcessCommunicationLayer()
        comm2 = infrastructure.communication.InProcessCommunicationLayer()
        a1 = Agent('a1', comm1)
        a2 = Agent('a2', comm2)

        a1.discovery.register_agent(a1.name, a1.address, publish=False)
        a1.discovery.register_agent(a2.name, a2.address, publish=False)
        a2.discovery.register_agent(a1.name, a1.address, publish=False)
        a2.discovery.register_agent(a2.name, a2.address, publish=False)

        a1.discovery.register_computation('c1', a1.name, a1.address, publish=False)
        a1.discovery.register_computation('c2', a2.name, a2.address, publish=False)
        a2.discovery.register_computation('c1', a1.name, a1.address, publish=False)
        a2.discovery.register_computation('c2', a2.name, a2.address, publish=False)

        self.assertEqual(a1.messages_count('c1'), 0)
        self.assertEqual(comm2.messaging.msg_queue_count, 0)

        msg = Message('pouet')
        a1._messaging.post_msg('c1', 'c2', msg)

        self.assertEqual(a1.messages_count('c1'), 1)
        self.assertEqual(a2.messages_count('c2'), 0)
        self.assertEqual(comm2.messaging.msg_queue_count, 1)

        received, _ = a2._messaging.next_msg()
        self.assertEqual(received.src_comp, 'c1')
        self.assertEqual(received.dest_comp, 'c2')
        self.assertEqual(received.msg, msg)

    def test_sendmsg_two_neighbors(self):
        comm1 = infrastructure.communication.InProcessCommunicationLayer()
        comm2 = infrastructure.communication.InProcessCommunicationLayer()
        comm3 = infrastructure.communication.InProcessCommunicationLayer()
        a1 = Agent('a1', comm1)
        a2 = Agent('a2', comm2)
        a3 = Agent('a3', comm3)

        agents = [a1, a2, a3]
        computations = [('c1', a1), ('c2', a2), ('c3', a3)]
        for agent in agents:
            for known_agent in agents:
                agent.discovery.register_agent(
                    known_agent.name, known_agent.address, publish=False)
            for computation, host in computations:
                agent.discovery.register_computation(
                    computation, host.name, host.address, publish=False)

        # use monkey patching on instance to set the _on_start method on a1
        # simply send a message to all neighbors
        def a1_start(self):
            for n in ['c2', 'c3']:
                self._messaging.post_msg('c1', n, Message('msg'))

        a1._on_start = types.MethodType(a1_start, a1)

        # Monkey patching a2 & a3 to check for message arrival
        a2.received = False
        a3.received = False
        a2.received_event = threading.Event()
        a3.received_event = threading.Event()

        def handle_message(self, sender, dest, msg, t):
            if msg == Message('msg'):
                self.received = True
                self.received_event.set()

        a2._handle_message = types.MethodType(handle_message, a2)
        a3._handle_message = types.MethodType(handle_message, a3)

        # Running the test
        try:
            a2.start()
            a3.start()
            a1.start()

            self.assertTrue(a2.received_event.wait(1))
            self.assertTrue(a3.received_event.wait(1))
            self.assertTrue(a2.received)
            self.assertTrue(a3.received)

            self.assertEqual(a1.messages_count('c1'), 2)
        finally:
            for agent in agents:
                agent.discovery.unregister_agent(agent.name, publish=False)
            for agent in agents:
                agent.stop()
            for agent in agents:
                agent.t.join(1)

    def test_send_received_from(self):
        comm1 = infrastructure.communication.InProcessCommunicationLayer()
        comm2 = infrastructure.communication.InProcessCommunicationLayer()
        a1 = Agent('a1', comm1)
        a2 = Agent('a2', comm2)

        agents = [a1, a2]
        computations = [('a1', a1), ('a2', a2)]
        for agent in agents:
            for known_agent in agents:
                agent.discovery.register_agent(
                    known_agent.name, known_agent.address, publish=False)
            for computation, host in computations:
                agent.discovery.register_computation(
                    computation, host.name, host.address, publish=False)

        # use monkey patching on instance to set the _on_start method on a1
        # simply send a message to a2
        def a1_start(self):
            self._messaging.post_msg('a1', 'a2', Message('msg'))

        a1._on_start = types.MethodType(a1_start, a1)

        # Monkey patching a2 to check for message arrival
        a2.received_from = None
        a2.received_event = threading.Event()

        def handle_message(self, sender, dest, msg, t):
            if msg == Message('msg'):
                self.received_from = sender
                self.received_event.set()

        a2._handle_message = types.MethodType(handle_message, a2)

        # Running the test
        try:
            a2.start()
            a1.start()

            self.assertTrue(a2.received_event.wait(1))
            self.assertEqual(a2.received_from, 'a1')
        finally:
            for agent in agents:
                agent.discovery.unregister_agent(agent.name, publish=False)
            for agent in agents:
                agent.stop()
            for agent in agents:
                agent.t.join(1)
