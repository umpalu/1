# -*- coding: utf-8 -*-

import pytest

from requeues import KEEP_QUEUED_ELEMENTS_REMOVE

from tests import redis_conn
from requeues.smartqueue import SmartQueue


ELEMENT_EGG = b'egg'
ELEMENT_BACON = b'bacon'
ELEMENT_SPAM = b'spam'
ELEMENT_42 = b'42'

some_elements = [
    ELEMENT_EGG,
    ELEMENT_BACON,
    ELEMENT_SPAM,
    ELEMENT_SPAM,
    ELEMENT_SPAM,
    ELEMENT_42,
    ELEMENT_SPAM,
]


class TestSmartQueue(object):

    def setup(self):
        self.queue = SmartQueue(
            id_args=['test', 'testing'],
            redis_conn=redis_conn
        )

    def test_empty(self):
        assert self.queue.num() is 0
        assert self.queue.is_empty() is True
        assert self.queue.is_not_empty() is False

    def test_add_to_all(self):
        statuses = self.queue._add_some_to_all(some_elements)
        assert len(statuses) is len(some_elements)

    def test_push(self):
        assert self.queue.push(ELEMENT_EGG) > 0
        assert self.queue.num() is 1
        assert self.queue.is_empty() is False
        assert self.queue.is_not_empty() is True

    def test_push_smart(self):
        assert self.queue.push(ELEMENT_EGG) > 0
        assert self.queue.push(ELEMENT_BACON) > 0
        assert self.queue.push(ELEMENT_SPAM) > 0
        assert self.queue.push(ELEMENT_SPAM) == 0
        assert self.queue.push(ELEMENT_SPAM) == 0
        assert self.queue.push(ELEMENT_42) > 0
        assert self.queue.push(ELEMENT_SPAM) == 0
        assert self.queue.num() is 4

    def test_push_pop(self):
        assert self.queue.push(ELEMENT_EGG) > 0
        assert self.queue.pop(ELEMENT_EGG) == ELEMENT_EGG

    def test_pop_empty_queue(self):
        assert self.queue.pop(ELEMENT_EGG) is None

    def test_push_first_pop_last(self):
        self.queue.push(element=ELEMENT_EGG, queue_first=False)
        self.queue.push(element=ELEMENT_BACON, queue_first=False)
        self.queue.push(element=ELEMENT_SPAM, queue_first=False)
        self.queue.push(element=ELEMENT_42, queue_first=True)

        assert self.queue.elements()[-1] == ELEMENT_SPAM
        assert self.queue.pop(last=True) == ELEMENT_SPAM

    def test_push_pop_last(self):
        self.queue.push(element=ELEMENT_EGG)
        self.queue.push(element=ELEMENT_BACON)
        self.queue.push(element=ELEMENT_SPAM)
        self.queue.push(element=ELEMENT_42)

        assert self.queue.elements()[0] == ELEMENT_EGG
        assert self.queue.pop() == ELEMENT_EGG

    def test_push_some(self):
        assert self.queue.num() is 0
        assert self.queue.push_some(some_elements) == len(set(some_elements))
        assert self.queue.num() is len(set(some_elements))

    def test_push_some_to_beginning(self):
        self.queue.push(element=ELEMENT_42, queue_first=True)
        self.queue.push_some(elements=some_elements, queue_first=True)
        assert self.queue.num() == len(set(some_elements))
        assert self.queue.pop() == ELEMENT_EGG

    def test_elements(self):
        self.queue.push_some(some_elements)
        elements = self.queue.elements()
        assert len(set(some_elements).difference(set(elements))) is 0

    def test_first_elements(self):
        self.queue.push_some(some_elements)
        assert self.queue.first_elements(3) == some_elements[0:3]

    def test_fresh_queue(self):
        self.queue.push(ELEMENT_EGG)
        assert self.queue.is_not_empty() is True

        queue_y = SmartQueue(
            id_args=['test', 'testing'],
            keep_previous=KEEP_QUEUED_ELEMENTS_REMOVE,
            redis_conn=redis_conn
        )
        assert queue_y.is_empty() is True

    def test_delete(self):
        self.queue.push(element=ELEMENT_42)
        assert self.queue.num() == 1
        assert self.queue.delete() is True
        assert self.queue.num() == 0

    def teardown(self):
        self.queue.delete()

if __name__ == '__main__':
    pytest.main()
