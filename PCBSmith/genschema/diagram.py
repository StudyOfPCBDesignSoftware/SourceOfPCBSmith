#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import uuid
import random

from kicad_sym import KicadSymbol, Pin, KicadLibrary

# 元器件
class DiagramSymbol(object):
    def __init__(self, symbol: KicadSymbol):
        self.full_name = '{}:{}'.format(symbol.libname, symbol.name)
        self.name = symbol.name
        self.symbol: KicadSymbol = symbol
        self.pins: List[DiagramPin] = []
        # 位置 (x, y, rotation)
        self.pos = [0, 0, 0]
        self.uuid = uuid.uuid4()
        self.index = symbol.index
        self.opts = {}
        self.gen_pin()
        return

    def get_name(self):
        return self.name

    def gen_pin(self):
        for pin in self.symbol.pins:
            dpin = DiagramPin(self, pin)
            self.pins.append(dpin)
        # self.pins.reverse()
        return

    def calc_pos(self):
        for dpin in self.pins:
            dpin.input_pos(self.pos)
        return

    def get_prop(self, name: str):
        for prop in self.symbol.properties:
            if prop.name == name:
                return prop.value
        return ""


# 引脚
class DiagramPin(object):
    def __init__(self, sym: DiagramSymbol, pin: Pin):
        # 位置 (x, y, rotation)
        self.pos = [pin.posx, pin.posy, pin.rotation]
        self.pin: Pin = pin
        self.sym: DiagramSymbol = sym
        # 链接状态
        self.status: bool = False
        return

    # input/output/passive
    def type(self):
        return self.pin.etype

    def set_status(self, status = True):
        self.status = status
        return

    def input_pos(self, pos):
        self.pos[0] += pos[0]
        self.pos[1] += pos[1]
        self.pos[2] += pos[2]
        return

# 边
class DiagramWire(object):
    def __init__(self, from_: DiagramPin, to_: DiagramPin):
        self.uuid = str(uuid.uuid4())
        self.from_: DiagramPin = from_
        self.to_: DiagramPin = to_
        self.from_.set_status()
        self.to_.set_status()
        return

    def get_pos(self):
        return (self.from_.pos, self.to_.pos)

# 中间结构
class Diagram(object):

    def __init__(self):
        self.symbols = []
        self.wires = []
        return

    def add_symbol(self, symbol: KicadSymbol):
        dsym = DiagramSymbol(symbol)
        self.symbols.append(dsym)
        return dsym

    def add_wire(self, from_: DiagramPin, to_: DiagramPin):
        wire = DiagramWire(from_, to_)
        self.wires.append(wire)
        return wire

    def complete_position(self):
        # 计算图标位置
        num = len(self.symbols)

        # 画圆
        # 当前在这个线的第几个位置
        sym_nd = 0
        turning_point = num / 4 + 1
        line = 0
        ptx, pty = (34, 158)
        step = 10
        for idx, dsym in enumerate(self.symbols):
            if sym_nd >= turning_point:
                sym_nd = 0
                line += 1
            sym_nd += 1
            if idx == 0:
                pass
            elif line == 0:
                pty -= sym_nd * 5
                ptx += sym_nd * 1
            elif line == 1:
                ptx += sym_nd * 5
                pty += sym_nd * 1
            elif line == 2:
                pty += sym_nd * 5
                ptx -= sym_nd * 1
            else:
                ptx -= sym_nd * 5
                pty -= sym_nd * 1
            # print("{}(turn {}) ({},{})".format(
            #     sym_nd, turning_point, ptx, pty
            # ))
            dsym.pos[0] = ptx
            dsym.pos[1] = pty

        for dsym in self.symbols:
            dsym.calc_pos()
        return

if __name__ == '__main__':
    pass