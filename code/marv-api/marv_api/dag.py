# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-few-public-methods,invalid-name,no-self-argument,no-self-use

from typing import Optional, Union

from pydantic import BaseModel, Extra, create_model, validator


class Model(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_mutation = False

    def __hash__(self):
        dct = self.__dict__
        # Objects of same class with same values for fields have same hash
        return hash((self.__class__,) + tuple(
            tuple(v) if isinstance(v, list) else v
            for v in (dct[x] for x in self.__fields__)
        ))


class Inputs(Model):
    """Base class for node input configuration models.

    The fields of its subclasses describe the input parameters to be
    passed to a node function.
    """

    @classmethod
    def subclass(cls, __module__, **kw):
        return create_model('Inputs', __base__=Inputs, __module__=__module__, **kw)

    @validator('*', pre=True)
    def streamify(cls, value):
        """Turn Node inputs into streams."""
        if hasattr(value, '__marv_node__'):
            return Stream(node=value.__marv_node__)
        return value


class Node(Model):  # pylint: disable=too-few-public-methods
    function: str
    inputs: Optional[Inputs]
    message_schema: Optional[str]
    group: Union[bool, str, None]
    version: Optional[int]
    foreach: Optional[str]

    @validator('function')
    def function_needs_to_be_dotted_path(cls, value):
        if '.' not in value:
            raise ValueError(f'Expected dotted path to function, not: {value!r}')
        return value

    def clone(self, **kw):
        # Send inputs through validation
        inputs = self.inputs.dict(exclude_unset=True, exclude_defaults=True)
        inputs.update(kw)
        return self.copy(update={'inputs': type(self.inputs).parse_obj(inputs)})


class Stream(Model):
    node: Node
    name: Optional[str]
