from pycparser import CParser
from pycparser.c_ast import *

bitSize = {'int': 4, 'char': 1}
calculate = {'+': "add", '-': "sub", '*': "mul", '/': "div"}


def getAST(sentence):
    sentence = "int main(){\n" + sentence + "}"
    ast = CParser().parse(sentence)
    body = ast.ext[0].body.block_items
    return body[0]


def GetInformation(ast):
    infor = {"Type": type(ast)}
    if type(ast) == Decl:
        delType = ast.type
        if type(delType) == TypeDecl:
            infor['DeclType'] = ast.type.type.names[0]
            infor['Name'] = ast.type.declname
            infor['Init'] = ast.init
            infor['BitSize'] = bitSize[infor['DeclType']]
            return infor
        elif type(delType) == ArrayDecl:
            infor['DeclType'] = ast.type.type.type.names[0]
            infor['Name'] = ast.type.type.declname
            infor['Init'] = ast.init
            infor['BitSize'] = bitSize[infor['DeclType']] * int(ast.type.dim.value)
            return infor
    elif type(ast) == Assignment:
        infor['LValue'] = ast.lvalue
        infor['RValue'] = ast.rvalue
        infor['Op'] = ast.op
        return infor
    elif type(ast) == ID:
        infor["Name"] = ast.name
        return infor
    elif type(ast) == BinaryOp:
        infor["Op"] = ast.op
        infor["Left"] = ast.left
        infor["Right"] = ast.right
        return infor
    elif type(ast) == ArrayRef:
        infor["Name"] = ast.name.name
        infor["Subscript"] = ast.subscript
        return infor
    elif type(ast) == UnaryOp:
        infor['Op'] = ast.op
        infor['ExprType'] = type(ast.expr)
        infor['Expr'] = ast.expr
        if type(ast.expr) == ArrayRef:
            infor['Name'] = ast.expr.name.name
            infor['Subscript'] = ast.expr.subscript
        elif type(ast.expr) == FuncCall:
            infor['Name'] = ast.expr.name.name
        else:
            infor['Name'] = ast.expr.name
        return infor
    elif type(ast) == FuncCall:
        infor["Name"] = ast.name.name
        infor["args"] = ast.args
        return infor


if __name__ == "__main__":
    txt = "sort(a, 1)++;"
    print(getAST(txt))
    print(GetInformation(getAST(txt)))
