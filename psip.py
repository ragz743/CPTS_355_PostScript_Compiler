# Name: Sairaghav Gubba
# Date: April 20, 2025
# WSU ID: 011796482
# Class: CPT_S 355
# Professor: Subramanian Kandaswamy
# Assignment: Postscript interpreter in Python (Assignment 4)

# Built upon the PostScript Interpreter we made in-class

import copy
import logging
import math

logging.basicConfig(level = logging.INFO)

op_stack = []
dict_stack = []
dict_stack.append({})

# Scope flag to switch between dynamic and lexical scoping. Use False for dynamic and True for lexical
scope_flag = False

class ParseFailed(Exception):
  """ Exception while parsing """
  def __init__(self, message):
    super().__init__(message)

class TypeMismatch(Exception):
  """ Exception with types of operators and operands """
  def __init__(self, message):
    super().__init__(message)

def repl():
  global scope_flag
  while True:
    user_input = input("REPL> ")
    if user_input.lower() == "quit":
      break
    elif user_input.lower() == "lexical":
      scope_flag = True
      print("Switched to lexical scoping")
    elif user_input.lower() == "dynamic":
      scope_flag = False
      print("Switched to dynamic scoping")
    else:
      process_input(user_input)
      logging.debug(f"Operand Stack: {op_stack}")

def process_boolean(input):
  logging.debug(f"Input to process boolean: {input}")
  if input == "true":
    return True
  elif input == "false":
    return False
  else:
    raise ParseFailed("Can't parse it into boolean")
  
def process_number(input):
  logging.debug(f"Input to process number: {input}")
  try:
    float_value = float(input)
    if float_value.is_integer():
      return int(float_value)
    else:
      return float_value
  except ValueError:
    raise ParseFailed("Can't parse this into a number")
  
def process_code_block(input):
  logging.debug(f"Input to process number: {input}")
  if len(input) >= 2 and input.startswith("{") and input.endswith("}"):
    tokens = input[1:-1].strip().split()
    if scope_flag == True: # lexical scope
      environment = copy.deepcopy(dict_stack)
      return (tokens, environment)
    else:
      return tokens
  else:
    raise ParseFailed("Can't parse this into a code block")
  
def process_string(input):
  logging.debug(f"Input to process number: {input}")
  input = input.strip()
  if input.startswith("(") and input.endswith(")"):
    length = len(input)
    return input[1:(length - 1)]
  else:
    raise ParseFailed("Can't parse this into a string")
  
def process_name_constant(input):
  logging.debug(f"Input to process number: {input}")
  if input.startswith("/"):
    return input
  else:
    raise ParseFailed("Can't parse into a name constant")
  
def lookup_in_dictionary(input):
  if input in dict_stack[0]:
    value = dict_stack[0][input]
    if callable(value):
      value()
    elif isinstance(value, list):
      for item in value:
        process_input(item)
    elif isinstance(value, tuple):
      tokens, environment = value
      dict_stack.append(environment)
      for token in tokens:
        process_input(token)
      dict_stack.pop()
    else:
      op_stack.append(value)
    return 

  # Lexical scoping
  if scope_flag == True: 
    # Check at the dictionary you are in (i.e. top of dict_stack) for input.
    # Otherwise, check the global dictionary (i.e. dict_stack[0]) 
    for dictionary in dict_stack:
      if input in dictionary:
        # Get value from input key
        value = dictionary[input]
        if callable(value): # Check if value is an operation
          value()
        elif isinstance(value, list): # Check if value is a list of tokens
          for item in value:
            process_input(item)
        elif isinstance(value, tuple):
          tokens, environment = value
          dict_stack.append(environment)
          for token in tokens:
            process_input(token)
          dict_stack.pop()
        else: # Otherwise, value is a number or string
          op_stack.append(value)
        return
  else:
    # Dynamic scoping
    # Start from the current dictionary and work your way to the global dictionary
    for dictionary in reversed(dict_stack):
      if input in dictionary:
        value = dictionary[input]
        if callable(value):
          value()
        elif isinstance(value, list):
          for item in value:
            process_input(item)
        elif isinstance(value, tuple):
          tokens, environment = value
          dict_stack.append(environment)
          for token in tokens:
            process_input(token)
          dict_stack.pop()
        else:
          op_stack.append(value)
        return
  raise ParseFailed(f"Input {input} is not in dictionary")

def process_input(user_input):
  if isinstance(user_input, list):
    for token in user_input:
      process_input(token)
  elif isinstance(user_input, str):
    # tokens = user_input.split()
    tokens = custom_tokenizer(user_input)
    for token in tokens:
      try:
        process_constants(token)
      except ParseFailed as e:
        logging.debug(e)
        try:
          lookup_in_dictionary(token)
        except Exception as e:
          logging.error(e)
  else: 
    raise ParseFailed(f"{type(user_input)} is an invalid input type")

# Made a custom tokenizer to solve the issue of splitting within strings
def custom_tokenizer(input):
  tokens = []
  cur = ''
  inside_string = False
  inside_block = 0

  for i in range(len(input)):
    # Go over each character in input
    character = input[i]
    # If we are inside a string (i.e. inside the parentheses)
    if inside_string is True:
      cur += character
      if character == ')':
        tokens.append(cur)
        cur = ''
        inside_string = False
    # If we are inside a code block (i.e. inside the curly brackets)
    elif inside_block > 0:
      cur += character
      if character == '{':
        inside_block += 1
      elif character == '}':
        inside_block -= 1
        if inside_block == 0:
          tokens.append(cur)
          cur = ''
    else: # If we are not inside a string
      if character.isspace(): # Is character a space
        if cur != '':
          tokens.append(cur)
          cur = ''
      elif character == '(':
        if cur != '':
          tokens.append(cur)
        cur = '('
        inside_string = True
      elif character == '{':
        if cur != '':
          tokens.append(cur)
        cur = '{'
        inside_block = 1
      else: 
        cur += character
  # Append the final token to tokens and return
  if cur != '':
    tokens.append(cur)
  return tokens
  
PARSERS = [
  process_boolean,
  process_number,
  process_code_block,
  process_name_constant,
  process_string
]

def process_constants(input):
  for parser in PARSERS:
    try:
      res = parser(input)
      op_stack.append(res)
      return
    except ParseFailed as e:
      logging.debug(e)
      continue
  raise ParseFailed(f"None of the parsers worked for the input: {input}")

# ----- STACK MANIPULATION OPERATIONS -----

# exch stack manipulation operation
def exch_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    op_stack.append(op1)
    op_stack.append(op2)
  else:
    raise TypeMismatch("Not enough operands for operation exch")
  
dict_stack[-1]["exch"] = exch_operation

# pop stack manipulation operation
def pop_operation():
  if len(op_stack) >= 1:
    op_stack.pop()
  else:
    raise TypeMismatch("Not enough operands for operation pop")
  
dict_stack[-1]["pop"] = pop_operation

# copy stack manipulation operation
def copy_operation():
  if len(op_stack) >= 1:
    n = op_stack.pop()
    if not isinstance(n, int) or n < 0:
      raise TypeMismatch("n should be a positive integer for operation copy")
    if len(op_stack) >= n:
      copied_elements = copy.deepcopy(op_stack[:n])
      op_stack.extend(copied_elements)
    else:
      raise TypeMismatch("Not enough elements to copy for operation copy")
  else:
    raise TypeMismatch("Not enough operands for operation copy")
  
dict_stack[-1]["copy"] = copy_operation

# dup stack manipulation operation
def dup_operation():
  if len(op_stack) >= 1:
    op1 = op_stack[-1]
    op_stack.append(op1)
  else:
    raise TypeMismatch("Not enough operands for operation dup")
  
dict_stack[-1]["dup"] = dup_operation

# clear stack manipulation operation
def clear_operation():
  op_stack.clear()

dict_stack[-1]["clear"] = clear_operation

# count stack manipulation operation
def count_operation():
  op1 = len(op_stack)
  op_stack.append(op1)

dict_stack[-1]["count"] = count_operation

# ----- ARITHMETIC OPERATIONS -----

# add arithmetic operation
def add_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      res = op1 + op2
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation add must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation add")
  
dict_stack[-1]["add"] = add_operation

# sub arithmetic operation
def sub_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      res = op2 - op1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation sub must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation sub")
  
dict_stack[-1]["sub"] = sub_operation

# mul arithmetic operation
def mul_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      res = op2 * op1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation mul must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation mul")
  
dict_stack[-1]["mul"] = mul_operation

# mod arithmetiic operation
def mod_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      res = op2 % op1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation mod must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation mod")
  
dict_stack[-1]["mod"] = mod_operation

# div arithmetic operation
def div_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      if op1 == 0:
        raise TypeMismatch("Division by zero")
      res = op2 / op1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation div must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation div")

dict_stack[-1]["div"] = div_operation

# idiv arithmetic operation
def idiv_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, (int, float)) and isinstance(op2, (int, float)):
      if op1 == 0:
        raise TypeMismatch("Division by zero")
      res = op2 // op1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation idiv must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation idiv")

dict_stack[-1]["idiv"] = idiv_operation

# abs arithmetic operation
def abs_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      res = abs(op1)
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation abs must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation abs")
  
dict_stack[-1]["abs"] = abs_operation

# neg arithmetic operation
def neg_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      res = op1 * -1
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation neg must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation neg")
  
dict_stack[-1]["neg"] = neg_operation

# ceiling arithmetic operation
def ceiling_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      res = math.ceil(op1)
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation ceiling must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation ceiling")
  
dict_stack[-1]["ceiling"] = ceiling_operation

# floor arithmetic operation
def floor_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      res = math.floor(op1)
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation floor must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation floor")
  
dict_stack[-1]["floor"] = floor_operation

# round arithmetic operation
def round_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      res = round(op1)
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation round must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation round")
  
dict_stack[-1]["round"] = round_operation

# sqrt arithmetic operation
def sqrt_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, (int, float)):
      if (op1 < 0):
        raise TypeMismatch("Square Root of a negative number")
      res = op1 ** 0.5
      op_stack.append(res)
    else:
      raise TypeMismatch("Operands for operation sqrt must be integers and/or floats")
  else:
    raise TypeMismatch("Not enough operands for operation sqrt")
  
dict_stack[-1]["sqrt"] = sqrt_operation

# ----- DICTIONARY OPERATIONS -----

# dict dictionary operation
def dict_operation():
  if len(op_stack) >= 1:
    dict_size = op_stack.pop()
    if dict_size >= 0 and isinstance(dict_size, int):
      # cd = CustomDict(dict_size)
      op_stack.append(dict_size)
      op_stack.append({})
    else:  
      raise TypeMismatch("Dictionary size must be an integer and positive")
  else:
    raise TypeMismatch("Not enough operands for operation dict")
  
dict_stack[-1]["dict"] = dict_operation
  
# length dictionary and string operation
def length_operation():
  if len(op_stack) >= 1:
    dictionary = op_stack.pop() 
    if isinstance(dictionary, dict) or isinstance(dictionary, str):
      l = len(dictionary)
      op_stack.append(l)
    else:
      raise TypeMismatch("length operation expects a dictionary or a string")
  else:
    raise TypeMismatch("Not enough operands for operation length")
  
dict_stack[-1]["length"] = length_operation

# maxlength dictionary operation
def maxlength_operation():
  if len(op_stack) >= 1:
    dictionary = op_stack.pop()
    ml = op_stack.pop()
    if isinstance(dictionary, dict) and isinstance(ml, int):
      op_stack.append(ml)
      op_stack.append(dictionary)
      op_stack.append(ml)
    else:
      raise TypeMismatch("maxlength operation expects a dictionary")
  else:
    raise TypeMismatch("Not enough operands for operation maxlength")
  
dict_stack[-1]["maxlength"] = maxlength_operation

# begin dictionary operation
def begin_operation():
  if len(op_stack) >= 2:
    dictionary = op_stack.pop()
    ml = op_stack.pop()
    if isinstance(dictionary, dict):
      dict_stack.append(dictionary)
    else:
      raise TypeMismatch("begin operation expects a dictionary")
  else:
    raise TypeMismatch("Not enough operands for operation begin")

dict_stack[-1]["begin"] = begin_operation

# end dictionary operation
def end_operation():
  if len(dict_stack) > 1:
    dict_stack.pop()
  else:
    raise TypeMismatch("Not enough operands in dict_stack for operation end")

dict_stack[-1]["end"] = end_operation

# def dictionary operation
def def_operation():
  if len(op_stack) >= 2:
    value = op_stack.pop()
    name = op_stack.pop()
    if isinstance(name, str) and name.startswith("/"):
      key = name[1:]
      dict_stack[-1][key] = value
    else:
      op_stack.append(name)
      op_stack.append(value)
  else:
    raise TypeMismatch("Not enough operands for operation add")
  
dict_stack[-1]["def"] = def_operation

# ----- STRING OPERATIONS -----

# length string operation (go to DICTIONARY OPERATIONS)

# get string operation
def get_operation():
  if len(op_stack) >= 2:
    index = op_stack.pop()
    string = op_stack.pop()
    if isinstance(index, int) and isinstance(string, str):
      if 0 <= index and index < len(string):
        res = string[index]
        op_stack.append(res)
      else:
        raise TypeMismatch("Index is out of range")
    else:
      raise TypeMismatch("get operation expects a string and integer")
  else:
    raise TypeMismatch("Not enough operands for operation get")

dict_stack[-1]["get"] = get_operation

# getinterval string operation
def getinterval_operation():
  if len(op_stack) >= 3:
    count = op_stack.pop()
    index = op_stack.pop()
    string = op_stack.pop()
    if isinstance(count, int) and isinstance(index, int) and isinstance(string, str):
      if 0 <= (index + count) and (index + count) < len(string):
        interval = string[index:(index + count)]
        op_stack.append(interval)
      else:
        raise TypeMismatch("Index and/or count is out of range")
    else:
      raise TypeMismatch("getinterval operation expects a string and two integers")
  else:
    raise TypeMismatch("Not enough operands for operation getinterval")

dict_stack[-1]["getinterval"] = getinterval_operation

# putinterval string function
def putinterval_operation():
  if len(op_stack) >= 3:
    string2 = op_stack.pop()
    index = op_stack.pop()
    string1 = op_stack.pop()
    if isinstance(string2, str) and isinstance(index, int) and isinstance(string1, str):
      if 0 <= index and index < len(string1):
        new_string = string1[:index] + string2 + string1[index + len(string2):]
        op_stack.append(new_string)
      else:
        raise TypeMismatch("Index is out of range")
    else:
      raise TypeMismatch("getinterval operation expects a string, an index, and another string")
  else:
    raise TypeMismatch("Not enough operands for operation putinterval")

dict_stack[-1]["putinterval"] = putinterval_operation

# ----- BIT AND BOOLEAN OPERATIONS -----

# eq boolean operation
def eq_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op1 == op2
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation eq")

dict_stack[-1]["eq"] = eq_operation

# ne boolean operation
def ne_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op1 != op2
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation ne")

dict_stack[-1]["ne"] = ne_operation

# ge boolean operation
def ge_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op2 >= op1
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation ge")

dict_stack[-1]["ge"] = ge_operation

# gt boolean operation
def gt_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op2 > op1
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation gt")

dict_stack[-1]["gt"] = gt_operation

# le boolean operation
def le_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op2 <= op1
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation le")

dict_stack[-1]["le"] = le_operation

# lt boolean operation
def lt_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    res = op2 < op1
    op_stack.append(res)
  else:
    raise TypeMismatch("Not enough operands for operation lt")

dict_stack[-1]["lt"] = lt_operation

# and bitwise operation
def and_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, int) and isinstance(op2, int):
      res = op2 & op1
      op_stack.append(res)
    elif isinstance(op1, bool) and isinstance(op2, bool):
      res = op2 and op1
      op_stack.append(res)
    else: 
      raise TypeMismatch("Operands for operation and must be either int or bool")
  else:
    raise TypeMismatch("Not enough operands for operation and")

dict_stack[-1]["and"] = and_operation

# not bitwise operation
def not_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, int):
      res = ~op1
      op_stack.append(res)
    elif isinstance(op1, bool):
      res = not op1
      op_stack.append(res)
    else: 
      raise TypeMismatch("Operands for operation not must be either int or bool")
  else:
    raise TypeMismatch("Not enough operands for operation not")

dict_stack[-1]["not"] = not_operation

# or bitwise operation
def or_operation():
  if len(op_stack) >= 2:
    op1 = op_stack.pop()
    op2 = op_stack.pop()
    if isinstance(op1, int) and isinstance(op2, int):
      res = op2 | op1
      op_stack.append(res)
    elif isinstance(op1, bool) and isinstance(op2, bool):
      res = op2 or op1
      op_stack.append(res)
    else: 
      raise TypeMismatch("Operands for operation or must be either int or bool")
  else:
    raise TypeMismatch("Not enough operands for operation or")

dict_stack[-1]["or"] = or_operation

def true_operation():
  op_stack.append(True)

dict_stack[-1]["true"] = true_operation

def false_operation():
  op_stack.append(False)

dict_stack[-1]["false"] = false_operation

# ----- FLOW CONTROL OPERATIONS -----

# if operation
def if_operation():
  if len(op_stack) >= 2:
    proc = op_stack.pop()
    bool_val = op_stack.pop()
    # if isinstance(bool_val, bool) and isinstance(proc, list):
    if isinstance(bool_val, bool):
      if bool_val == True:
        if isinstance(proc, tuple): 
          tokens, environment = proc
          dict_stack.append(environment)
          for token in tokens:
            process_input(token)
          dict_stack.pop()
        else: 
          for token in proc:
            process_input(token)
          '''
          for token in proc:
            process_input(token)
          '''
    else:
      raise TypeMismatch("Operands for operation if must be a boolean and a list")
  else:
    raise TypeMismatch("Not enough operands for operation if")

dict_stack[-1]["if"] = if_operation

# ifelse operation
def ifelse_operation():
  if len(op_stack) >= 3:
    proc2 = op_stack.pop()
    proc1 = op_stack.pop()
    bool_val = op_stack.pop()
    if isinstance(bool_val, bool) and isinstance(proc1, list) and isinstance(proc2, list):
      right_proc = []
      if bool_val == True:
        right_proc = proc1
      else:
        right_proc = proc2
      for token in right_proc:
        process_input(token)
    else:
      raise TypeMismatch("Operands for operation ifelse must be a boolean and two lists")
  else:
    raise TypeMismatch("Not enough operands for operation ifelse")

dict_stack[-1]["ifelse"] = ifelse_operation

# for operation
def for_operation():
  if len(op_stack) >= 4:
    proc = op_stack.pop()
    l = op_stack.pop()
    k = op_stack.pop()
    j = op_stack.pop()
    if isinstance(proc, list) and isinstance(l, int) and isinstance(k, int) and isinstance(j, int):
      if (k == 0 and j != l):
        raise TypeMismatch("The k value must be greater than one if j != l")
      num_loops = int((l - j) / k) + 1
      for i in range(num_loops):
        cur = j + (i * k)
        op_stack.append(cur)
        for token in proc:
          process_input(token)
    else:
      raise TypeMismatch("Operands for operation ifelse must be three integers and a list")
  else:
    raise TypeMismatch("Not enough operands for operation for")

dict_stack[-1]["for"] = for_operation

# repeat operation
def repeat_operation():
  if len(op_stack) >= 2:
    proc = op_stack.pop()
    n = op_stack.pop()
    if isinstance(proc, list) and isinstance(n, int):
      for i in range(n):
        for token in proc:
          process_input(token)
    else:
      raise TypeMismatch("Operands for operation repeate must be a list and an integer")  
  else:
    raise TypeMismatch("Not enough operands for operation repeat")

dict_stack[-1]["repeat"] = repeat_operation

# quit operation
def quit_operation():
  exit()

dict_stack[-1]["quit"] = quit_operation

# ----- INPUT AND OUTPUT OPERATIONS -----

# print operation
def print_operation():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, str):
      print(op1, end='')
    else:
      raise TypeMismatch("Operands for operation print must be a string")
  else:
    raise TypeMismatch("Stack is empty! Nothing to print")

dict_stack[-1]["print"] = print_operation

# '=' operation
def pop_and_print():
  if (len(op_stack) >= 1):
    op1 = op_stack.pop()
    print(op1)
  else:
    raise TypeMismatch("Stack is empty! Nothing to print")

dict_stack[-1]["="] = pop_and_print

# '==' operation
def pop_and_print2():
  if len(op_stack) >= 1:
    op1 = op_stack.pop()
    if isinstance(op1, str):
      print(f"({op1})")
    else:
      print(op1)
  else:
    raise TypeMismatch("Stack is empty! Nothing to print")

dict_stack[-1]["=="] = pop_and_print2

# main function
if __name__ == "__main__":
  repl()