# -*- coding:utf-8 -*-
from enum import Enum
from Calculate import *

Length = {'int': 4, 'char': 1}
PointerLength = 4
reg_use = 0


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def regAllocate(var=None):
    global reg_use
    if isinstance(var, int) or var is None:
        reg_use += 1
        return "tempReg-" + str(reg_use)
    var = str(var)
    if "Reg-" in var:
        return var
    elif is_number(var):
        return int(var)
    else:
        return "Reg-" + var


class Grammar(Enum):
    VarDefinition = 0
    PointerDefinition = 1
    ArrayDefinition = 2
    VarAsgn = 3
    MemAsgn = 4
    VarAddAsgn = 5
    VarMinusAsgn = 6
    VarMutilAsgn = 7
    VarDivAsgn = 8
    SelfAdd = 9
    SelfMinus = 10


class Statements:
    def __init__(self, grammar, defVar=None, useVar=None, left=None, right=None, memUse=None, varSpace=None, top=None):
        self.grammar = grammar
        self.defVar = defVar
        self.useVar = useVar
        self.left = left
        self.right = right
        self.memUse = memUse
        self.varSpace = varSpace
        self.stackTop = top
        self.ISA = []

    def memProcess(self, mem, right=True):
        index = self.memUse[mem]
        varName = mem[:mem.find('[')]
        stack_value = []
        for item in index:
            if item in ['+', '-', '*', '/']:
                n2 = stack_value.pop()  # 注意，先出栈的在操作符右边.
                n1 = stack_value.pop()
                # 均为数字
                if is_number(n1) and is_number(n2):
                    if item == '/':
                        item = '//'
                    result = eval(n1 + item + n2)
                    stack_value.append(result)
                else:
                    reg0 = regAllocate()
                    reg_n1 = regAllocate(n1)
                    reg_n2 = regAllocate(n2)
                    self.ISA.append((item, reg0, reg_n1, reg_n2))
                    stack_value.append(reg0)
            else:
                stack_value.append(item)  # 数值直接压栈.
        fin = stack_value[0]
        if right:
            reg1 = regAllocate()
            reg2 = regAllocate()
            if is_number(fin):
                self.ISA.append(('lw', reg2, regAllocate('s0'),
                                 self.varSpace[varName] - self.stackTop + int(fin) * 4))
            else:
                self.ISA.append(('slli', reg1, fin, 2))
                self.ISA.append(
                    ('addi', reg2, regAllocate('s0'), self.varSpace[varName] - self.stackTop))
                self.ISA.append(('add', reg2, reg2, reg1))
                self.ISA.append(('lw', reg2, reg2, 0))
            return reg2
        else:
            return fin

    def process(self):
        if self.grammar == Grammar.VarAsgn:
            stack_value = []
            for item in self.right:
                if item in ['+', '-', '*', '/']:
                    n2 = stack_value.pop()  # 注意，先出栈的在操作符右边.
                    n1 = stack_value.pop()
                    if is_number(n1) and is_number(n2):
                        if item == '/':
                            item = '//'
                        stack_value.append(eval(n1 + item + n2))
                    else:
                        reg1 = regAllocate(n1)
                        reg2 = regAllocate(n2)
                        if n1 in self.memUse:
                            reg1 = self.memProcess(n1)
                        if n2 in self.memUse:
                            reg2 = self.memProcess(n2)
                        reg0 = regAllocate()
                        self.ISA.append((item, reg0, reg1, reg2))
                        stack_value.append(reg0)
                else:
                    stack_value.append(item)  # 数值直接压栈.
            rightValue = stack_value[0]
            # 单个内存情况考虑
            if '[' in rightValue:
                rightValue = self.memProcess(rightValue)
            if self.left in self.varSpace:
                if is_number(rightValue):
                    self.ISA.append(('li', regAllocate(self.left), int(rightValue)))
                else:
                    self.ISA.append(('add', regAllocate(self.left), regAllocate("x0"), rightValue))
            else:
                varName = self.left[:self.left.find('[')]
                index = self.memProcess(self.left, False)
                if is_number(index):
                    if is_number(rightValue):
                        reg0 = regAllocate()
                        self.ISA.append(('li', reg0, int(rightValue)))
                        self.ISA.append(('sw', reg0, regAllocate('s0'),
                                         self.varSpace[varName] - self.stackTop + int(index) * 4))
                    else:
                        self.ISA.append(('sw', rightValue, regAllocate('s0'),
                                         self.varSpace[varName] - self.stackTop + int(index) * 4))
                else:
                    reg1 = regAllocate()
                    reg2 = regAllocate()
                    self.ISA.append(('slli', reg1, index, 2))
                    self.ISA.append(
                        ('addi', reg2, regAllocate('s0'), self.varSpace[varName] - self.stackTop))
                    self.ISA.append(('add', reg2, reg2, reg1))
                    if is_number(rightValue):
                        self.ISA.append(('li', reg1, int(rightValue)))
                        self.ISA.append(('sw', reg1, reg2, 0))
                    else:
                        self.ISA.append(('sw', rightValue, reg2, 0))
        print(self.ISA)


class Tokenizer:
    def __init__(self, varSpace=None):
        if varSpace is None:
            varSpace = {}
        self.varSpace = varSpace
        self.pointer = 10000
        self.top = self.pointer

    # 暂不考虑数组的套娃使用
    def memParse(self, mem):
        varName = mem[:mem.find('[')]
        assert varName in self.varSpace
        expr = mem[mem.find('[') + 1:mem.find(']')]
        expr = middle_to_after(expr)
        use = []
        for item in expr:
            if item in self.varSpace:
                use.append(item)
        return expr, use

    def token(self, sentence):
        sentence = sentence.strip()
        sentence = sentence[:-1]
        if 'int' == sentence[:3] or 'char' == sentence[:4]:
            varName = sentence.split(" ")[-1]
            if "[" in varName:
                pos = varName.find("[")
                arrayLength = varName[pos + 1:-1]
                varName = varName[: pos]
                assert varName not in self.varSpace
                self.pointer -= int(arrayLength) * Length[sentence[:3]]
                self.varSpace[varName] = self.pointer
                return Statements(Grammar.ArrayDefinition)
            elif "*" in sentence:
                varName = varName.replace('*', '')
                assert varName not in self.varSpace
                # -1表示不分配内存
                self.varSpace[varName] = -1
                return Statements(Grammar.PointerDefinition)
            else:
                assert varName not in self.varSpace
                self.varSpace[varName] = -1
                return Statements(Grammar.ArrayDefinition)

        if '=' in sentence:
            pos = sentence.find('=')
            if sentence[pos - 1] == '+':
                grammarType = Grammar.VarAddAsgn
                left = sentence[:pos - 1].strip()
            elif sentence[pos - 1] == '-':
                grammarType = Grammar.VarMinusAsgn
                left = sentence[:pos - 1].strip()
            elif sentence[pos - 1] == '*':
                grammarType = Grammar.VarMutilAsgn
                left = sentence[:pos - 1].strip()
            elif sentence[pos - 1] == '/':
                grammarType = Grammar.VarDivAsgn
                left = sentence[:pos - 1].strip()
            else:
                grammarType = Grammar.VarAsgn
                left = sentence[:pos].strip()
            right = sentence[pos + 1:].strip()
            right = middle_to_after(right)
            useVar = []
            memUse = {}
            if "[" not in left:
                defVar = left
            else:
                defVar = None
                useVar.append(left[:left.find('[')])
                expr, use = self.memParse(left)
                memUse[left] = expr
                useVar.extend(use)
            for item in right:
                if '[' in item:
                    expr, use = self.memParse(item)
                    memUse[item] = expr
                    useVar.extend(use)
                    item = item[:item.find('[')]
                if item in self.varSpace:
                    useVar.append(item)
            useVar = list(set(useVar))
            return Statements(grammarType, defVar, useVar, left, right, memUse, self.varSpace, self.top)

        if "++" in sentence:
            varName = sentence[2:].strip()
            useVar = []
            memUse = {}
            if '[' not in varName:
                defVar = varName
                useVar.append(varName)
            else:
                defVar = None
                useVar.append(varName[:varName.find('[')])
                expr, use = self.memParse(varName)
                memUse[varName] = expr
                useVar.extend(use)
            useVar = list(set(useVar))
            return Statements(Grammar.SelfAdd, defVar=defVar, useVar=useVar, memUse=memUse)

        if "--" in sentence:
            varName = sentence[2:].strip()
            useVar = []
            memUse = {}
            if '[' not in varName:
                defVar = varName
                useVar.append(varName)
            else:
                defVar = None
                useVar.append(varName[:varName.find('[')])
                expr, use = self.memParse(varName)
                memUse[varName] = expr
                useVar.extend(use)
            useVar = list(set(useVar))
            return Statements(Grammar.SelfMinus, defVar=defVar, useVar=useVar, memUse=memUse)


if __name__ == "__main__":
    tokenizer = Tokenizer()
    tokenizer.token(" int  abc[10];")
    tokenizer.token("int a;")
    tokenizer.token("int c;")
    test = tokenizer.token(" a= abc[c+a]+a;")
    test.process()
    # tokenizer.token(" a += abc[a] + c;")
    # tokenizer.token("++ abc[a+3];")
