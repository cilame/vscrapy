"""
Helper functions for serializing (and deserializing) requests.
"""
import six

from scrapy.http import Request
from scrapy.utils.python import to_unicode, to_native_str
from scrapy.utils.misc import load_object


def request_to_dict(request, spider=None):
    """Convert Request object to a dict.

    If a spider is given, it will try to find out the name of the spider method
    used in the callback and store that as the callback.
    """
    cb = request.callback
    if callable(cb):
        cb = _find_method(spider, cb)
    eb = request.errback
    if callable(eb):
        eb = _find_method(spider, eb)
    request._plusmeta.update({'__callerr__':{'callback':cb,'errback':eb}})
    d = {
        'url': to_unicode(request.url),  # urls should be safe (safe_string_url)
        'callback': 'parse',
        'errback': eb,
        'method': request.method,
        'headers': dict(request.headers),
        'body': request.body,
        'cookies': request.cookies,
        'meta': request.meta,
        '_encoding': request._encoding,
        'priority': request.priority,
        'dont_filter': request.dont_filter,
        'flags': request.flags,
        '_plusmeta':request._plusmeta,
    }
    if type(request) is not Request:
        d['_class'] = request.__module__ + '.' + request.__class__.__name__
    return d


def request_from_dict(d, spider=None):
    """Create Request object from a dict.

    If a spider is given, it will try to resolve the callbacks looking at the
    spider for methods with the same name.
    """
    cb = d['callback']
    if cb and spider:
        cb = _get_method(spider, cb)
    eb = d['errback']
    if eb and spider:
        eb = _get_method(spider, eb)
    request_cls = load_object(d['_class']) if '_class' in d else Request
    _cls = request_cls(
        url=to_native_str(d['url']),
        callback=cb,
        errback=eb,
        method=d['method'],
        headers=d['headers'],
        body=d['body'],
        cookies=d['cookies'],
        meta=d['meta'],
        encoding=d['_encoding'],
        priority=d['priority'],
        dont_filter=d['dont_filter'],
        flags=d.get('flags'))
    _cls._plusmeta = d['_plusmeta']
    return _cls


# 被魔改的地方主要就是这里
# 让这个函数跳过原本的对象验证，将 callback，errorback 与 spider 取消绑定的关系
def _find_method(obj, func):
    if obj:
        return func.__name__
    raise ValueError("Function %s is not a method of: %s" % (func, obj))


def _get_method(obj, name):
    name = str(name)
    try:
        return getattr(obj, name)
    except AttributeError:
        raise ValueError("Method %r not found in: %s" % (name, obj))
