#!/usr/bin/env assertpython
# coding=utf-8

from collections import defaultdict, namedtuple

Arguments = namedtuple('Arguments', ['args', 'kwargs'])


class FunctionCallRecord(object):
    '''
    记录方法调用的参数，方便做一些重试

    场景:
        当写一些for循环调用的时候，面临里面某一步失败的情况，
        失败后希望可以做一些retry
    '''

    def __init__(self):
        '''
        _data = {
            'op_name': {
                'func': func,
                'args': [Arguments1, Arguments2],
            }
        }
        '''
        self._data = defaultdict(lambda: {'func': None, 'args': []})

    def recording(self, op_name, func, args=None, kwargs=None):
        '''
        func必传
        同一个op_name下的func应该是相同的，不相同请用另一个op_name
        '''
        data = self._data[op_name]
        if not func:
            return
        if data['func'] and data['func'] != func:
            return
        data['func'] = func
        if not args:
            args = []
        if not kwargs:
            kwargs = {}
        data['args'].append(Arguments(args=args, kwargs=kwargs))

    def _get_retry_op_name(self, op_name, retry_time=1):
        assert retry_time >= 1
        if retry_time is 1:
            return op_name
        return '__{}__{}'.format(op_name, retry_time)

    def retry(self, op_name, handle_exception=None, retry_times=1):
        if retry_times < 1:
            return
        for retry_time in xrange(retry_times):
            self._retry(op_name, handle_exception, retry_time+1)

    def _retry(self, op_name, handle_exception, retry_time):
        '''
        retry_time为1时取得是op_name里面记录的东西
        retry_time大于1为n时，例如二,取得是__op_name__n里面的东西
        '''
        real_op_name = self._get_retry_op_name(op_name, retry_time)
        if op_name not in self._data or real_op_name not in self._data:
            return
        data = self._data[real_op_name]
        func = data['func']
        if not func:
            return
        for arguments in data['args']:
            try:
                func(*arguments.args, **arguments.kwargs)
            except Exception as exc:
                next_retry_op_name = self._get_retry_op_name(op_name, retry_time+1)
                self.recording(next_retry_op_name, func, arguments.args, arguments.kwargs)
                if not handle_exception:
                    raise exc
                handle_exception(exc)
