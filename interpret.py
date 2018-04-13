#!/usr/bin/env python3


# Libraries
import sys
import xml.etree.ElementTree as ET
import re
import logging


# === Constants ===
ERROR_IDK = 420
ERROR_ARGUMENT = 10
ERROR_FILE = 11
ERROR_STRUCTURE = 31
ERROR_SYNTAX = 32
ERROR_SEMANTIC = 52
ERROR_OPERANDS = 53
ERROR_NOTEXISTVARIABLE = 54
ERROR_NOTEXISTSCOPE = 55
ERROR_MISSINGVALUE = 56
ERROR_ZERODIVIDE = 57
ERROR_STRING = 58


# === Debug logs ===
logger = logging.getLogger("interpret")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel("DEBUG")


# === Main function ===
def main():
	filePath = processProgramArguments()

	logger.debug("==================================\nfile: {0}\n==============================\n".format(filePath))
	
	# --- Opening input file ---
	try:
		tree = ET.ElementTree(file=filePath)	# @todo Throws error when no root found
	except IOError:
		print("Opening input file error", file=sys.stderr)
		sys.exit(ERROR_FILE)		


	# --- Checking root node ---
	root = tree.getroot()
	# @todo check if root not found???
	if root.tag != "program":
		sys.exit(ERROR_IDK)
	if "language" in root.attrib:
		if root.attrib["language"] != "IPPcode18":	# @todo Case sensitive or not?
			sys.exit(ERROR_IDK)	# Invalid language
		del root.attrib["language"]
	else:
		sys.exit(ERROR_IDK)	# Language missing
	if "name" in root.attrib:
		del root.attrib["name"]
	if "description" in root.attrib:
		del root.attrib["description"]
	if len(root.attrib) != 0:
		sys.exit(ERROR_IDK)	# Attributes error
		
		
	# --- Processing instructions ---
	global interpret
	interpret = Interpret()
	interpret.loadInstructions(root)
		
		
# === Other functions ===
def errorExit(code, msg):
	print("ERROR: {0}".format(msg), file=sys.stderr)
	sys.exit(code)	


def processProgramArguments(): # @todo space in source name
	if len(sys.argv) != 2:
		print("Invalid argument count", file=sys.stderr)
		sys.exit(ERROR_ARGUMENT)
	
	if sys.argv[1] == "--help":
		print("@todo")
		sys.exit(0)
	elif sys.argv[1][:9] == "--source=":
		return sys.argv[1][9:]	
	else:
		print("Illegal argument", file=sys.stderr)
		sys.exit(ERROR_ARGUMENT)
		
		
# === Classes ===		
class GlobalFrame:
	def	__init__(self):
		self.frame = {}
	
	def add(self, name):
		if name in self.frame:
			errorExit(ERROR_IDK, "Variable '{0}' already exist in global frame".format(name))
		self.frame[name] = None;
		
	def set(self, name, value): # @todo Maybe not value but Instruction object? To be sure about the type
		if name not in self.frame:
			errorExit(ERROR_IDK, "Coudn't set value to non-existing variable '{0}'".format(name))
		
		if type(value) == var:	# If trying to save var
			value = value.getValue()
			
		self.frame[name] = value;
		
	def get(self, name):
		if name not in self.frame:
			errorExit(ERROR_IDK, "Variable '{0}' does not exist in global frame".format(name))	# @todo Die or retuern None??
		
		result = self.frame[name]
		
		if type(result) == type(None):
			errorExit(ERROR_IDK, "Tried to get non-initilaized value")
		
		return result;			

"""
class Argument():
	def __init__(self, inType, inValue):
		# --- Variable type ---
		if inType == "var":
			if not re.search(r"^(LF|TF|GF)@[\w_\-$&%*][\w\d_\-$&%*]*$", inValue):
				errorExit(ERROR_IDK, "Invalid var name")
		
		# --- Integer type ---		
		elif inType == "int":
			if not re.search(r"^[-+]?\d+$$", inValue):
				errorExit(ERROR_IDK, "Invalid int value")		
			
			inValue = int(inValue)	# Convert str to int	
			
		# --- String type ---
		elif inType == "string":
			if re.search(r"(?!\\\\[0-9]{3})\s\\\\", inValue):	# @see parse.php for regex legend
				errorExit(ERROR_IDK, "Illegal character in string")		
		
		# --- Boolean type ---
		# @todo	
			
		# --- Invalid type ---
		else:
			errorExit(ERROR_IDK, "Unknown argument type")
			
		# --- Save value and type ---
		self.value = inValue
		self.argType = inType
	
	def getValue(self):
		'''Returns actual value, even if used on variable'''
		if self.argType == "var":
			value = interpret.globalFrame.get(self.getName())
			if value is None:
				errorExit(ERROR_MISSINGVALUE, "Tried to read uninitialised variable") # Error 56
			return value
		else:
			return self.value
		
	def getType(self):
		return self.argType
		
	def getName(self):
		'''Returns name of variable without "GF@"'''
		if self.argType == "var":
			return self.value[3:]
		else:
			errorExit(ERROR_IDK, "Can't use getName() on non-variable")		
"""

class Stack():
	def __init__(self):
		self.content = []
		
	def pop(self, dest):
		if len(self.content) == 0:
			errorExit(ERROR_MISSINGVALUE, "Cannot pop empty stack")
			
		if type(dest) != var:
			errorExit(ERROR_IDK, "Cannot pop to non-variable")
		
		value = self.content.pop()	# Pop top of the stack
		
		dest.setValue(value)	# Set the value
		
		
	def push(self, value):
		self.content.append(value)
		
		
class var:
	def __init__(self, name):
		self.name = name	
		
	def getValue(self):
		"""Returns value stored in var"""
		return interpret.globalFrame.get(self.getName())

	def getName(self):
		"""Returns name of var including frame prefix"""
		return self.name
	
	def setValue(self, value):
		interpret.globalFrame.set(self.getName(), value)
		
	def __add__(self, other):	# When var + int is called
		# --- Get values ---
		selfVal = self.getValue()
		if type(other) == var:
			otherVal = other.getValue()
		else:
			otherVal = other	
	
		# --- Check types ---
		if type(selfVal) != int or type(otherVal) != int:
			errorExit(ERROR_IDK, "Cannot add non-int values/variables")
		
		# --- Solve result ---
		return selfVal + otherVal 
		
	def __radd__(self, other):	# When int + var is called
		return self.__add__(other)
	
class symb:
	"""Dummy object representing str, int, bool or var in instruction.checkArgumentes()"""
	pass
		
				
	
class Interpret():
	def __init__(self):
		order = 1
		#valueCreator = ValueCreator()
		self.globalFrame = GlobalFrame()
		self.stack = Stack()
		
	def loadInstructions(self, root):
		for instrNode in root:
			# Debug info
			logger.debug("=============")
			logger.debug("{0} {1} ".format(instrNode.tag, instrNode.attrib))
			for arg in instrNode:
				logger.debug("{0} {1} {2}".format(arg.tag, arg.attrib,arg.text))
			
			# --- Processing instruction ---
			instruction = Instruction(instrNode)
			instruction.execute()
	
	def convertValue(self, xmlType, xmlValue):
		"""Converts XML value (str in python) to actual type (int, str, bool or var)"""
		
		# --- Variable type ---
		if xmlType == "var":
			if not re.search(r"^(LF|TF|GF)@[\w_\-$&%*][\w\d_\-$&%*]*$", xmlValue):
				errorExit(ERROR_IDK, "Invalid var name")
				
			return var(xmlValue)
		
		# --- Integer type ---		
		elif xmlType == "int":
			if not re.search(r"^[-+]?\d+$$", xmlValue):
				errorExit(ERROR_IDK, "Invalid int value")		
			
			return int(xmlValue)	# Convert str to int	
			
		# --- String type ---
		elif xmlType == "string":
			#if re.search(r"(?!\\[0-9]{3})[\s\\#]", xmlValue):	# @see parse.php for regex legend
			#	errorExit(ERROR_IDK, "Illegal character in string")	# @todo check the regex
			
			# @todo decode escape characters
			#search = 
			
			#while(True):	# Please don't tell Smrcka
			#	found = re.search(r"\\([0-9]{3})", xmlValue)
			#	
			#	if(found == None)
			#		break
			#	
			#	re.sub(r"\\[0-9]{3}", chr(found.group(1)), xmlValue)
			
			groups = re.findall(r"\\([0-9]{3})", xmlValue)	# Find escape sequences
			groups = list(set(groups))	# Remove duplicates
			
			for group in groups:
				if group == "092":	# Special case for \ (I don't even know why)
					xmlValue = re.sub("\\\\092", "\\\\", xmlValue)
					continue
				xmlValue = re.sub("\\\\{0}".format(group), chr(int(group)), xmlValue)
			
			return xmlValue
		
		# --- Boolean type ---
		# @todo	
			
		# --- Invalid type ---
		else:
			errorExit(ERROR_IDK, "Unknown argument type (given {0})".format(xmlType))
	
	
	
class Instruction():
	def __init__(self, node):
		'''Initialization of internal strcture of XML <instruction> node'''
		
		# --- Check node ---
		if node.tag != "instruction":
			errorExit(ERROR_IDK, "Wrong node loaded (Expected instruction)")
		
		# @todo here shuld be order chceck
		
		# --- Process node ---
		self.opCode = node.attrib["opcode"]	
		self.args = self.__loadArguments(node)
		self.argCount = len(self.args)
		
		
	def __loadArguments(self, instrNode):	
		'''Loads child nodes (<argX>) of <instruction> node'''
		args = []
		argIndex = 0	
		
		# --- Load child nodes ---
		for argNode in instrNode:
			# -- Check arg node --
			if argNode.tag != "arg{0}".format(argIndex+1):
				errorExit(ERROR_IDK, "Wrong node loaded (Expected arg{0})".format(argIndex+1))
		
			# --- Save arg value ---
			args.append(interpret.convertValue(argNode.attrib["type"], argNode.text))
			argIndex = argIndex+1
			
		return(args)
	
	
	def __checkArguments(self, *expectedArgs):	
		# --- Checking arguments count ---
		if self.argCount != len(expectedArgs):
			errorExit(ERROR_IDK, "Invalid argument count")
			
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
					errorExit(ERROR_IDK, "Invalid argument type (expected {0} given {1})".format(expectedArgs[i],argType))
					
			# -- More allowed types --
			elif type(expectedArgs[i]) == list:
				if argType not in expectedArgs[i]:	# Check if used argument has one of expected types
					errorExit(ERROR_IDK, "Invalid argument type (expected {0} given {1})".format(expectedArgs[i],argType))
					
			# -- Wrong method parameters --
			else:
				errorExit(ERROR_IDK, "Illegal usage of Instruction.checkArguments()")
				
			i = i+1
	
	def __checkVarType(self, variable, expected):
		'''Compares expected and actula variable type if called on variable'''
		if type(variable) != var:
			return
		
		if type(variable.getValue()) != expected:
			errorExit(ERROR_OPERANDS, "Wrong type inside variable (expected {0} given {1})".format(expected, variable.getType()))
			
		
	
	def execute(self):
		if self.opCode == "DEFVAR":
			self.DEFVAR()
		elif self.opCode == "ADD":
			self.ADD()
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
		else:	# @todo more instructions
			errorExit(ERROR_IDK, "Unkown instruction")	
	
		
	# --- Instrcution DEFVAR ---
	def DEFVAR(self):
		self.__checkArguments(var)
		
		interpret.globalFrame.add(self.args[0].getName())	
		
	# --- Instrcution ADD ---
	def ADD(self):
		self.__checkArguments(var, [int, var], [int, var])

		# -- Count and save result --
		result = self.args[1] + self.args[2]	
		self.args[0].setValue(result)
	
	# --- Instrcution WRITE ---
	def WRITE(self):
		self.__checkArguments(symb)
	
		if type(self.args[0]) == var:	# Printing variable
			result = self.args[0].getValue()
		else:
			result = str(self.args[0])
		print(result, end='')	# end='' means no \n at the end

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
	
		if type(self.args[1]) == var:
			string = self.args[1].getValue()
		else:
			string = str(self.args[1])
		
		length = len(string)
	
		self.args[0].setValue(length)
		
main()
