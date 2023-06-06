import json
import requests
import operator
import string



# links
url_2 = "https://www.wix.com/_serverless/hiring-task-spreadsheet-evaluator/sheets"


# getting json into python
response = requests.get(url_2)
response.raise_for_status()  # raises exception when not a 2xx response
if response.status_code != 204:
    data = response.json()


# initial changes(email, results)
url = data.pop("submissionUrl")
print(url)
data["email"] = "lazarchuk.dm@gmail.com"
data["results"] = data.pop("sheets")
# print(json.dumps(data, indent=2))



# Working with contents


# defining multiply function for all el-s in a list
def multiplyList(myList):
    result = 1
    for x in myList:
        result = result * x
    return result


# defining the operator functions
OPERATORS = {
    "SUM": sum,
    "MULTIPLY": multiplyList,
    "DIVIDE": operator.truediv,
    "GT": operator.gt,
    "EQ": operator.eq,
    "NOT": operator.not_,
    "AND": all,
    "OR": any,
    "IF": lambda cond, true_val, false_val: true_val if cond else false_val,
    "CONCAT": lambda strings: "".join(strings),
}


# function to parse the concat args correctly
def concat_args_parser(formula):
    formula_args = "," + formula[:-1].split("(", 1)[1]
    args_list = []
    i = 0
    while i < len(formula_args):
        character = formula_args[i]
        if character == ",":
            token = formula_args[i + 1 :].split(",", 1)[0].strip()
            i += len(token) + 2
            args_list.append(token)
            continue
        if character == '"':
            token = formula_args[i + 1 :].split('"', 1)[0]
            i += len(token) + 2
            args_list.append(token)
            continue
        i += 1
    return args_list


# alphabet to check for the cell reference
letters = string.ascii_uppercase


# loop to calculate cells
for sheet in data["results"]:
    for row_idx, row in enumerate(sheet["data"]):
        for col_idx, cell in enumerate(row):
            if isinstance(cell, str) and cell.startswith("="):
                operator_str, *args = cell[1:].split(",")

                if "IF" in operator_str:
                    operator_str, cond, temp = operator_str.split("(")
                    cond = cond.strip()
                else:
                    try:
                        operator_str, temp = operator_str.split("(")
                    except:
                        temp = operator_str

                # remove white spaces from args and operator
                operator_str = operator_str.strip()
                args.insert(0, temp)
                args = [arg.strip(" )") for arg in args]

                # cell references
                for i, arg in enumerate(args):
                    if arg.replace(".", "", 1).isdigit():
                        args[i] = int(arg) 
                    elif arg[0].upper() in letters and arg[1:].isdigit():
                        col = letters.index(arg[0].upper())
                        row = int(arg[1:]) - 1
                        args[i] = sheet["data"][row][col]
                        ref = sheet["data"][row][col]


                # checking value types
                arg_types = [type(arg) for arg in args]
                error_check = len(set(arg_types))

                # evaluation
                if error_check > 1 and "cond" not in globals():
                    result = "#ERROR: type does not match"
                    sheet["data"][row_idx][col_idx] = result
                elif operator_str in OPERATORS:
                    if operator_str in ("SUM", "AND", "OR", "MULTIPLY"):
                        result = OPERATORS[operator_str](args)
                        sheet["data"][row_idx][col_idx] = result
                    elif operator_str == "CONCAT":
                        args = concat_args_parser(cell)

                        for i, arg in enumerate(args):
                            if arg.replace(".", "", 1).isdigit():
                                args[i] = int(arg)   
                            elif arg[0].upper() in letters and arg[1:].isdigit():
                                col = letters.index(arg[0].upper())
                                row = int(arg[1:]) - 1
                                args[i] = sheet["data"][row][col]
                                ref = sheet["data"][row][col]

                        args = [arg.strip('"') for arg in args]
                        args = list(filter(None, args))
                        result = OPERATORS[operator_str](args)
                        sheet["data"][row_idx][col_idx] = result
                    elif operator_str == "IF":
                        conds = [args.pop(0) for arg in args[:2]]
                        cond = OPERATORS[cond](*conds)
                        args.insert(0, cond)
                        result = OPERATORS[operator_str](*args)
                        sheet["data"][row_idx][col_idx] = result
                    else:
                        result = OPERATORS[operator_str](*args)
                        sheet["data"][row_idx][col_idx] = result
                else:
                    if isinstance(ref, str):
                        while ref.startswith("="):
                            ref = ref[1:]
                            col = letters.index(ref[0].upper())
                            row = int(ref[1:]) - 1
                            ref = sheet["data"][row][col]
                    sheet["data"][row_idx][col_idx] = ref




# submitting
response = requests.post(url, json=data)
print(response.text, response.status_code)
# fcbaa93fbafc57904103906723e5d75a
