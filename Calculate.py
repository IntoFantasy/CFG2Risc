# -*- coding:utf-8 -*-
# 运算规则，先乘除，后加减.
ops_rule = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2
}


def preprocess(s):
    s = s.replace('+', ' + ')
    s = s.replace('-', ' - ')
    s = s.replace('*', ' * ')
    s = s.replace('/', ' / ')
    s = s.replace('(', ' ( ')
    s = s.replace(')', ' ) ')
    s = s.strip()
    while "  " in s:
        s = s.replace("  ", " ")
    flag = False
    for i in range(len(s)):
        if s[i] == '[':
            flag = True
        if s[i] == ']':
            flag = False
        if flag and s[i] == ' ':
            s = s[:i] + '#' + s[i+1:]
    s = s.replace('#', '')
    return s


def middle_to_after(s):
    """
    中缀表达式转化后缀表达式.
    :param s: 中缀表达式的字符串表示，本程序中采用操作符跟数值之间用空格分开，例如:
    "9 + ( 3 - 1 ) * 3 + 10 / 2"
    :return: 后缀表达式，数组的形式，每个数值或者操作符占一个数组下标.
    """
    s = preprocess(s)
    expression = []
    ops = []
    ss = s.split(' ')
    for item in ss:
        if item in ['+', '-', '*', '/']:  # 操作符
            while len(ops) >= 0:
                if len(ops) == 0:
                    ops.append(item)
                    break
                op = ops.pop()
                if op == '(' or ops_rule[item] > ops_rule[op]:
                    ops.append(op)
                    ops.append(item)
                    break
                else:
                    expression.append(op)
        elif item == '(':  # 左括号，直接入操作符栈
            ops.append(item)
        elif item == ')':  # 右括号，循环出栈道
            while len(ops) > 0:
                op = ops.pop()
                if op == '(':
                    break
                else:
                    expression.append(op)
        else:
            expression.append(item)  # 数值，直接入表达式栈

    while len(ops) > 0:
        expression.append(ops.pop())

    return expression


def expression_to_value(expression, cal):
    """
    :param cal: 函数
    :param expression: 后缀表达式的数组表示
    :return: 运算结果，一个值
    """
    stack_value = []
    for item in expression:
        if item in ['+', '-', '*', '/']:
            n2 = stack_value.pop()  # 注意，先出栈的在操作符右边.
            n1 = stack_value.pop()
            result = cal(n1, n2, item)
            stack_value.append(result)
        else:
            stack_value.append(item)  # 数值直接压栈.
    return stack_value[0]


# def cal(n1, n2, op):
#     if op == '+':
#         return n1 + n2
#     if op == '-':
#         return n1 - n2
#     if op == '*':
#         return n1 * n2
#     if op == '/':
#         return n1 / n2


if __name__ == "__main__":
    sen = "a4+ (3- 1 )*3 +10 / 2"
    # sen = preprocess(sen)
    print(middle_to_after(sen))
    # print(expression_to_value("9 3 1 - 3 * + 10 2 / +"))
