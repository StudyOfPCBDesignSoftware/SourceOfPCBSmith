#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import re
import numpy as np
import time

from diagram import *
from kicad_selector import KicadSelector
from kicad_writer import KicadWriter

class LoopGenerator(object):

    def __init__(self, selector):
        self.dia: Diagram = Diagram()
        self.selector: KicadSelector = selector
        return

    # 轮盘赌选择
    def roulette(self, probability):
        probabilityTotal = np.zeros(len(probability))
        probabilityTmp = 0
        for i in range(len(probability)):
            probabilityTmp += probability[i]
            probabilityTotal[i] = probabilityTmp
        randomNumber = np.random.rand()
        result = 0
        for i in range(1, len(probabilityTotal)):
            if randomNumber < probabilityTotal[0]:
                result = 0
                break
            elif probabilityTotal[i - 1] < randomNumber <= probabilityTotal[i]:
                result = i
        return result

    def gen(self, ComponentNumber):
        # source
        # choice = random.choice(["VSOURCE", "ISOURCE"])
        choice = random.choice(["VSOURCE"])
        sym = self.selector.select(choice)
        self.dia.add_symbol(sym)

        # 读取配置文件
        conf = []
        file = open("conf.txt", "r")
        for line in file:
            s = line.replace("\n", "")
            s = re.split(r" +", s)
            conf.append(s)
        file.close()

        # 处理配置文件-分类
        category_probability = {'R': 0.48, 'L': 0.03, 'C': 0.26, 'D': 0.16, 'Q': 0.07}
        category = list(category_probability.keys())
        probability = []
        for key, value in category_probability.items():
            probability.append(value)

        #need = component_num
        need = ComponentNumber
        # chosen_component = []

        for idx in range(need):
            # 元器件种类轮盘赌选择
            selectCate = self.roulette(probability)
            selected_category = category[selectCate]

            # 种类内的元器件进行轮盘赌选择
            candidates_num = []
            candidates_name = []
            for i in range(len(conf)):
                if conf[i][1] == selected_category:
                    candidates_num.append(conf[i][2])
                    candidates_name.append(conf[i][0])

            weight_sum = 0
            for i in range(len(candidates_num)):
                weight_sum += float(candidates_num[i])

            weight_true = random.random() * weight_sum

            weight_sum = 0
            found = 0
            for i in range(len(candidates_num)):
                weight_sum += float(candidates_num[i])
                if weight_sum >= weight_true:
                    selected = candidates_name[i]
                    found = 1
                    break
            if found == 0:
                selected = candidates_name[0]

            sym = selector.select(selected)
            if sym:
                self.dia.add_symbol(sym)
            pass


        # NOTE: 对于三引脚的全部接地
        ground = self.selector.select("0")
        assert ground is not None
        dground = self.dia.add_symbol(ground)
        assert len(dground.pins) > 0
        for dsym in self.dia.symbols:
            if len(dsym.pins) < 3:
                continue
            # 找没链接的引脚
            if dsym.name == "Q_NPN_BCE":
                for dpin in dsym.pins:
                    if dpin.pin.number == "2":
                        print(dpin.pin.number)
                        self.dia.add_wire(dpin, dground.pins[0])
            if dsym.name == "Q_PJFET_DGS" or dsym.name == "Q_PMOS_DGS":
                for dpin in dsym.pins:
                    if dpin.pin.number == "1":
                        print(dpin.pin.number)
                        self.dia.add_wire(dpin, dground.pins[0])
            if dsym.name == "PN2222A":
                for dpin in dsym.pins:
                    if dpin.pin.number == "3":
                        print(dpin.pin.number)
                        self.dia.add_wire(dpin, dground.pins[0])
            if dsym.name == "Q_NIGBT_CEG":
                # print(dsym.name)
                for dpin in dsym.pins:
                    if dpin.pin.number == "2":
                        print(dpin.pin.number)
                        self.dia.add_wire(dpin, dground.pins[0])

        # 添加线
        self.connect()

        # self.dia.add_wire(dsource.pins[0], dground.pins[0])
        for dsym in self.dia.symbols:
            if str(dsym.name).endswith("D"):
                self.dia.add_wire(dsym.pins[0], dground.pins[0])

        self.dia.complete_position()

        return self.dia


    def find_unuse_pin(self, dsym: DiagramPin, out:bool = False):
        # 先找input的
        print("Symbol in find_unuse pin =",dsym.name)
        if not out:
            for pin in dsym.pins:
                if not pin.status and pin.pin.etype == "input":
                    #pin.status = True
                    return pin
        else:
            for pin in dsym.pins:
                if not pin.status and pin.pin.etype == "output":
                    return pin
        for pin in dsym.pins:
            if not pin.status:
                return pin
        return None


    def connect(self):
        head_dsym = None
        prev_dsym = None
        for dsym in self.dia.symbols:
            print(dsym.name)
            if dsym.name == '0': #不处理接地元器件
                continue
            if not prev_dsym:
                head_dsym = prev_dsym = dsym
                continue
            print("prev_dsym=",prev_dsym.name)
            print("dsym=",dsym.name)
            from_pin = self.find_unuse_pin(prev_dsym, True)
            print("from_pin=",from_pin.pin.number)
            to_pin = self.find_unuse_pin(dsym, False)
            print("to_pin=",to_pin.pin.number)
            if not from_pin or not to_pin:
                raise "invalid use symbols(check select phase)"
            self.dia.add_wire(from_pin, to_pin)
            prev_dsym = dsym
        # 最后连城环 (prev -> head)
        from_pin = self.find_unuse_pin(prev_dsym, True)
        to_pin = self.find_unuse_pin(head_dsym, False)
        if not from_pin or not to_pin:
            raise "invalid use symbols(check select phase)"
        self.dia.add_wire(from_pin, to_pin)
        return


if __name__ == '__main__':

    folder_path = "./gendir/"
    generator_num = 100

    for i in range(generator_num):
        selector = KicadSelector()
        selector.import_library("kicad_sym/pspice.kicad_sym")
        selector.import_library("kicad_sym/Switch.kicad_sym")
        selector.import_library("kicad_sym/Device.kicad_sym")
        selector.import_library("kicad_sym/Diode.kicad_sym")
        selector.import_library("kicad_sym/Transistor_BJT.kicad_sym")
        print(f"Start generating {i}.kicad_sch!")
        ComponentNumber = random.randint(10,100)
        dia = LoopGenerator(selector).gen(ComponentNumber)
        KicadWriter(folder_path+str(i)+".kicad_sch").write(dia)
        print(f"{i}.kicad_sch generated sucessfully!")


