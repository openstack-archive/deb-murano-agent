# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import anyjson
import ssl as ssl_module

from eventlet import patcher
kombu = patcher.import_patched('kombu')
from subscription import Subscription


class MqClient(object):
    def __init__(self, login, password, host, port, virtual_host,
                 ssl=False, ca_certs=None):
        ssl_params = None

        if ssl is True:
            ssl_params = {
                'ca_certs': ca_certs,
                'cert_reqs': ssl_module.CERT_REQUIRED
            }

        self._connection = kombu.Connection(
            'amqp://{0}:{1}@{2}:{3}/{4}'.format(
                login,
                password,
                host,
                port,
                virtual_host
            ), ssl=ssl_params
        )
        self._channel = None
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def connect(self):
        self._connection.connect()
        self._channel = self._connection.channel()
        self._connected = True

    def close(self):
        self._connection.close()
        self._connected = False

    def declare(self, queue, exchange='', enable_ha=False, ttl=0):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        queue_arguments = {}
        if enable_ha is True:
            # To use mirrored queues feature in RabbitMQ 2.x
            # we need to declare this policy on the queue itself.
            #
            # Warning: this option has no effect on RabbitMQ 3.X,
            # to enable mirrored queues feature in RabbitMQ 3.X, please
            # configure RabbitMQ.
            queue_arguments['x-ha-policy'] = 'all'
        if ttl > 0:
            queue_arguments['x-expires'] = ttl

        exchange = kombu.Exchange(exchange, type='direct', durable=True)
        queue = kombu.Queue(queue, exchange, queue, durable=True,
                            queue_arguments=queue_arguments)
        bound_queue = queue(self._connection)
        bound_queue.declare()

    def send(self, message, key, exchange=''):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        producer = kombu.Producer(self._connection)
        producer.publish(
            exchange=str(exchange),
            routing_key=str(key),
            body=anyjson.dumps(message.body),
            message_id=str(message.id)
        )

    def open(self, queue, prefetch_count=1):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        return Subscription(self._connection, queue, prefetch_count)
