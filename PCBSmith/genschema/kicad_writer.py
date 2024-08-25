#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path
import os
import traceback
import uuid
import random

import sexpr
from diagram import Diagram, DiagramSymbol, DiagramWire

class KicadWriter(object):

    def __init__(self, filename: str):
        self.filename = filename
        return

    def write(self, dia: Diagram):
        with open(self.filename, "w") as f:
            sch = self.gen(dia)
            content = sexpr.format_sexp(
                sexpr.build_sexp(sch),
                max_nesting=4
            )
            f.write(content)
        return

    def gen(self, dia: Diagram):
        sch = [
            "kicad_sch",
            ["version", "20211123"],
        ]
        sch.append(["generator", "eeschema"])
        uid = uuid.uuid4()
        muuid = ["uuid", uid]
        sch.append(muuid)
        sch.append(["paper", "\"A4\""])

        # 将符号库写入电路图文件
        sx = [
            "lib_symbols",
        ]
        for dsym in dia.symbols:
            sx.append(self.get_symbol_sexpr(dsym))
        sch.append(sx)

        # 对元器件进行连线
        for wire in dia.wires:
            ws = self.get_wire_sexpr(wire)
            sch.append(ws)

        # 添加仿真命令，比如瞬态、AC等
        sch.append(self.get_spice_order())

        # 添加ngspice仿真参数
        sch.append(self.get_option_order())

        for dsym in dia.symbols:
            if dsym.name == "SW_Push":
                sch.append(self.add_sw_model(dsym))

        # 添加接地引脚

        # sheet
        sheet = [
            "sheet_instances",
            ["path \"/\"",
            ["page", "\"1\""]
            ],
        ]
        sch.append(sheet)

        # 生成元器件实例
        for dsym in dia.symbols:
            ds = self.get_instance_sexpr(dsym)
            sch.append(ds)

        # 写符号实例（电路图文件结尾）
        symbolinstance = [
            "symbol_instances",
        ]
        for dsym in dia.symbols:
            symbolins = []
            symbolins.append('path "/{}"'.format(dsym.uuid))
            symbolins.append([
                "reference",
                '"{}"'.format(dsym.get_prop("Reference"))
                ])
            symbolins.append(["unit", "1"])
            symbolins.append([
                "value",
                '"{}"'.format(dsym.get_prop("Value"))
                ])
            symbolins.append([
                "footprint",
                '"{}"'.format(dsym.get_prop("Footprint"))
            ])
            symbolinstance.append(symbolins)
        sch.append(symbolinstance)
        return sch


    def get_spice_order(self):
        ## 目前我们只设计一种仿真命令
        spiceOrder = [
            "text",
        ]
        ## 以后可以在其中进行随机选择想要仿真的形式，以及电气值
        spiceOrderStr1 = (".TRAN 0.1ns 100ns")
        spiceOrderStr2 = (".DC V1 0 5 0.2")
        spice_commands = [".TRAN 0.1ns 100ns", ".DC V1 0 5 0.2"]
        spiceOrderStr = random.choice(spice_commands)
        spiceOrder.append("\"" + spiceOrderStr + "\"")
        TextPosition = "170 115 0"  # 文本的位置，以后看情况在确定是否需要改动
        spiceOrder.append(["at", TextPosition])
        spiceOrder.append(["effects",
                        ["font",
                            ["size 1.27 1.27"]],
                        ["justify left bottom"],
                        ])

        UUID = uuid.uuid4()
        spiceOrder.append(["uuid", UUID])
        return spiceOrder

    def get_option_order(self):
        ## 目前我们只设计一种仿真命令
        optionOrder = [
            "text",
        ]
        ## 以后可以在其中进行随机选择想要仿真的形式，以及电气值
        optionOrderStr = ".options rshunt=1G chgtol=1e-12"
        # optionOrderStr = ".OPTIONS METHOD=TRAP RELTOL=0.01 TMAX=0.1m"
        optionOrder.append("\"" + optionOrderStr + "\"")
        TextPosition = "150 125 0"  # 文本的位置，以后看情况在确定是否需要改动
        optionOrder.append(["at", TextPosition])
        optionOrder.append(["effects",
                           ["font",
                            ["size 1.27 1.27"]],
                           ["justify left bottom"],
                           ])

        UUID = uuid.uuid4()
        optionOrder.append(["uuid", UUID])
        return optionOrder

    def add_sw_model(self, dsym: DiagramSymbol):
        assert dsym.name == "SW_Push"
        # 临时添加开关的spice模型
        spiceOrdernew = ["text"]
        vt = 10
        if "vt" in dsym.opts:
            vt = dsym.opts["vt"]
        spiceOrderStrnew = ".model sw_push{} sw(vt={} vh=0.2 ron=1 roff=10k)".format(
            # 开关名称
            dsym.index,
            # dsym.symbol.properties[0].value,
            # vt 电压值
            vt
        )
        spiceOrdernew.append("\"" + spiceOrderStrnew + "\"")
        TextPositionnew = "67.31 38.1 0"
        # 文本的位置，以后看情况在确定是否需要改动
        spiceOrdernew.append(["at", TextPositionnew])
        spiceOrdernew.append(["effects",
                        ["font",
                            ["size 1.27 1.27"]],
                        ["justify left bottom"],
                        ])
        UUIDnew = uuid.uuid4()
        spiceOrdernew.append(["uuid", UUIDnew])
        return spiceOrdernew


    def get_symbol_sexpr(self, dsym: DiagramSymbol):
        symbol = dsym.symbol
        # add header
        full_name = symbol.quoted_string("{}".format(
            symbol.libname + ":" + symbol.name
        ))
        sx = ["symbol", full_name]
        if symbol.extends:
            sx.append(["extends", symbol.quoted_string(symbol.extends)])

        pn = ["pin_names"]
        if symbol.pin_names_offset != 0.508:
            pn.append(["offset", symbol.pin_names_offset])
        if symbol.hide_pin_names:
            pn.append("hide")
        if len(pn) > 1:
            sx.append(pn)

        sx.append(["in_bom", "yes" if symbol.in_bom else "no"])
        sx.append(["on_board", "yes" if symbol.on_board else "no"])
        if symbol.is_power:
            sx.append(["power"])
        if symbol.hide_pin_numbers:
            sx.append(["pin_numbers", "hide"])

        # add properties
        for prop in symbol.properties:
            sx.append(prop.get_sexpr())

        # add units
        for d in range(0, symbol.demorgan_count + 1):
            for u in range(0, symbol.unit_count + 1):
                hdr = symbol.quoted_string("{}_{}_{}".format(symbol.name, u, d))
                sx_i = ["symbol", hdr]
                for pin in (
                        symbol.arcs
                        + symbol.circles
                        + symbol.texts
                        + symbol.rectangles
                        + symbol.polylines
                        + symbol.pins
                ):
                    if pin.is_unit(u, d):
                        sx_i.append(pin.get_sexpr())

                if len(sx_i) > 2:
                    sx.append(sx_i)
        return sx



    def get_wire_sexpr(self, wire: DiagramWire):
        ssx = [
            "wire",
        ]
        temp = [
            "pts",
            # ["xy", str(PIN[0][0]) + " " + str(PIN[0][1])],
            # ["xy", str(PIN[1][0]) + " " + str(PIN[1][1])],
            ["xy", wire.from_.pos[0], wire.from_.pos[1]],
            ["xy", wire.to_.pos[0], wire.to_.pos[1]],
        ]
        ssx.append(temp)
        stk = [
            "stroke",
            ["width", "0"],
            ["type", "default"],
            ["color", "0 0 0 0"],
        ]
        ssx.append(stk)
        ssx.append(["uuid", str(uuid.uuid4())])
        return ssx

    def get_property_sexpr(self, prop, sympos, effects: bool = False):
        sx = ["property",
              prop.quoted_string(prop.name),
              prop.quoted_string(prop.value),
              ["id", prop.idd],
              ["at",
               prop.posx + sympos[0],
               prop.posy + sympos[1],
               prop.rotation + sympos[2]],
              ]
        # Footprint和Datasheet需要effects
        if effects:
            sx.append(prop.effects.get_sexpr())
        return sx

    def get_instance_sexpr(self, dsym: DiagramSymbol):
        symbol: DiagramSymbol = dsym.symbol
        full_name = symbol.quoted_string(
            "{}:{}".format(symbol.libname, symbol.name)
        )
        sx = ["symbol", ["lib_id", full_name]]
        sx.append(["at", *dsym.pos])
        sx.append(["unit", 1])

        sx.append(["in_bom", "yes" if symbol.in_bom else "no"])
        sx.append(["on_board", "yes" if symbol.on_board else "no"])
        sx.append(["fields_autoplaced"])
        # 给元器件唯一标识
        sx.append(["uuid", dsym.uuid])

        # properties
        for prop in symbol.properties:
            effect = False
            if prop.name == "Footprint" and prop.name == "Footprint":
                effect = True
            if prop.name == "Reference" or prop.name == "Value" or prop.name == "Footprint" or prop.name == "Datasheet":
                sx.append(self.get_property_sexpr(prop, dsym.pos, effect))

        ## 如果元器件不是接地，则需要添加相关仿真属性
        if symbol.name != "0":
            addSpiceProperty(sx, dsym)

        # add pins 并添加uuid
        for pin in symbol.pins:
            pinuuid = uuid.uuid4()
            ssx = ["pin", '"{}"'.format(pin.number),
                    ["uuid", pinuuid],
                   ]
            sx.append(ssx)

        return sx

def addSpiceProperty(sx, dsym: DiagramSymbol):
    symbol = dsym.symbol
    SymbolPosition = dsym.pos
    # 给元器件添加仿真用的参数“Spice_primitive”\"Spice_Model"\"Spice_Netlist_Enabled"
    ## 添加“Spice_primitive”
    print("spice_primitive=", symbol.properties[0].value[0])
    if symbol.name == "Q_PMOS_DGS" or symbol.name == "Q_PJFET_DGS" or symbol.name == "Q_NIGBT_CEG":
    ## 目前除了GND的reference的值是“#GND‘,其它元器件的Reference的值与spice_Pcirmitive的值是一样的，都用单个字符表示
        spiceSex1 = [
            "property",
            "\"" + "Spice_Primitive" + "\"",
            "\"" + "X" + "\"",  ## 获取Reference的值，不要后面的顺序号,这就可以做为Spice_Primitive的值
        ]
    else:
        spiceSex1 = [
            "property",
            "\"" + "Spice_Primitive" + "\"",
            "\"" + symbol.properties[0].value[0] + "\"",  ## 获取Reference的值，不要后面的顺序号,这就可以做为Spice_Primitive的值
        ]

    spiceSex1.append(["id", "4"], )
    spiceSex1.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
    spiceSex1.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了

    sx.append(spiceSex1)

    ## 添加"Spice_Model"
    spiceSex2 = [
        "property",
        "\"" + "Spice_Model" + "\"",
    ]

    ## 根据不同元器件进行仿真电器值设定
    if (symbol.name == "R" or symbol.name == "R_Variable" or symbol.name == "R_Photo" or symbol.name == "R_Trim" or
            symbol.name == "R_US"):
        parameterValues = random.randint(1, 1000)  # 设置电阻值，之后可以随机生成
        spiceSex2.append("\"" + str(parameterValues) + "\"")
    elif symbol.name == "CAP" or symbol.name == "C_Variable" or symbol.name == "C_Polarized" or symbol.name == "C_Polarized_US":
        parameterValues = random.randint(1, 1000)  # 设置电容值，之后可以随机生成
        spiceSex2.append("\"" + str(parameterValues) + "nF" + "\"")
    elif (symbol.name == "INDUCTOR" or symbol.name == "L_Ferrite" or symbol.name == "L_Iron" or symbol.name == "L_Iron_Small"
          or symbol.name == "L_Small" or symbol.name == "L_Trim"):
        parameterValue1 = random.randint(1, 1000)  # 设置电感值，之后可以随机生成
        sexprText1 = "\"" + str(parameterValue1) + "uH" + "\""
        parameterValue2 = random.randint(10,100)
        sexprText2 = "\"" + str(parameterValue2) + "mH" + "\""
        selected_string = random.choice([sexprText1, sexprText2])
        spiceSex2.append(selected_string)
    elif symbol.name == "VSOURCE" or symbol.name == "ISOURCE":
        parameterValues = random.randint(3, 100)
        # assert "dc" in dsym.opts
        # parameterValues = dsym.opts["dc"]
        spiceSex2.append("\"" + "dc" + " " + str(parameterValues) + "\"")
    elif symbol.name == "SW_Push":
        parameterValues = "1 0 sw_push{}".format(
            dsym.index
            # symbol.properties[0].value
        )
        spiceSex2.append("\"" + str(parameterValues) + "\"")
    elif symbol.name == "DIODE":
        modelName = "1N3491"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Schottky":
        modelName = "1N5711"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Zener":
        # modelName = "BZT52C2V7LP"
        modelName = "10A01"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "LED":
        modelName = "A1SS-O612_VFBIN_D"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "1N4001":
        modelName = "1N4001"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D":
        modelName = "1N4002"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Filled":
        modelName = "1N4003"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Small":
        modelName = "1N4004"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "LED_Filled":
        modelName = "LED_GENERAL"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Zener_Filled":
        modelName = "DI_1N4728A"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "D_Zener_Small":
        modelName = "DI_AZ23C10W"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "Q_NPN_BCE" or symbol.name == "PN2222A":
        modelName = "PN2222"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "Q_PJFET_DGS":
        # modelName = "2N7002A"
        modelName = "DMG4435SSS"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "Q_PMOS_DGS":
        # modelName = "DI_DMG6968U"
        modelName = "DI_DMG6968UDM"
        spiceSex2.append("\"" + modelName + "\"")
    elif symbol.name == "Q_NIGBT_CEG":
        modelName = "APT100G2"
        spiceSex2.append("\"" + modelName + "\"")


    spiceSex2.append(["id", "5"], )
    spiceSex2.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
    spiceSex2.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了

    sx.append(spiceSex2)

    ## 添加"Spice_Netlist_Enabled"
    spiceSex3 = [
        "property",
        "\"" + "Spice_Netlist_Enabled" + "\"",
        "\"" + "Y" + "\"",
    ]
    spiceSex3.append(["id", "6"], )
    spiceSex3.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
    spiceSex3.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了

    sx.append(spiceSex3)

    ## 有源器件需要给模型添加spice模型
    if symbol.name == "DIODE":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = "D:\spice_lib\MicroCap-LIBRARY-for-ngspice\diode.lib"
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "D_Schottky":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = "D:\spice_lib\MicroCap-LIBRARY-for-ngspice\diode.lib"
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "D_Zener":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = "D:\spice_lib\MicroCap-LIBRARY-for-ngspice\DiodesInc.lib"
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "LED":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        spiceLib = "D:\spice_lib\\\\basic_models\LED\SnapLED150.mod"
        # spiceLib = os.path.join('D:','spice_lib','basic_models','LED','SnapLED150.mod')
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "1N4001" or symbol.name == "D" or symbol.name == "D_Filled" or symbol.name == "D_Small":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        spiceLib = "D:\spice_lib\\\\basic_models\diodes\diode.lib"
        # spiceLib = os.path.join('D:','spice_lib','basic_models','LED','SnapLED150.mod')
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "LED_Filled":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        spiceLib = ("D:\spice_lib\KiCad-Spice-Library-master\Models\Diode\led.lib")
        # spiceLib = os.path.join('D:','spice_lib','basic_models','LED','SnapLED150.mod')
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "D_Zener_Filled" or symbol.name == "D_Zener_Small":
        ## 添加"Spice_Lib_File"属性
        spiceSex4 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        spiceLib = ("D:\spice_lib\KiCad-Spice-Library-master\Models\Diode\zener.lib")
        # spiceLib = os.path.join('D:','spice_lib','basic_models','LED','SnapLED150.mod')
        spiceSex4.append("\"" + spiceLib + "\"")
        spiceSex4.append(["id", "7"], )
        spiceSex4.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex4.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex4)
    if symbol.name == "Q_NPN_BCE" or symbol.name == "PN2222A":
        ## 添加"Spice_Lib_File"属性
        spiceSex5 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        spiceLib = "D:\spice_lib\modelos_subckt\PN2222.mod"
        spiceSex5.append("\"" + spiceLib + "\"")
        spiceSex5.append(["id", "7"], )
        spiceSex5.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex5.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex5)
        ## 添加"Spice_Node_Sequence"属性,因为三极管引脚是有顺序的集电极，基极，发射极，基板（可选）
        ## 需要将符号的引脚与模型的引脚的顺序相对应，因此需要添加该属性
        spiceSex6 = [
            "property",
            "\"" + "Spice_Node_Sequence" + "\"",
        ]
        NodeSequence = "2,1,3"  # 目前固定的这个模型引脚顺序为2，1,3
        spiceSex6.append("\"" + NodeSequence + "\"")
        spiceSex6.append(["id", "8"], )
        spiceSex6.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex6.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex6)
    if symbol.name == "Q_PJFET_DGS":
        ## 添加"Spice_Lib_File"属性
        spiceSex5 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = "D:\spice_lib\MicroCap-LIBRARY-for-ngspice\DiodesInc_FET.lib"
        spiceSex5.append("\"" + spiceLib + "\"")
        spiceSex5.append(["id", "7"], )
        spiceSex5.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex5.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex5)
    if symbol.name == "Q_PMOS_DGS":
        ## 添加"Spice_Lib_File"属性
        spiceSex5 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = "D:\spice_lib\MicroCap-LIBRARY-for-ngspice\DiodesInc_MOSFET.LIB"
        spiceSex5.append("\"" + spiceLib + "\"")
        spiceSex5.append(["id", "7"], )
        spiceSex5.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex5.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex5)
    if symbol.name == "Q_NIGBT_CEG":
        ## 添加"Spice_Lib_File"属性
        spiceSex5 = [
            "property",
            "\"" + "Spice_Lib_File" + "\"",
        ]
        ## 这个是给元器件选择实际模型的时候所在库的位置，目前先根据元器件都写死，之后再看如何动态选择等
        spiceLib = r"D:\spice_lib\KiCad-Spice-Library-master\Models\uncategorized\spice_complete\IGBT.LIB"
        spiceSex5.append("\"" + spiceLib + "\"")
        spiceSex5.append(["id", "7"], )
        spiceSex5.append(["at", SymbolPosition[0], SymbolPosition[1], SymbolPosition[2]], )
        spiceSex5.append(symbol.properties[3].effects.get_sexpr())  # 与Datasheet属性的effects值一样，我们就直接用，就不进行拼接了
        sx.append(spiceSex5)


if __name__ == '__main__':
    writer = KicadWriter("test3.kicad_sch")
    dia = Diagram()
    writer.write(dia)
