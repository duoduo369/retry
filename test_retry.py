#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
retry是为了做方法重试的一个东西
useage:
    from retry import FunctionCallRecord

    func_record = FunctionCallRecord()

    for i in xrange(times):
        try:
            your_func_call(arg1, kwarg1='kwarg1_xxx')
        except:
            func_record.recording('special_op_name', your_func_call, [arg1], {'kwarg1':'kwarg1_xxx'})
            some_exception_handle()

    def handle_exception(exc):
        if isinstance(exc, SomeException):
            some_exception_handle()
        ...
    func_record.retry('special_op_name', handle_exception, retry_times=5)
'''
import unittest

from retry import FunctionCallRecord


class FunctionCallRecordTest(unittest.TestCase):

    def setUp(self):
        self.func_record = FunctionCallRecord()
        self.raise_exception = True

    def no_args_func(self):
        return 'no args func'

    def args_func(self, arg1, arg2):
        return (arg1, arg2)

    def kwargs_func(self, kwarg1=1, kwarg2=2):
        return {kwarg1: kwarg1, kwarg2: kwarg2}

    def args_and_kwargs_fun(self, arg1, arg2, kwarg1, kwarg2):
        return [(arg1, arg2), {kwarg1: kwarg1, kwarg2: kwarg2}]

    def raise_exception_fun(self, time, raise_exception=False):
        if self.raise_exception and raise_exception:
            raise Exception(str(time))

    def assertEqualArgument(self, argument, args, kwargs):
        self.assertEqual(argument.args, args)
        self.assertEqual(argument.kwargs, kwargs)

    def test_no_args_func(self):
        op_name = 'test_no_args_func'
        self.func_record.recording(op_name, self.no_args_func)
        self.func_record.retry(op_name)
        self.assertIn(op_name, self.func_record._data)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), 1)
        self.assertEqualArgument(arguments[0], [], {})

    def test_args_fun(self):
        op_name = 'test_args_fun'
        args = [1, 2]
        self.func_record.recording(op_name, self.args_func, args=args)
        self.func_record.retry(op_name)
        self.assertIn(op_name, self.func_record._data)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), 1)
        self.assertEqualArgument(arguments[0], args, {})

    def test_kwargs_func(self):
        op_name = 'test_kwargs_func'
        kwargs = {'kwarg1': 1, 'kwarg2': 2}
        self.func_record.recording(op_name, self.kwargs_func, kwargs=kwargs)
        self.func_record.retry(op_name)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), 1)
        self.assertEqualArgument(arguments[0], [], kwargs)

    def test_args_and_kwargs_fun_func(self):
        op_name = 'test_args_and_kwargs_fun'
        args = [1, 2]
        kwargs = {'kwarg1': 1, 'kwarg2': 2}
        self.func_record.recording(op_name, self.args_and_kwargs_fun, args=args, kwargs=kwargs)
        self.func_record.retry(op_name)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), 1)
        self.assertEqualArgument(arguments[0], args, kwargs)

    def test_multiple_recording(self):
        op_name = 'test_multiple_recording'
        args = [1, 2]
        kwargs = {'kwarg1': 1, 'kwarg2': 2}
        times = 10
        for i in xrange(times):
            self.func_record.recording(op_name, self.args_and_kwargs_fun, args=args, kwargs=kwargs)
        self.assertEqual(len(self.func_record._data), 1)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), times)
        for i in xrange(times):
            self.assertEqualArgument(arguments[i], args, kwargs)
        self.func_record.retry(op_name)
        self.assertEqual(len(self.func_record._data), 1)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), times)
        for i in xrange(times):
            self.assertEqualArgument(arguments[i], args, kwargs)

    def test_multiple_exception_without_handle_exception(self):
        op_name = 'test_multiple_exception'
        kwargs = {'raise_exception': True}
        times = 10
        for i in xrange(times):
            self.func_record.recording(op_name, self.raise_exception_fun, args=[i], kwargs=kwargs)
        # 不传handle_exception, 则遇到异常调用时依然会break
        with self.assertRaises(Exception) as cm:
            self.func_record.retry(op_name)
        ex = cm.exception
        self.assertEqual(str(ex), '0')

    def test_multiple_exception_with_handle_exception(self):
        op_name = 'test_multiple_exception'
        kwargs = {'raise_exception': True}
        times = 10
        for i in xrange(times):
            self.func_record.recording(op_name, self.raise_exception_fun, args=[i], kwargs=kwargs)

        # 传handle_exception, 则会处理
        def handle_exception(exc):
            if isinstance(exc, Exception):
                print exc
        retry_times = 5
        self.func_record.retry(op_name, handle_exception=handle_exception, retry_times=retry_times)
        # 因为func依然会抛异常
        self.assertEqual(len(self.func_record._data), retry_times + 1)
        for i in xrange(retry_times):
            next_retry_op_name = self.func_record._get_retry_op_name(op_name, i + 2)
            self.assertIn(next_retry_op_name, self.func_record._data)
        for op_name, data in self.func_record._data.iteritems():
            arguments = data['args']
            self.assertEqual(len(arguments), times)

    def test_multiple_exception_with_handle_exception2(self):
        '''这个会关闭测试方法的抛异常逻辑'''
        op_name = 'test_multiple_exception'
        kwargs = {'raise_exception': True}
        times = 10
        for i in xrange(times):
            self.func_record.recording(op_name, self.raise_exception_fun, args=[i], kwargs=kwargs)

        # 传handle_exception, 则会处理
        def handle_exception(exc):
            if isinstance(exc, Exception):
                print exc
        self.raise_exception = False
        self.func_record.retry(op_name, handle_exception=handle_exception, retry_times=5)
        # 因为func不会抛异常, 所以在retry_time为1的时候就完成了所有的重试
        self.assertEqual(len(self.func_record._data), 1)
        self.assertIn(op_name, self.func_record._data)
        next_retry_op_name = self.func_record._get_retry_op_name(op_name, 2)
        self.assertNotIn(next_retry_op_name, self.func_record._data)
        arguments = self.func_record._data[op_name]['args']
        self.assertEqual(len(arguments), times)
