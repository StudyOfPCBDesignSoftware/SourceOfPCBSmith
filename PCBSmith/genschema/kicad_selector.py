#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import copy
from kicad_sym import KicadSymbol, KicadLibrary, KicadFileFormatError

# 这里全都是选择相关基础的逻辑，不涉及选择算法
# 所有策略都在strategy相关类中
class KicadSelector(object):

    def __init__(self):
        self.libs = []
        self.repeated = {}
        return


    def import_library(self, filepath: str):
        try:
            library = KicadLibrary.from_file(filepath)
        except KicadFileFormatError as e:
            self.printer.red("Could not parse library: %s. (%s)" % (filepath, e))
            traceback.print_exc()

        self.libs.append(library)
        return

    def select_name(self, lib: KicadLibrary, name: str):
        # 在获取到的符号库中选择指定的元器件
        for symbol in lib.symbols:
            # 循环符号库，选择指定元器件
            if symbol.name == name:
                return symbol
        return False

    def mapping_name(self, name: str):
        mapping = {
            "R": "R",
            "R_Variable": "R",
            "R_Photo": "R",
            "R_Trim": "R",
            "R_US": "R",
            "CAP": "C",
            "C_Variable": "C",
            "C_Polarized": "C",
            "C_Polarized_US": "C",
            "INDUCTOR": "L",
            "L_Ferrite": "L",
            "L_Iron": "L",
            "L_Iron_Small": "L",
            "L_Small": "L",
            "L_Trim": "L",
            "VSOURCE": "?",
            "ISOURCE": "?",
            "DIODE": "D",
            "LED": "D",
            "D_Schottky": "D",
            "D_Zener": "D",
            "1N4001": "D",
            "D": "D",
            "D_Filled": "D",
            "D_Small": "D",
            "LED_Filled": "D",
            "D_Zener_Filled": "D",
            "D_Zener_Small": "D",
            "Q_NPN_BCE": "Q",
            "Q_PJFET_DGS": "Q",
            "Q_PMOS_DGS": "Q",
            "Q_NIGBT_CEG": "Q",
            "PN2222A": "Q",
            "SW_Push": "S"
        }
        if name in mapping:
            return mapping[name]
        else:
            return name

    def rename_symbol(self, sym: KicadSymbol):
        index = 1
        name = self.mapping_name(sym.name)
        if name in self.repeated:
            index = self.repeated[name]
        self.repeated[name] = index + 1
        newsym = copy.deepcopy(sym)
        newsym.properties[0].value += str(index)
        newsym.index = index
        return newsym


    # 对外部接口
    def select(self, name: str, rename: bool = True):
        for lib in self.libs:
            sym = self.select_name(lib, name)
            if sym:
                if rename:
                    sym = self.rename_symbol(sym)
                return sym
        return None


if __name__ == '__main__':
    selector = KicadSelector()
    selector.import_library("kicad_sym/pspice.kicad_sym")
    selector.import_library("kicad_sym/Switch.kicad_sym")
    selector.import_library("kicad_sym/Device.kicad_sym")
    selector.import_library("kicad_sym/Diode.kicad_sym")
    #print(selector.select(name="VSOURCE"))
    #print(selector.select(name="VSOURCE"))
