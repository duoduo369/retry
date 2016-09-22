retry
---
[![Build
Status](https://travis-ci.org/duoduo369/retry.svg?branch=master)](https://travis-ci.org/duoduo369/retry)

retry是为了做方法重试的一个东西。

其他有的retry是直接给一个方法写一个装饰器，让整个方法来做retry， 这里提供一个更小粒度的retry方法，你可以在任何你想retry的地方添加自己的逻辑，无论失败与否。

useage:
```
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
```
