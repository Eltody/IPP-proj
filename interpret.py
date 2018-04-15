#!/usr/bin/env python3

"""IPPcode18 language interpret
@author Jiri Furda (xfurda00)
"""


# Libraries
import sys
import xml.etree.ElementTree as ET
import re
import logging


# === Debug logs ===
logger = logging.getLogger("interpret")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel("CRITICAL")


# === Main function ===
def main():
	filePath = processProgramArguments()

	logger.debug("==================================\nfile: {0}\n==============================\n".format(filePath))
	
	# --- Opening input file ---
	try:
		tree = ET.ElementTree(file=filePath)	# @todo Throws error when no root found
	except IOError:
		Error.exit(Error.file, "Opening input file error")		
	except ET.ParseError:
		Error.exit(Error.structure, "No element found in the file")		


	# --- Checking root node ---
	root = tree.getroot()
	# @todo check if root not found???
	
	if root.tag != "program":
		Error.exit(Error.structure, "Root node <program> not found")
		
	if "language" in root.attrib:
		if root.attrib["language"].lower() != "ippcode18":
			Error.exit(Error.syntax, "Invalid language attribute")
		del root.attrib["language"]
	else:
		Error.exit(Error.structure, "Language attribute missing")
		
	if "name" in root.attrib:
		del root.attrib["name"]
	if "description" in root.attrib:
		del root.attrib["description"]
		
	if len(root.attrib) != 0:
		Error.exit(Error.structure, "Invalid <program> attributes")
		
		
	# --- Processing instructions ---
	global interpret
	interpret = Interpret()
	interpret.loadInstructions(root)
	
	
	# --- Successful end ---
	sys.exit(0)
		
		
# === Other functions ===
def processProgramArguments():
	if len(sys.argv) != 2:
		Error.exit(Error.argument, "Invalid argument count")
	
	if sys.argv[1] == "--help":
		print("This program interprets code in language IPPcode18 parsed to XML")
		sys.exit(0)
	elif sys.argv[1][:9] == "--source=":
		return sys.argv[1][9:]	
	else:
		Error.exit(Error.argument, "Invalid argument")
		
		
# === Classes ===		
class Error:
	argument = 10
	file = 11
	
	structure = 31
	syntax = 32
	
	semantic = 52
	operands = 53
	varExistence = 54
	scopeExistence = 55
	missingValue = 56
	zeroDivide = 57
	string = 58	
	
	custom = 59
	
	internal = 99
	
	@staticmethod
	def exit(code, msg):
		print("ERROR: {0}".format(msg), file=sys.stderr)
		#print(code)
		sys.exit(code)
		

class Frames:
	globalFrame = {}
	localFrame = None
	temporaryFrame = None
	stack = []
	
	@classmethod
	def add(cls, name):
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Check for duplicity ---
		if name in frame:
			Error.exit(Error.custom, "Variable '{0}' already exist in global frame".format(name))
		
		# --- Create var in frame ---
		frame[name] = None;


	@classmethod
	def set(cls, name, value):
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Check if exists ---
		if name not in frame:
			Error.exit(Error.varExistence, "Coudn't set value to non-existing variable '{0}'".format(name))
		
		# --- Get actual value ---
		if type(value) == var:	# If trying to add var (e.g. MOVE GF@aaa GF@bbb)
			value = value.getValue()	# Save its value not whole object
			
		# --- Save value to frame ---
		frame[name] = value;
		
		
	@classmethod	
	def get(cls, name):
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Check if exists ---
		if name not in frame:
			Error.exit(Error.varExistence, "Variable '{0}' does not exist".format(name))
		
		# --- Get value from frame ---
		result = frame[name]
		
		# --- Check if initialized ---
		if type(result) == type(None):
			Error.exit(Error.missingValue, "Tried to get non-initilaized value")
		
		# --- Result ---
		return result;		
	
	
	@classmethod
	def __identifyFrame(cls, name):
		if name[:3] == "GF@":
			frame = cls.globalFrame
			
		elif name[:3] == "LF@":
			frame = cls.localFrame
			
		elif name[:3] == "TF@":
			frame = cls.temporaryFrame
			
		else:
			Error.exit(Error.syntax, "Invalid frame prefix") # Maybe should be Error.internal because it should be chceked in Instruction.__loadArguments()

		if frame == None:
			Error.exit(Error.scopeExistence, "Cannot access not initialized frame")
			

		return frame

class Stack:
	"""Stack for values in IPPcode18"""
	def __init__(self):
		self.content = []
		
	def pop(self, dest):
		if len(self.content) == 0:
			Error.exit(Error.missingValue, "Cannot pop empty stack")
			
		if type(dest) != var:
			Error.exit(Error.operands, "Cannot pop to non-variable")
		
		value = self.content.pop()	# Pop top of the stack
		
		dest.setValue(value)	# Set the value
		
		
	def push(self, value):
		self.content.append(value)


class CallStack:	# @todo merge with classicStack
	content = []
	
	@classmethod
	def push(cls, value):
		cls.content.append(value)
	
	@classmethod	
	def pop(cls):
		if len(cls.content) == 0:
			Error.exit(Error.missingValue, "Cannot pop empty call stack")
			
		return cls.content.pop()
		
	
		
		
class Labels:
	labels = {}
	
	@classmethod	
	def add(cls, name):
		name = str(name)	# Convert type label to str
		
		if name in cls.labels:
			Error.exit(Error.semantic, "Label '{0}' already exists".format(name))
			
		cls.labels[name] = interpret.instrOrder
	
	@classmethod	
	def jump(cls, name):
		name = str(name)	# Convert type label to str
		
		if name not in cls.labels:
			Error.exit(Error.semantic, "Label '{0}' does not exist".format(name))
			
		interpret.instrOrder = cls.labels[name]
		
		
class var:
	def __init__(self, name):
		self.name = name	
		
	def getValue(self):
		"""Returns value stored in var"""
		return Frames.get(self.getName())

	def getName(self):
		"""Returns name of var including frame prefix"""
		return self.name
	
	def setValue(self, value):
		Frames.set(self.getName(), value)
			
	
	# == Actual value convert method ==
	def __str__(self):
		value = self.getValue()
		
		if type(value) != str:
			Error.exit(Error.internal, "Cannot convert non-string variable to string")
			
		return value
		
	def __int__(self):
		value = self.getValue()
		
		if type(value) != int:
			Error.exit(Error.internal, "Cannot convert non-string variable to int")
			
		return value
	
	def __bool__(self):
		value = self.getValue()
		
		if type(value) != bool:
			Error.exit(Error.internal, "Cannot convert non-string variable to bool")
			
		return value	
		
		
class symb:
	"""Dummy class representing str, int, bool or var in instruction.checkArgumentes()"""
	pass
	
class label:
	def __init__(self, name):
		self.name = name
	
	def __str__(self):
		return self.name
		
				
	
class Interpret():
	def __init__(self):
		self.instrOrder = 1
		self.stack = Stack()
		
	def loadInstructions(self, root):
		# --- Search all nodes ---
		instrNodes = root.findall("./")
		instrNodesCount = len(instrNodes)
		
		# --- Search for LABEL nodes ---
		self.__findLabels(instrNodes)
		self.instrOrder = 1	# Reset instruction counter
			
		# --- Cycle throught every node ---
		while self.instrOrder <= instrNodesCount:	# Watchout! instrOrder starts at 1
			# -- Get current node --
			node = instrNodes[self.instrOrder-1]
			
			# -- Skip LABEL nodes --
			if node.attrib["opcode"].upper() == "LABEL":
				self.instrOrder = self.instrOrder+1
				continue	# They are already loaded by __findLabels()
			
			# -- Debug info --
			logger.debug("=============")
			logger.debug("{0} {1} ".format(node.tag, node.attrib))
			for arg in node:
				logger.debug("{0} {1} {2}".format(arg.tag, arg.attrib,arg.text))
			
			# -- Processing instruction --
			instruction = Instruction(node)
			instruction.execute()
			
			# -- Add counter --
			self.instrOrder = self.instrOrder+1
	
	
	def __findLabels(self, instrNodes):
		"""Search every label instruction used and saves it"""
		for node in instrNodes:
			if node.attrib["opcode"].upper() == "LABEL":
				self.instrOrder = int(node.attrib["order"])	# This is read from Labels.add
				instruction = Instruction(node)
				instruction.execute()
				
		
	
	def convertValue(self, xmlType, xmlValue, die):
		"""Converts XML value (str in python) to actual type (int, str, bool or var)
		Paremetr die accepts bool value and determines if conversion is strict and exit program upon fail
		or it returns defalt value"""
		
		# --- Variable type ---
		if xmlType == "var":
			if not re.search(r"^(LF|TF|GF)@[\w_\-$&%*][\w\d_\-$&%*]*$", xmlValue):
				Error.Exit(Error.syntax, "Invalid var name")
				
			return var(xmlValue)
		
		# --- Integer type ---		
		elif xmlType == "int":
			if not re.search(r"^[-+]?\d+$$", xmlValue):
				if die == True:
					Error.Exit(Error.syntax, "Invalid int value")
				else:
					return 0
			
			return int(xmlValue)	# Convert str to int	
			
		# --- String type ---
		elif xmlType == "string":
			# -- Check empty string --
			if xmlValue == None:
				xmlValue = ""
			
			if re.search(r"(?!\\[0-9]{3})[\s\\#]", xmlValue):	# @see parse.php for regex legend
				if die == True:
					Error.Exit(Error.syntax, "Illegal characters in string")
				else:
					return ""
			
			# -- Search escape sequences --
			groups = re.findall(r"\\([0-9]{3})", xmlValue)	# Find escape sequences
			groups = list(set(groups))	# Remove duplicates
			
			# -- Decode escape sqeuences --
			for group in groups:
				if group == "092":	# Special case for \ (I don't even know why)
					xmlValue = re.sub("\\\\092", "\\\\", xmlValue)
					continue
				xmlValue = re.sub("\\\\{0}".format(group), chr(int(group)), xmlValue)
			
			# -- Return decoded string --
			return xmlValue
		
		# --- Boolean type ---
		elif xmlType == "bool":
			if xmlValue == "true":
				boolean = True
			elif xmlValue == "false":
				boolean = False
			else:
				if die == True:
					Error.Exit(Error.syntax, "Invalid bool value (given {0})".format(xmlValue))
				else:
					return False
			
			return boolean
			
		# --- Type type ---
		if xmlType == "type":
			if not re.search(r"^(int|string|bool)$", xmlValue):
				Error.Exit(Error.syntax, "Invalid type value")
				
			return xmlValue
			
		# --- Type label ---
		if xmlType == "label":
			if not re.search(r"^[\w_\-$&%*][\w\d_\-$&%*]*$", xmlValue):
				Error.Exit(Error.syntax, "Invalid label name")
				
			return label(xmlValue)	
			
		# --- Invalid type ---
		else:
			Error.Exit(Error.syntax, "Unknown argument type (given {0})".format(xmlType))
	
	
	
class Instruction():
	def __init__(self, node):
		'''Initialization of internal strcture of XML <instruction> node'''
		
		# --- Check node ---
		if node.tag != "instruction":
			Error.exit(Error.structure, "Wrong node loaded (Expected instruction)")
		
		# --- Order check ---
		if int(node.attrib["order"]) != interpret.instrOrder:
			Error.exit(Error.structure, "Wrong instruction order")
		
		# --- Process node ---
		self.opCode = node.attrib["opcode"].upper()	
		self.args = self.__loadArguments(node)
		self.argCount = len(self.args)
		
		
	def __loadArguments(self, instrNode):	
		'''Loads child nodes (<argX>) of <instruction> node'''
		args = [None] * len(instrNode)
		
		
		# --- Load child nodes ---	
		for argNode in instrNode:
			if argNode.tag[:3] != "arg":
				Error.exit(Error.structure, "Wrong node loaded (expected arg node given)")

			# -- Get arg index --
			argIndex = int(argNode.tag[3:])-1
			
			if argIndex > len(args):
				Error.exit(Error.structure, "Argument node out of range")
			
			if args[argIndex] != None:
				Error.exit(Error.structure, "Duplicated argument node")
		
			# --- Save arg value ---
			args[argIndex] = interpret.convertValue(argNode.attrib["type"], argNode.text, True)
		
		# --- Check if loaded all ---	
		for arg in args:
			if arg == None:
				Error.exit(Error.structure, "Argument node not loaded")
		
		# --- Return loaded arguments ---
		return(args)
	
	
	def __checkArguments(self, *expectedArgs):		
		# --- Checking arguments count ---
		if self.argCount != len(expectedArgs):
			Error.exit(Error.semantic, "Invalid argument count")
			
		# --- Converting tuple to list ---
		expectedArgs = list(expectedArgs)	
			
		# --- Checking arguments type ---
		i = 0;
		for arg in self.args: # Check every argument
			# -- Replacing <symb> --
			if expectedArgs[i] == symb:
				expectedArgs[i] = [int, bool, str, var]
			
			
			argType = type(arg)	# Saved argument's type
			
			# -- Only one allowed type --
			if type(expectedArgs[i]) == type:
				if argType != expectedArgs[i]:
					Error.exit(Error.operands, "Invalid argument type (expected {0} given {1})".format(expectedArgs[i],argType))
					
			# -- More allowed types --
			elif type(expectedArgs[i]) == list:
				if argType not in expectedArgs[i]:	# Check if used argument has one of expected types
					Error.exit(Error.operands, "Invalid argument type (expected {0} given {1})".format(expectedArgs[i],argType))
					
			# -- Wrong method parameters --
			else:
				Error.exit(Error.internal, "Illegal usage of Instruction.checkArguments()")
				
			i = i+1
		
	
	def execute(self):
		if self.opCode == "DEFVAR":
			self.DEFVAR()
		elif self.opCode == "ADD":
			self.ADD()
		elif self.opCode == "SUB":
			self.SUB()
		elif self.opCode == "MUL":
			self.MUL()
		elif self.opCode == "IDIV":
			self.IDIV()
		elif self.opCode == "WRITE":
			self.WRITE()
		elif self.opCode == "MOVE":
			self.MOVE()
		elif self.opCode == "PUSHS":
			self.PUSHS()
		elif self.opCode == "POPS":
			self.POPS()
		elif self.opCode == "STRLEN":
			self.STRLEN()
		elif self.opCode == "CONCAT":
			self.CONCAT()
		elif self.opCode == "GETCHAR":
			self.GETCHAR()
		elif self.opCode == "SETCHAR":
			self.SETCHAR()
		elif self.opCode == "TYPE":
			self.TYPE()
		elif self.opCode == "AND":
			self.AND()
		elif self.opCode == "OR":
			self.OR()
		elif self.opCode == "NOT":
			self.NOT()
		elif self.opCode == "LT" or self.opCode == "EQ" or self.opCode == "GT":
			self.LT_EQ_GT(self.opCode)
		elif self.opCode == "INT2CHAR":
			self.INT2CHAR()
		elif self.opCode == "STRI2INT":
			self.STRI2INT()
		elif self.opCode == "READ":
			self.READ()
		elif self.opCode == "LABEL":	# Called from Interpret.__findLabels()
			self.LABEL()	
		elif self.opCode == "JUMP":
			self.JUMP()
		elif self.opCode == "JUMPIFEQ":
			self.JUMPIFEQ_JUMPIFNEQ(True)
		elif self.opCode == "JUMPIFNEQ":
			self.JUMPIFEQ_JUMPIFNEQ(False)		
		elif self.opCode == "DPRINT" or self.opCode == "BREAK":
			pass
		elif self.opCode == "CREATEFRAME":
			self.CREATEFRAME()
		elif self.opCode == "PUSHFRAME":
			self.PUSHFRAME()
		elif self.opCode == "POPFRAME":
			self.POPFRAME()
		elif self.opCode == "CALL":
			self.CALL()
		elif self.opCode == "RETURN":
			self.RETURN()
		else:	# @todo more instructions
			Error.exit(Error.syntax, "Unknown instruction code")	
	
	
	# === IPPcode18 methods ===
		
	# --- Instrcution DEFVAR ---
	def DEFVAR(self):
		self.__checkArguments(var)
		
		Frames.add(self.args[0].getName())	
		
		
	# --- Instrcution ADD ---
	def ADD(self):
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) + int(self.args[2])	
		self.args[0].setValue(result)
		
		
	# --- Instrcution SUB ---
	def SUB(self):
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) - int(self.args[2])	
		self.args[0].setValue(result)

		
	# --- Instrcution ADD ---
	def MUL(self):
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) * int(self.args[2])	
		self.args[0].setValue(result)
		
		
	# --- Instrcution ADD ---
	def IDIV(self):
		self.__checkArguments(var, [int, var], [int, var])

		# -- Check for zero divide --
		if int(self.args[2]) == 0:
			Error.exit(Error.zeroDivide, "Tried to divide by zero")

		result = int(self.args[1]) // int(self.args[2])	
		
		self.args[0].setValue(result)
		
		
	# --- Instrcution WRITE ---
	def WRITE(self):
		self.__checkArguments(symb)
	
		# --- Get value stored in var ---
		if type(self.args[0]) == var:
			value = self.args[0].getValue()
		else:
			value = self.args[0]

		# --- Prepare print for bool ---
		if type(value) == bool:
			if value == True:
				value = "true"
			else:
				value = "false"
		
		result = str(value)
			
		print(result)


	# --- Instrcution MOVE ---
	def MOVE(self):
		self.__checkArguments(var, symb)
		
		self.args[0].setValue(self.args[1])
		
		
	# --- Instrcution PUSHS ---
	def PUSHS(self):
		self.__checkArguments(symb)
	
		interpret.stack.push(self.args[0])


	# --- Instrcution POPS ---
	def POPS(self):
		self.__checkArguments(var)
	
		interpret.stack.pop(self.args[0])
		
		
	# --- Instrcution STRLEN ---
	def STRLEN(self):
		self.__checkArguments(var, [str, var])
		
		result = len(str(self.args[1]))
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution CONCAT ---
	def CONCAT(self):
		self.__checkArguments(var, [str, var], [str, var])
	
		result = str(self.args[1]) + str(self.args[2])
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution GETCHAR ---
	def GETCHAR(self):
		self.__checkArguments(var, [str, var], [int, var])
	
		string = str(self.args[1])
		position = int(self.args[2])
		
		if position >= len(string):
			Error.exit(Error.string, "GETCHAR/STRI2INT position out of range")
		
		result = string[position]
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution GETCHAR ---
	def SETCHAR(self):
		self.__checkArguments(var, [int, var], [str, var])
	
		string = str(self.args[0])
		position = int(self.args[1])
		character = str(self.args[2])
		
		if position >= len(string):
			Error.exit(Error.string, "SETCHAR position out of range")
		if len(character) == 0:
			Error.exit(Error.string, "SETCHAR replacement character not given")
		
		result = string[:position] + character[0] + string[position+1:]
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution TYPE ---	
	def TYPE(self):
		self.__checkArguments(var, symb)
		
		# -- Get value inside var --
		if type(self.args[1]) == var:
			value = self.args[1].getValue()
		else:
			value = self.args[1]
		
		# -- Convert value type name to str --	
		valueType = re.search(r"<class '(str|bool|int)'>", str(type(value))).group(1)
		
		# -- Rename str to string --
		if valueType == "str":
			result = "string"
		else:
			result = valueType
			
		# -- Save value --
		self.args[0].setValue(result)


	# --- Instrcution AND ---	
	def AND(self):
		self.__checkArguments(var, [bool, var], [bool, var])
		
		result = bool(self.args[1]) and bool(self.args[2])
		
		self.args[0].setValue(result)
		
		
	# --- Instrcution OR ---	
	def OR(self):
		self.__checkArguments(var, [bool, var], [bool, var])
		
		result = bool(self.args[1]) or bool(self.args[2])
		
		self.args[0].setValue(result)


	# --- Instrcution NOT ---	
	def NOT(self):
		self.__checkArguments(var, [bool, var])
		
		result = not bool(self.args[1])
		
		self.args[0].setValue(result)
		
		
	# --- Instrcution LT/EQ/GT ---	
	def LT_EQ_GT(self, operation):
		self.__checkArguments(var, symb, symb)
		
		# -- Get values inside var --
		if type(self.args[1]) == var:
			valueA = self.args[1].getValue()
		else:
			valueA = self.args[1]
			
		if type(self.args[2]) == var:
			valueB = self.args[2].getValue()
		else:
			valueB = self.args[2]
		
		# -- Check for same type --
		if type(valueA) != type(valueB):
			Error.exit(Error.operands, "Can't compare different types")
		
		# -- Compare values --
		if opreation == "LT":
			result = valueA < valueB
		elif operation == "EQ":
			result = valueA == valueB
		elif operation == "GT":
			result = valueA > valueB
		else:
			Error.exit(Error.internal, "Invalid operation in Instruction.LT_EQ_GT")
					
		# -- Save result --
		self.args[0].setValue(result)
		
		
	# --- Instrcution INT2CHAR ---	
	def INT2CHAR(self):
		self.__checkArguments(var, [int, var])
		
		value = int(self.args[1])
		
		try:
			result = chr(value)
		except ValueError:
			Error.exit(Error.string, "INT2CHAR invalid character code")
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution STRI2INT ---	
	def STRI2INT(self):
		self.GETCHAR()	# Too lazy
		
		result = ord(self.args[0].getValue())
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution READ ---	
	def READ(self):
		self.__checkArguments(var, str)	# Should be <var> <type> but I'm going to bed
		
		inputStr = input()
		
		# -- Bool input special rules --
		inputStr = inputStr.lower()
		
		# -- Convert input type --
		result = interpret.convertValue(self.args[1], inputStr, False)
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution LABEL ---	
	def LABEL(self):	# Called from Interpret.__findLabels()
		self.__checkArguments(label)
		
		Labels.add(self.args[0])


	# --- Instrcution JUMP ---	
	def JUMP(self):
		self.__checkArguments(label)
		
		Labels.jump(self.args[0])
		
		
	# --- Instrcutions JUMPIFEQ & JUMPIFNEQ ---	
	def JUMPIFEQ_JUMPIFNEQ(self, expectedResult):
		self.__checkArguments(label, symb, symb)
		
		# -- Get values inside var --
		if type(self.args[1]) == var:
			valueA = self.args[1].getValue()
		else:
			valueA = self.args[1]
			
		if type(self.args[2]) == var:
			valueB = self.args[2].getValue()
		else:
			valueB = self.args[2]
		
		# -- Check for same type --
		if type(valueA) != type(valueB):
			Error.exit(Error.operands, "Can't compare different types")
		
		# -- Compare values --
		result = valueA == valueB
		
		# -- Jump if condition is met --
		if result == expectedResult:
			Labels.jump(self.args[0])
			
			
	# --- Instrcution CREATEFRAME ---	
	def CREATEFRAME(self):
		self.__checkArguments()
		
		# -- Reset TF --
		Frames.temporaryFrame = {}
		
		
	# --- Instrcution PUSHFRAME ---	
	def PUSHFRAME(self):
		self.__checkArguments()
		
		if Frames.temporaryFrame == None:
			Error.exit(Error.scopeExistence, "Tried to access not defined frame")
		
		# -- Move TF to stack --
		Frames.stack.append(Frames.temporaryFrame)
		
		# -- Set LF --
		Frames.localFrame = Frames.stack[-1]	# LF = top of the stack (previously TF)
			
		# -- Reset TF --
		Frames.temporaryFrame == None
		
		
	# --- Instrcution POPFRAME ---	
	def POPFRAME(self):		
		self.__checkArguments()

		# -- Check if LF exists --		
		if Frames.localFrame == None:
			Error.exit(Error.scopeExistence, "Local frame not defined")
			
		# -- Set TF --
		Frames.temporaryFrame = Frames.stack.pop()	# TF = previous top of the stack (LF)
		
		# -- Reset LF --
		Frames.localFrame == None
		
		
	# --- Instrcution CALL ---	
	def CALL(self):		
		CallStack.push(interpret.instrOrder)
		
		self.JUMP()
		
		
	# --- Instrcution RETURN ---	
	def RETURN(self):	
		self.__checkArguments()
			
		interpret.instrOrder = CallStack.pop()	
		
		
main()
