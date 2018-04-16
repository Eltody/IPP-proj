#!/usr/bin/env python3

"""IPPcode18 language interpret
@author Jiri Furda (xfurda00)
"""


# Libraries
import sys
import xml.etree.ElementTree as ET
import re
import logging


# === Main function ===
def main():
	"""Main body of the interpret"""
	
	filePath = processProgramArguments()

	# --- Open input file ---
	try:
		tree = ET.ElementTree(file=filePath)
	except IOError:
		Error.exit(Error.file, "Opening input file error")		
	except ET.ParseError:
		Error.exit(Error.structure, "No element found in the file")		


	# --- Check root node ---
	root = tree.getroot()

		
	# --- Process instructions ---
	Interpret.loadInstructions(root)
	
	
	# --- Successful end ---
	sys.exit(0)
		
		
# === Other functions ===
def processProgramArguments():
	"""Checks and process interpret's start parameters
	Returns path to source file to be interpreted
	"""
	
	# --- Check argument count ---
	if len(sys.argv) != 2:
		Error.exit(Error.argument, "Invalid argument count")
	
	# --- Print argument "--help" ---
	if sys.argv[1] == "--help":
		print("This program interprets code in language IPPcode18 parsed to XML")
		print("Author: Jiri Furda (xfurda00)")
		print("Usage:")
		print("python3.6 interpret.py --source=<path to .src>")
		sys.exit(0)
		
	# --- Load arguemnt "--source" ---
	elif sys.argv[1][:9] == "--source=":
		return sys.argv[1][9:]	
		
	# --- Check illegal argument ---
	else:
		Error.exit(Error.argument, "Invalid argument")
		
		
# === Classes ===		
class Error:
	"""Class used to store error codes and to print them"""
	
	# Input errors
	argument = 10
	file = 11
	
	# Pre-run errors
	structure = 31
	syntax = 32
	
	# Running errors
	semantic = 52
	operands = 53
	varExistence = 54
	scopeExistence = 55
	missingValue = 56
	zeroDivide = 57
	string = 58	
	
	# Other errors
	custom = 59
	internal = 99
	
	
	@staticmethod
	def exit(code, msg):
		"""Prints error message to STDERR and ends with defined return code"""
		
		print("ERROR: {0}".format(msg), file=sys.stderr)
		sys.exit(code)
		

class Frames:
	"""Class working with IPPcode18 frames to store values (Global Frame, Local Frame and Temporary Frame)"""
	
	globalFrame = {}
	localFrame = None
	temporaryFrame = None
	stack = []	# Stack used to store temporary frames when PUSHFRAME and POPFRAME is called	
	
	
	@classmethod
	def add(cls, name):
		"""Creates new variable in the frame defined in its name"""
		
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Remove frame prefix ---
		name = name[3:]
		
		# --- Check for duplicity ---
		if name in frame:
			Error.exit(Error.custom, "Variable '{0}' already exist in global frame".format(name))
		
		# --- Create var in frame ---
		frame[name] = None;


	@classmethod
	def set(cls, name, value):
		"""Sets value to variable stored in certain frame"""
		
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Remove frame prefix ---
		name = name[3:]
		
		# --- Check if exists ---
		if name not in frame:
			Error.exit(Error.varExistence, "Couldn't set value to non-existing variable '{0}'".format(name))
		
		# --- Get actual value ---
		if type(value) == var:	# If trying to add var (e.g. MOVE GF@aaa GF@bbb)
			value = value.getValue()	# Save its value not whole object
			
		# --- Save value to frame ---
		frame[name] = value;
		
		
	@classmethod	
	def get(cls, name):
		"""Returns value of variable stored in certain frame"""
		
		# --- Identify frame ---
		frame = cls.__identifyFrame(name)
		
		# --- Remove frame prefix ---
		name = name[3:]
		
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
		"""Returns specific frame depending on preffix (e.g. GF@) in variable name"""
		
		# --- Find certain frame ---
		if name[:3] == "GF@":
			frame = cls.globalFrame
			
		elif name[:3] == "LF@":
			frame = cls.localFrame
			
		elif name[:3] == "TF@":
			frame = cls.temporaryFrame
		
		# --- Check for invalid frame ---	
		else:
			Error.exit(Error.syntax, "Invalid frame prefix") # Maybe should be Error.internal because it should be already chceked in Instruction.__loadArguments()

		# --- Check for not initialized frame ---
		if frame == None:
			Error.exit(Error.scopeExistence, "Cannot access not initialized frame")

		# --- Result frame ---
		return frame


class Stack:
	"""Class used for stack (values and calls)"""
	
	def __init__(self):
		"""Creates empty list for stack"""
		
		self.content = []
		
		
	def pop(self):
		"""Pops value on top of the stack"""
		
		# --- Check for empty stack ---
		if len(self.content) == 0:
			Error.exit(Error.missingValue, "Cannot pop empty stack")

		# --- Pop value ---
		return self.content.pop()
		
		
	def push(self, value):
		"""Pushes value to the stack"""
		
		self.content.append(value)	
		
		
class Labels:
	"""Class used to store IPPcode18 labels and to jump to them"""
	
	labels = {}
	
	
	@classmethod	
	def add(cls, name):
		"""Saves new label and its value"""
		
		# --- Convert type label to str ---
		name = str(name)	
		
		# --- Check for duplicity ---
		if name in cls.labels:
			Error.exit(Error.semantic, "Label '{0}' already exists".format(name))
			
		# --- Save label ---
		cls.labels[name] = Interpret.instrOrder
	
	
	@classmethod	
	def jump(cls, name):
		"""Jump interpret reading to certain label"""
		
		# --- Convert type label to str ---
		name = str(name)	
		
		# --- Check for existence ---
		if name not in cls.labels:
			Error.exit(Error.semantic, "Label '{0}' does not exist".format(name))
			
		# --- Jump interpret reading to label ---
		Interpret.instrOrder = cls.labels[name]
		
		
class var:
	"""Class representing IPPcode18 type var"""
	
	def __init__(self, name):
		"""Sets name of var"""
		
		self.name = name	
		
		
	def getValue(self):
		"""Returns value stored inside var"""
		
		return Frames.get(self.getName())


	def getName(self):
		"""Returns name of var including frame prefix"""
		
		return self.name
	
	
	def setValue(self, value):
		"""Changes value stored inside var"""
		
		Frames.set(self.getName(), value)
			
	
	# == Actual value convert method ==
	def __getValueWithType(self, expectedType):
		"""Get value stored inside var and check its type"""
		
		# --- Get value stored in var ---
		value = self.getValue()
		
		# --- Check if value is really str ---
		if type(value) != expectedType:
			Error.exit(Error.internal, "Unexpected type stored inside variable")	# Internal because it should be checked by Instruction.__checkArguments()
			
		# --- Return result ---
		return value
		
	
	def __str__(self):
		"""Get str value stored inside var"""
		
		return self.__getValueWithType(str)
		
		
	def __int__(self):
		"""Get int value stored inside var"""
		
		return self.__getValueWithType(int)
	
	
	def __bool__(self):
		"""Get bool value stored inside var"""
		
		return self.__getValueWithType(bool)	
		
		
class symb:
	"""Dummy class representing str, int, bool or var in instruction.checkArguments()"""
	
	pass
	
class label:
	"""Class representing IPPcode18 type label"""
	
	def __init__(self, name):
		"""Sets name of the label"""
		
		self.name = name
	
	
	def __str__(self):
		"""Gets name of the label"""
		
		return self.name
				
	
class Interpret():
	"""Main class of this program. It represents the interpret itself"""
	
	instrOrder = 1	# Defines order number of instruction which is currently loaded
	valStack = Stack()	# Used by POPS and PUSHS
	callStack = Stack()	# Used by CALL and RETURN
	
	@staticmethod		
	def checkRoot(root):
		"""Checks if root node is valid"""
		
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
	
	
	@classmethod		
	def loadInstructions(cls, root):
		"""Loads all instruction nodes in source file and executes them"""
		
		# --- Search all nodes ---
		instrNodes = root.findall("./")
		instrNodesCount = len(instrNodes)
		
		# --- Search for LABEL nodes ---
		cls.__findLabels(instrNodes)
		cls.instrOrder = 1	# Reset instruction counter
			
		# --- Cycle throught every node ---
		while cls.instrOrder <= instrNodesCount:	# Watchout! instrOrder starts at 1
			# -- Get current node --
			node = instrNodes[cls.instrOrder-1]
			
			# -- Skip LABEL nodes --
			if node.attrib["opcode"].upper() == "LABEL":
				cls.instrOrder = cls.instrOrder+1
				continue	# They are already loaded by __findLabels()
			
			# -- Processing instruction --
			instruction = Instruction(node)
			instruction.execute()
			
			# -- Add counter --
			cls.instrOrder = cls.instrOrder+1
	
	
	@classmethod	
	def __findLabels(cls, instrNodes):
		"""Search every LABEL instruction used and saves it"""
		for node in instrNodes:
			if node.attrib["opcode"].upper() == "LABEL":
				cls.instrOrder = int(node.attrib["order"])	# This is read from Labels.add
				instruction = Instruction(node)
				instruction.execute()
				
		
	@staticmethod	
	def convertValue(xmlType, xmlValue, die):
		"""Converts XML value (str in python) to actual type (int, str, bool or var)
		Parameter die is bool value determining if program ends with error or if it
		reuturn default value when invalid input is given
		"""
		
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
	"""Class representing one IPPcode18 instruction"""
	
	def __init__(self, node):
		"""Initialization of internal strcture of XML <instruction> node"""
		
		# --- Check node ---
		if node.tag != "instruction":
			Error.exit(Error.structure, "Wrong node loaded (Expected instruction)")
		
		# --- Order check ---
		if int(node.attrib["order"]) != Interpret.instrOrder:
			Error.exit(Error.structure, "Wrong instruction order")
		
		# --- Process node ---
		self.opCode = node.attrib["opcode"].upper()	
		self.args = self.__loadArguments(node)
		self.argCount = len(self.args)
		
		
	def __loadArguments(self, instrNode):	
		"""Loads child nodes (<argX>) of <instruction> node"""
		
		# --- Create list for arguments ---
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
			args[argIndex] = Interpret.convertValue(argNode.attrib["type"], argNode.text, True)
		
		# --- Check if loaded all expected arguments ---	
		for arg in args:
			if arg == None:
				Error.exit(Error.structure, "Argument node missing")
		
		# --- Return loaded arguments ---
		return(args)
	
	
	def __checkArguments(self, *expectedArgs):	
		"""Checks if arguments have expected type"""
			
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
		"""Executes instruction depending on opCode"""
		
		if self.opCode == "DEFVAR":
			self.__DEFVAR()
		elif self.opCode == "ADD":
			self.__ADD()
		elif self.opCode == "SUB":
			self.__SUB()
		elif self.opCode == "MUL":
			self.__MUL()
		elif self.opCode == "IDIV":
			self.__IDIV()
		elif self.opCode == "WRITE":
			self.__WRITE()
		elif self.opCode == "MOVE":
			self.__MOVE()
		elif self.opCode == "PUSHS":
			self.__PUSHS()
		elif self.opCode == "POPS":
			self.__POPS()
		elif self.opCode == "STRLEN":
			self.__STRLEN()
		elif self.opCode == "CONCAT":
			self.__CONCAT()
		elif self.opCode == "GETCHAR":
			self.__GETCHAR()
		elif self.opCode == "SETCHAR":
			self.__SETCHAR()
		elif self.opCode == "TYPE":
			self.__TYPE()
		elif self.opCode == "AND":
			self.__AND()
		elif self.opCode == "OR":
			self.__OR()
		elif self.opCode == "NOT":
			self.__NOT()
		elif self.opCode == "LT" or self.opCode == "EQ" or self.opCode == "GT":
			self.__LT_EQ_GT(self.opCode)
		elif self.opCode == "INT2CHAR":
			self.__INT2CHAR()
		elif self.opCode == "STRI2INT":
			self.__STRI2INT()
		elif self.opCode == "READ":
			self.__READ()
		elif self.opCode == "LABEL":	# Called from Interpret.__findLabels()
			self.__LABEL()	
		elif self.opCode == "JUMP":
			self.__JUMP()
		elif self.opCode == "JUMPIFEQ":
			self.__JUMPIFEQ_JUMPIFNEQ(True)
		elif self.opCode == "JUMPIFNEQ":
			self.__JUMPIFEQ_JUMPIFNEQ(False)		
		elif self.opCode == "DPRINT" or self.opCode == "BREAK":
			pass
		elif self.opCode == "CREATEFRAME":
			self.__CREATEFRAME()
		elif self.opCode == "PUSHFRAME":
			self.__PUSHFRAME()
		elif self.opCode == "POPFRAME":
			self.__POPFRAME()
		elif self.opCode == "CALL":
			self.__CALL()
		elif self.opCode == "RETURN":
			self.__RETURN()
		else:
			Error.exit(Error.syntax, "Unknown instruction code")	
	
	
	# === IPPcode18 methods ===
		
	# --- Instrcution DEFVAR ---
	def __DEFVAR(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var)
		
		Frames.add(self.args[0].getName())	
		
		
	# --- Instrcution ADD ---
	def __ADD(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) + int(self.args[2])	
		self.args[0].setValue(result)
		
		
	# --- Instrcution SUB ---
	def __SUB(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) - int(self.args[2])	
		self.args[0].setValue(result)

		
	# --- Instrcution ADD ---
	def __MUL(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = int(self.args[1]) * int(self.args[2])	
		self.args[0].setValue(result)
		
		
	# --- Instrcution ADD ---
	def __IDIV(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [int, var], [int, var])

		# -- Check for zero divide --
		if int(self.args[2]) == 0:
			Error.exit(Error.zeroDivide, "Tried to divide by zero")

		# -- Count and save result --
		result = int(self.args[1]) // int(self.args[2])	
		self.args[0].setValue(result)
		
		
	# --- Instrcution WRITE ---
	def __WRITE(self):
		"""@see zadani.pdf"""
		
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
		
		# --- Print result ---	
		result = str(value)
		print(result)


	# --- Instrcution MOVE ---
	def __MOVE(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, symb)
		
		self.args[0].setValue(self.args[1])
		
		
	# --- Instrcution PUSHS ---
	def __PUSHS(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(symb)
	
		Interpret.valStack.push(self.args[0])


	# --- Instrcution POPS ---
	def __POPS(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var)
	
		value = Interpret.valStack.pop()
		
		self.args[0].setValue(value)
		
		
	# --- Instrcution STRLEN ---
	def __STRLEN(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [str, var])
		
		result = len(str(self.args[1]))
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution CONCAT ---
	def __CONCAT(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [str, var], [str, var])
	
		result = str(self.args[1]) + str(self.args[2])
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution GETCHAR ---
	def __GETCHAR(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [str, var], [int, var])
	
		string = str(self.args[1])
		position = int(self.args[2])
		
		if position >= len(string):
			Error.exit(Error.string, "GETCHAR/STRI2INT position out of range")
		
		result = string[position]
	
		self.args[0].setValue(result)
		
		
	# --- Instrcution GETCHAR ---
	def __SETCHAR(self):
		"""@see zadani.pdf"""
		
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
	def __TYPE(self):
		"""@see zadani.pdf"""
		
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
	def __AND(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [bool, var], [bool, var])
		
		result = bool(self.args[1]) and bool(self.args[2])
		
		self.args[0].setValue(result)
		
		
	# --- Instrcution OR ---	
	def __OR(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [bool, var], [bool, var])
		
		result = bool(self.args[1]) or bool(self.args[2])
		
		self.args[0].setValue(result)


	# --- Instrcution NOT ---	
	def __NOT(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [bool, var])
		
		result = not bool(self.args[1])
		
		self.args[0].setValue(result)
		
		
	# --- Instrcution LT/EQ/GT ---	
	def __LT_EQ_GT(self, operation):
		"""@see zadani.pdf"""
		
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
		if operation == "LT":
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
	def __INT2CHAR(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, [int, var])
		
		value = int(self.args[1])
		
		try:
			result = chr(value)
		except ValueError:
			Error.exit(Error.string, "INT2CHAR invalid character code")
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution STRI2INT ---	
	def __STRI2INT(self):
		"""@see zadani.pdf"""
		
		self.__GETCHAR()
		
		result = ord(self.args[0].getValue())	# Get char's ASCII code
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution READ ---	
	def __READ(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(var, str)	# Should be <var> <type> but there is no class Type
		
		inputStr = input()
		
		# -- Bool input special rules --
		inputStr = inputStr.lower()
		
		# -- Convert input type --
		result = Interpret.convertValue(self.args[1], inputStr, False)
		
		# -- Save result --
		self.args[0].setValue(result)	
		
		
	# --- Instrcution LABEL ---	
	def __LABEL(self):	# Called from Interpret.__findLabels()
		"""@see zadani.pdf"""
		
		self.__checkArguments(label)
		
		Labels.add(self.args[0])


	# --- Instrcution JUMP ---	
	def __JUMP(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments(label)
		
		Labels.jump(self.args[0])
		
		
	# --- Instrcutions JUMPIFEQ & JUMPIFNEQ ---	
	def __JUMPIFEQ_JUMPIFNEQ(self, expectedResult):
		"""@see zadani.pdf"""
		
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
	def __CREATEFRAME(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments()
		
		# -- Reset TF --
		Frames.temporaryFrame = {}
		
		
	# --- Instrcution PUSHFRAME ---	
	def __PUSHFRAME(self):
		"""@see zadani.pdf"""
		
		self.__checkArguments()
		
		if Frames.temporaryFrame == None:
			Error.exit(Error.scopeExistence, "Tried to access not defined frame")
		
		# -- Move TF to stack --
		Frames.stack.append(Frames.temporaryFrame)
		
		# -- Set LF --

		Frames.localFrame = Frames.stack[-1]	# LF = top of the stack (previously TF)

		# -- Reset TF --
		Frames.temporaryFrame = None

		
	# --- Instrcution POPFRAME ---	
	def __POPFRAME(self):		
		"""@see zadani.pdf"""
		
		self.__checkArguments()

		# -- Check if LF exists --		
		if Frames.localFrame == None:
			Error.exit(Error.scopeExistence, "Local frame not defined")
			
		# -- Set TF --
		Frames.temporaryFrame = Frames.stack.pop()	# TF = previous top of the stack (LF)
		
		# -- Reset LF --
		Frames.localFrame = None
		
		
	# --- Instrcution CALL ---	
	def __CALL(self):		
		"""@see zadani.pdf"""
		
		Interpret.callStack.push(Interpret.instrOrder)
		
		self.__JUMP()
		
		
	# --- Instrcution RETURN ---	
	def __RETURN(self):	
		"""@see zadani.pdf"""
		
		self.__checkArguments()
			
		Interpret.instrOrder = Interpret.callStack.pop()	
		
		
main()
