#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import netsocadmin


class TestNetsocadmin(unittest.TestCase):

    def setUp(self):
        # Use import to make flake8 happy with initial tests.
        dir(netsocadmin)

    def test_something(self):
        pass

    def tearDown(self):
        pass
