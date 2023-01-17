# -*- coding: utf-8 -*-
from AST import *


class Var:
    def __init__(self, Type, name, BitSize, MemAddr):
        """
        :param Type: 变量类型
        :param name: 变量名称
        :param BitSize: 大小
        :param MemAddr: 其实地址
        """
        self.Type = Type
        self.Name = name
        self.BitSize = BitSize
        self.MemAddr = MemAddr


class RegAllocate:
    def __init__(self):
        self.regNum = 0

    def allocate(self, varName=None):
        if varName is None:
            self.regNum += 1
            return "tempReg-" + str(self.regNum)
        elif "Reg-" in varName:
            return varName
        else:
            return "Reg-" + varName


class Tokenizer:
    def __init__(self, varSpace=None):
        if varSpace is None:
            varSpace = {}
        self.varSpace = varSpace
        self.stack_size = 10000
        self.stack_pointer = self.stack_size
        self.regAllocate = RegAllocate()
        self.BlockNum = 0
        self.ISA = []
        self.ISAProcess = []

    def CreateBlock(self):
        self.ISA.append("Create Block " + str(self.BlockNum))
        self.BlockNum += 1

    def memAllocate(self, BitSize):
        self.stack_pointer -= BitSize
        return self.stack_pointer

    def token(self, sentence):
        if isinstance(sentence, str):
            ast = getAST(sentence)
        else:
            ast = sentence
        nodeType = type(ast)
        infor = GetInformation(ast)
        if nodeType == Decl:
            delType = ast.type
            if type(delType) == TypeDecl:
                self.varSpace[infor['Name']] = Var(infor['DeclType'], infor['Name'], infor['BitSize'], -1)
            elif type(delType) == ArrayDecl:
                self.varSpace[infor['Name']] = Var(infor['DeclType'], infor['Name'],
                                                   infor['BitSize'], self.memAllocate(infor['BitSize']))
            return None
        elif nodeType == Assignment:
            lvalue = infor["LValue"]
            rvalue = infor["RValue"]
            rReg = self.token(rvalue)
            if type(lvalue) == ID:
                self.ISA.append([infor["Op"], self.regAllocate.allocate(lvalue.name), rReg])
            elif type(lvalue) == ArrayRef:
                subscript = self.token(lvalue.subscript)
                self.ISA.append([infor["Op"], "sw", lvalue.name.name, subscript, rReg])
            return None
        elif nodeType == ID:
            return self.regAllocate.allocate(infor['Name'])
        elif nodeType == Constant:
            return int(ast.value)
        elif nodeType == BinaryOp:
            left = infor['Left']
            right = infor['Right']
            lvalue = self.token(left)
            rvalue = self.token(right)
            if isinstance(lvalue, int) and isinstance(rvalue, int):
                return lvalue + rvalue
            targetReg = self.regAllocate.allocate()
            self.ISA.append([infor["Op"], targetReg, lvalue, rvalue])
            return targetReg
        elif nodeType == ArrayRef:
            subscript = self.token(infor['Subscript'])
            targetReg = self.regAllocate.allocate()
            self.ISA.append(["lw", targetReg, infor["Name"], subscript])
            return targetReg
        elif nodeType == UnaryOp:
            if infor['ExprType'] == ID:
                self.ISA.append([infor['Op'], infor['Name']])
                return self.regAllocate.allocate(infor['Name'])
            else:
                subscript = infor['Subscript']
                subscript = self.token(subscript)
                self.ISA.append([infor['Op'], infor['Name'], subscript])
                return None
        elif nodeType == FuncCall:
            funcName = infor["Name"]
            self.ISA.append(["call", funcName])
            return self.regAllocate.allocate()

    def process(self):
        for isa in self.ISA:
            if isinstance(isa, str):
                num = isa.split(" ")[-1]
                self.ISAProcess.append("Block " + str(num))
            else:
                op = isa[0]
                if op == '+':
                    targetReg = isa[1]
                    reg1 = isa[2]
                    reg2 = isa[3]
                    if isinstance(reg1, int) or isinstance(reg2, int):
                        reg1, reg2 = (reg2, reg1) if isinstance(reg1, int) else (reg1, reg2)
                        self.ISAProcess.append(("addi", targetReg, reg1, reg2))
                    else:
                        self.ISAProcess.append(("add", targetReg, reg1, reg2))
                elif op == "-":
                    targetReg = isa[1]
                    reg1 = isa[2]
                    reg2 = isa[3]
                    if isinstance(reg1, int) or isinstance(reg2, int):
                        reg1, reg2 = (reg2, reg1) if isinstance(reg1, int) else (reg1, reg2)
                        self.ISAProcess.append(("addi", targetReg, reg1, -reg2))
                    else:
                        self.ISAProcess.append(("sub", targetReg, reg1, reg2))
                elif op == '*':
                    targetReg = isa[1]
                    reg1 = isa[2]
                    reg2 = isa[3]
                    if isinstance(reg1, int) or isinstance(reg2, int):
                        reg1, reg2 = (reg2, reg1) if isinstance(reg1, int) else (reg1, reg2)
                        reg3 = self.regAllocate.allocate()
                        self.ISAProcess.append(("li", reg3, reg2))
                        self.ISAProcess.append(("mul", targetReg, reg1, reg3))
                    else:
                        self.ISAProcess.append(("mul", targetReg, reg1, reg2))
                elif op == '/':
                    targetReg = isa[1]
                    reg1 = isa[2]
                    reg2 = isa[3]
                    if isinstance(reg1, int) or isinstance(reg2, int):
                        reg1, reg2 = (reg2, reg1) if isinstance(reg1, int) else (reg1, reg2)
                        reg3 = self.regAllocate.allocate()
                        self.ISAProcess.append(("li", reg3, reg2))
                        self.ISAProcess.append(("div", targetReg, reg1, reg3))
                    else:
                        self.ISAProcess.append(("div", targetReg, reg1, reg2))
                elif op == 'lw':
                    offset = isa[-1]
                    varName = isa[-2]
                    startOffset = self.varSpace[varName].MemAddr - self.stack_size
                    targetReg = isa[1]
                    if isinstance(offset, int):
                        self.ISAProcess.append(('lw', targetReg, self.regAllocate.allocate("s0"),
                                                startOffset + offset * bitSize[self.varSpace[varName].Type]))
                    else:
                        if self.varSpace[varName].Type == 'int':
                            self.ISAProcess.append(("slli", offset, offset, 2))
                        reg1 = self.regAllocate.allocate()
                        self.ISAProcess.append(("addi", reg1, self.regAllocate.allocate("s0"), startOffset))
                        self.ISAProcess.append(("add", reg1, reg1, offset))
                        self.ISAProcess.append(("lw", targetReg, reg1, 0))
                elif op == "=":
                    if isa[1] != 'sw':
                        if isinstance(isa[2], str):
                            self.ISAProcess.append(('add', isa[1], self.regAllocate.allocate("x0"), isa[2]))
                        else:
                            self.ISAProcess.append(('li', isa[1], isa[2]))
                    else:
                        offset = isa[-2]
                        varName = isa[-3]
                        startOffset = self.varSpace[varName].MemAddr - self.stack_size
                        useReg = isa[-1]
                        if isinstance(useReg, int):
                            tmp = useReg
                            useReg = self.regAllocate.allocate()
                            self.ISAProcess.append(("li", useReg, tmp))
                        if isinstance(offset, int):
                            self.ISAProcess.append(('sw', useReg, self.regAllocate.allocate("s0"),
                                                    startOffset + offset * bitSize[self.varSpace[varName].Type]))
                        else:
                            if self.varSpace[varName].Type == 'int':
                                self.ISAProcess.append(("slli", offset, offset, 2))
                            reg1 = self.regAllocate.allocate()
                            self.ISAProcess.append(("addi", reg1, self.regAllocate.allocate("s0"), startOffset))
                            self.ISAProcess.append(("add", reg1, reg1, offset))
                            self.ISAProcess.append(("sw", useReg, reg1, 0))
                elif "=" in op:
                    cal = op[0]
                    if isa[1] != 'sw':
                        if isinstance(isa[2], str):
                            self.ISAProcess.append((calculate[cal], isa[1], isa[1], isa[2]))
                        else:
                            if cal == "+":
                                self.ISAProcess.append(('addi', isa[1], isa[1], isa[2]))
                            elif cal == "-":
                                self.ISAProcess.append(('addi', isa[1], isa[1], -isa[2]))
                            else:
                                reg1 = self.regAllocate.allocate()
                                self.ISAProcess.append(('li', reg1, isa[2]))
                                self.ISAProcess.append((calculate[cal], isa[1], isa[1], reg1))
                    else:
                        offset = isa[-2]
                        varName = isa[-3]
                        startOffset = self.varSpace[varName].MemAddr - self.stack_size
                        useReg = isa[-1]
                        if isinstance(useReg, int):
                            tmp = useReg
                            useReg = self.regAllocate.allocate()
                            self.ISAProcess.append(("li", useReg, tmp))
                        if isinstance(offset, int):
                            regTemp = self.regAllocate.allocate()
                            self.ISAProcess.append(('lw', regTemp, self.regAllocate.allocate("s0"),
                                                    startOffset + offset * bitSize[self.varSpace[varName].Type]))
                            self.ISAProcess.append((calculate[cal], regTemp, regTemp, useReg))
                            self.ISAProcess.append(('sw', regTemp, self.regAllocate.allocate("s0"),
                                                    startOffset + offset * bitSize[self.varSpace[varName].Type]))
                        else:
                            if self.varSpace[varName].Type == 'int':
                                self.ISAProcess.append(("slli", offset, offset, 2))
                            reg1 = self.regAllocate.allocate()
                            self.ISAProcess.append(("addi", reg1, self.regAllocate.allocate("s0"), startOffset))
                            self.ISAProcess.append(("add", reg1, reg1, offset))
                            regTemp = self.regAllocate.allocate()
                            self.ISAProcess.append(("lw", regTemp, reg1, 0))
                            self.ISAProcess.append((calculate[cal], regTemp, regTemp, useReg))
                            self.ISAProcess.append(("sw", regTemp, reg1, 0))
                elif op == 'p++' or op == 'p--' or op == '++' or op == '--':
                    varName = isa[1]
                    if len(isa) == 2:
                        if op[1] == "+":
                            self.ISAProcess.append(("addi", self.regAllocate.allocate(varName),
                                                    self.regAllocate.allocate(varName), 1))
                        else:
                            self.ISAProcess.append(("addi", self.regAllocate.allocate(varName),
                                                    self.regAllocate.allocate(varName), -1))
                    else:
                        offset = isa[-1]
                        varName = isa[-2]
                        startOffset = self.varSpace[varName].MemAddr - self.stack_size
                        regTemp = self.regAllocate.allocate()
                        if isinstance(offset, int):
                            self.ISAProcess.append(('lw', regTemp, self.regAllocate.allocate("s0"),
                                                    startOffset + offset * bitSize[self.varSpace[varName].Type]))
                            if op[1] == "+":
                                self.ISAProcess.append(("addi", regTemp, regTemp, 1))
                            else:
                                self.ISAProcess.append(("addi", regTemp, regTemp, -1))
                            self.ISAProcess.append(('sw', regTemp, self.regAllocate.allocate("s0"),
                                                    startOffset + offset * bitSize[self.varSpace[varName].Type]))
                        else:
                            if self.varSpace[varName].Type == 'int':
                                self.ISAProcess.append(("slli", offset, offset, 2))
                            reg1 = self.regAllocate.allocate()
                            self.ISAProcess.append(("addi", reg1, self.regAllocate.allocate("s0"), startOffset))
                            self.ISAProcess.append(("add", reg1, reg1, offset))
                            self.ISAProcess.append(("lw", regTemp, reg1, 0))
                            if op[1] == "+":
                                self.ISAProcess.append(("addi", regTemp, regTemp, 1))
                            else:
                                self.ISAProcess.append(("addi", regTemp, regTemp, -1))
                            self.ISAProcess.append(("sw", regTemp, reg1, 0))
                elif op == "call":
                    self.ISAProcess.append(("call", isa[1]))


if __name__ == "__main__":
    tokenizer = Tokenizer()
    tokenizer.CreateBlock()
    txt = "int a;"
    tokenizer.token(txt)
    txt = "int b;"
    tokenizer.token(txt)
    txt = "int c[10];"
    tokenizer.token(txt)
    txt = "a = sort(c);"
    # txt = "c[a] *= c[a] + b;"
    tokenizer.token(txt)
    tokenizer.process()
    print(tokenizer.ISA)
    print(tokenizer.ISAProcess)
