# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from collections import namedtuple

CreateStream = namedtuple('CreateStream', 'parent name group header')
GetLogger = namedtuple('GetLogger', '')
GetRequested = namedtuple('GetRequested', '')
MakeFile = namedtuple('MakeFile', 'handle name')

Pull = namedtuple('Pull', 'handle enumerate')
PullAll = namedtuple('PullAll', 'handles')
Push = namedtuple('Push', 'output')
SetHeader = namedtuple('SetHeader', 'header')
