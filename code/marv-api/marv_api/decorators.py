# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from inspect import getfullargspec, isgeneratorfunction

from pydantic import Field

from .dag import Inputs, Node, Stream
from .utils import NOTSET, exclusive_setitem, popattr


class InputNameCollision(Exception):
    """An input with the same name already has been declared."""


def input(name, default=NOTSET, foreach=None, type=None):
    """Declare input for a node.

    Plain inputs, that is plain python objects, are directly passed to
    the node. Whereas streams generated by other nodes are requested
    and once the handles of all input streams are available the node
    is instantiated.

    Args:
        name (str): Name of the node function argument the input will
            be passed to.
        default: An optional default value for the input. This can be
            any python object or another node.
        foreach (bool): This parameter is currently not supported and
            only for internal usage.

    Returns:
        The original function decorated with this input
        specification. A function is turned into a node by the
        :func:`node` decorator.

    """
    # NOTE: Foreach is deprecated and does not need a proper exception
    assert default is NOTSET or foreach is None

    if foreach is not None:
        default = foreach

    if type is None and default in (NOTSET, None):
        raise TypeError("'type' is needed if 'default' is None or not set")

    if hasattr(default, '__marv_node__'):
        default = default.__marv_node__
    if isinstance(default, Node):
        default = Stream(node=default)
        if type:
            raise TypeError("'type' is not (yet) supported for input streams")

    field = Field(default)

    def deco(func):
        if foreach:
            # NOTE: Foreach is deprecated and does not need a proper exception
            assert not hasattr(func, '__marv_foreach__'), 'Only one input may declare foreach'
            func.__marv_foreach__ = name

        inputs = func.__dict__.setdefault('__marv_inputs__', {})
        exclusive_setitem(inputs, name, (type, field), InputNameCollision)
        return func
    return deco


def node(schema=None, group=None, version=None):
    """Turn function into node.

    Args:
        schema: capnproto schema describing the output messages format
        group (bool): A boolean indicating whether the default stream
            of the node is a group, meaning it will be used to
            published handles for streams or further groups. In case
            of :paramref:`marv.input.foreach` specifications this flag will
            default to `True`. This parameter is currently only for
            internal usage.
        version (int): This parameter currently has no effect.

    Returns:
        A :class:`Node` instance according to the given
        arguments and :func:`input` decorators.

    """
    if hasattr(schema, 'from_bytes_packed'):  # capnp schema
        # There are two known variations:
        # - marv_nodes/types.capnp:Dataset
        # - marv_api.tests.types_capnp:Test
        schema = schema.schema.node.displayName.replace('.capnp', '_capnp')\
                                               .replace('/', '.')

    def deco(func):
        if hasattr(func, '__marv_node__'):
            raise TypeError('Attempted to convert function into node twice.')

        if not isgeneratorfunction(func):
            raise TypeError(f'{func} needs to be a generator function')

        foreach = popattr(func, '__marv_foreach__', None)
        inputs = popattr(func, '__marv_inputs__', {})

        argspec = getfullargspec(func)
        missing = inputs.keys() ^ argspec.args
        unsupported = {
            x for x in (
                'varargs', 'varkw', 'defaults', 'kwonlyargs', 'kwonlydefaults', 'annotations',
            )
            if getattr(argspec, x)
        }
        if missing:
            raise TypeError(f'Missing input declarations: {missing}')
        if unsupported:
            raise TypeError('Only positional arguments allowed in function signature')

        func.__marv_node__ = Node(function=f'{func.__module__}.{func.__qualname__}',
                                  inputs=Inputs.subclass(func.__module__, **inputs)(),
                                  message_schema=schema,
                                  group=group,
                                  version=version,
                                  foreach=foreach)
        func.clone = func.__marv_node__.clone
        return func
    return deco


# NOTE: Strictly speaking not a decorator but related to decoration of node functions
def select(node, name):  # pylint: disable=redefined-outer-name
    """Select specific stream of a node by name.

    Args:
        node: A node producing a group of streams.
        name (str): Name of stream to select.

    Returns:
        Node outputting selected stream.

    """
    return Stream(node=node.__marv_node__, name=name)


# NOTE: Strictly speaking not a decorator but related to decoration of node functions
def getdag(node):  # pylint: disable=redefined-outer-name
    return node.__marv_node__
