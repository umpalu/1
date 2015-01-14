# -*- coding: utf-8 -*-

from requeues import QUEUE_COLLECTION_OF_ELEMENTS
from requeues import KEEP_QUEUED_ITEMS_KEEP, KEEP_QUEUED_ITEMS_REMOVE

from requeues import Tools
from requeues.exceptions import RequeuesError


class SimpleQueue(object):
    '''
    A lightweight queue. Simple Queue.
    '''

    QUEUE_TYPE_NAME = 'simple'

    def __init__(self, id_args=[],
                 collection_of=QUEUE_COLLECTION_OF_ELEMENTS,
                 keep_previous=KEEP_QUEUED_ITEMS_KEEP,
                 redis_conn=None):
        '''
        Create a SimpleQueue object.

        Arguments:
        :id_args -- list, list's values will be used to name the queue
        :collection_of -- string (default: QUEUE_COLLECTION_OF_ELEMENTS),
                          a type descriptor of queued elements
        :keep_previous -- boolean (default: KEEP_QUEUED_ITEMS_KEEP),
                          a flag to create a fresh queue or not
        :redis_conn -- redis.client.Redis (default: None), a redis
                       connection will be created using the default
                       redis.client.Redis connection params.
        '''
        self.id_args = id_args
        self.collection_of = collection_of

        if redis_conn is None:
            redis_conn = redis.Redis()
        self.redis = redis_conn

        self.key = self.get_key()

        if keep_previous is KEEP_QUEUED_ITEMS_REMOVE:
            self.delete(self.keys)

    def __str__(self):
        '''
        Return a string representation of the class.

        Returns: string
        '''
        return '<SimpleQueue: %s (%s)>' % (self.key, self.num())

    def get_key(self):
        '''
        Get a key id that will be used to store/retrieve data from
        the redis server.

        Returns: string
        '''
        return 'queue:%s:type:%s:of:%s' % ('.'.join(self.id_args),
            SimpleQueue.QUEUE_TYPE_NAME, self.collection_of)

    def push(self, element, queue_first=False):
        '''
        Push a element into the queue. Element can be pushed to the first or
        last position (by default is pushed to the last position).

        Arguments:
        :element -- string
        :queue_first -- boolean (default: False)

        Raise:
        :RequeuesError(), if element can not be pushed

        Returns: long, the number of queued elements
        '''
        try:

            element = element.strip()

            if queue_first:
                return self.redis.lpush(self.key, element)
            return self.redis.rpush(self.key, element)

        except Exception as e:
            raise RequeuesError(e.message)

    def push_some(self, elements, queue_first=False, num_block_size=None):
        '''
        Push a bunch of elements into the queue. Elements can be pushed to the
        first or last position (by default are pushed to the last position).

        Arguments:
        :elements -- iterable
        :queue_first -- boolean (default: false)
        :num_block_size -- integer (default: none)

        Raise:
        :RequeuesError(), if element can not be pushed

        Returns: long, the number of queued elements
        '''
        try:

            elements = list(elements)

            if queue_first:
                elements.reverse()

            block_slices = Tools.get_block_slices(
                num_elements=len(elements),
                num_block_size=num_block_size
            )

            pipe = self.redis.pipeline()
            for s in block_slices:
                some_elements = elements[s[0]:s[1]]
                if queue_first:
                    pipe.lpush(self.key, *some_elements)
                else:
                    pipe.rpush(self.key, *some_elements)
            return pipe.execute().pop()

        except Exception as e:
            raise RequeuesError(e.message)

    def pop(self, last=False):
        '''
        Pop a element from the queue. Element can be popped from the begining
        or the ending of the queue (by default pops from the begining).

        If no element is poped, it returns None

        Arguments:
        :last -- boolean (default: false)

        Returns: string, the popped element, or, none, if no element is popped
        '''
        if last:
            return self.redis.rpop(self.key)
        return self.redis.lpop(self.key)

    def num(self):
        '''
        Get the number of elements that are queued.

        Returns: integer, the number of elements that are queued
        '''
        return self.redis.llen(self.key)

    def is_empty(self):
        '''
        Check if the queue is empty.

        Returns: boolean, true if queue is empty, otherwise false
        '''
        return True if self.num() is 0 else False

    def is_not_empty(self):
        '''
        Check if the queue is not empty.

        Returns: boolean, true if queue is not empty, otherwise false
        '''
        return not self.is_empty()

    def elements(self, queue_from=0, queue_to=-1):
        '''
        Get some (or even all) queued elements, by the order that they are
        queued. By default it returns all queued elements.

        Note
        ====
        Elements are not popped.

        Arguments:
        :queue_from -- integer (default: 0)
        :queue_to -- integer (default: -1)

        Returns: list
        '''
        return self.redis.lrange(self.key, queue_from, queue_to)

    def first_elements(self, num_elements=10):
        '''
        Get the N first queued elements, by the order that they are
        queued. By default it returns the first ten elements.

        Note
        ====
        Elements are not popped.

        Arguments:
        :num_elements -- integer (default: 10)

        Returns: list
        '''
        queue_to = num_elements - 1
        return self.elements(queue_to=queue_to)

    def delete(self):
        '''
        Delete the queue with all its elements.

        Returns: boolean, true if queue has been deleted, otherwise false
        '''
        if self.redis.delete(self.key) is 1:
            return True
        return False