#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper, wraps


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    return func


def decorator(deco):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''

    def wrapped(func):
        return update_wrapper(deco(func), func)

    return update_wrapper(wrapped, deco)

@decorator
def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        res = func(*args, **kwargs)
        return res
    wrapper.calls = 0
    # wrapper.__doc__ = func.__doc__
    return wrapper


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''

    cache = func.cache = {}

    @wraps(func)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache.keys():
            cache[key] = func(*args, **kwargs)

        return cache[key]

    return memoizer


def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''

    def n_ary_func(x, *args):
        return x if not args else func(x, n_ary_func(*args))

    return n_ary_func


def trace(prefix):
    '''Trace calls made to function decorated.

        @trace("____")
        def fib(n):
            ....

        >>> fib(3)
         --> fib(3)
        ____ --> fib(2)
        ________ --> fib(1)
        ________ <-- fib(1) == 1
        ________ --> fib(0)
        ________ <-- fib(0) == 1
        ____ <-- fib(2) == 2
        ____ --> fib(1)
        ____ <-- fib(1) == 1
         <-- fib(3) == 3

    '''

    @decorator
    def real_trace(func):
        def wrapped(*args, **kwargs):
            name = func.__name__
            arg_string = ", ".join([f'{item}' for item in args])
            kwargs_string = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
            if args and kwargs:
                print(f'{prefix} {name}({arg_string}, {kwargs_string})')
            elif args and not kwargs:
                print(f'{prefix} {name}({arg_string})')
            elif not args and kwargs:
                print(f'{prefix} {name}({kwargs_string})')
            elif not args and not kwargs:
                print(f'{prefix} {name}()')
            return func(*args, **kwargs)
        res = wrapped
        return res
    return real_trace


@countcalls
@memo
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    """
    Some doc
    """
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
