#!/usr/bin/env python3



# Libraries
import sys
import xml.etree.ElementTree as ET
import re
import logging

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

def main():
	filePath = processArguments()

	# --- Opening input file ---
	try:
		tree = ET.ElementTree(file=filePath)
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
		
		

def errorExit(code, msg):
	print(msg, file=sys.stderr)
	sys.exit(code)	

def processArguments(): # @todo space in source name
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
			
		# @todo Check types
		self.frame[name] = value;
		
	def get(self, name):
		if name not in self.frame:
			errorExit(ERROR_IDK, "Variable '{0}' does not exist in global frame".format(name))	# @todo Die or retuern None??
		return self.frame[name];

''' # Won't use this anymore?		
class ValueCreator:
	def create(self, typeAndValue):
		split = typeAndValue.split("@", 1)	# Divide into two elements by char '@'
		
		if len(split) != 2:
			errorExit(ERROR_IDK, "Expected char '@' in value") # Might be syntax error
		
		specificObject = self.__determineType(split[0])
		specificObject.setUp(split[1])
		
		return specificObject
		
		
	def __determineType(self, strType):
		if strType == "int":
			return IntValue()
		else:
			errorExit(ERROR_IDK, "Invalid value type")
'''			
			
			
	
class IntValue():	# @todo Funkci co na zaklade int@ rozhodne ze se vytvori int objekt
	def __init__(self, strValue):
		if not re.search(r"^[-+]?\d+$", strValue):
			errorExit(ERROR_IDK, "Invalid int definition")
			
		self.value = int(strValue)



class Argument():
	def __init__(self, inType, inValue):
		if inType == "var":
			if not re.search(r"^(LF|TF|GF)@[\w_\-$&%*][\w\d_\-$&%*]*$", inValue):
				errorExit(ERROR_IDK, "Invalid var name")
		elif inType == "int":
			if not re.search(r"^[-+]?\d+$$", inValue):
				errorExit(ERROR_IDK, "Invalid int value")		
			inValue = int(inValue)	# Convert str to int	
		else:
			errorExit(ERROR_IDK, "Unkown argument type")
			
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
	
class Interpret():
	def __init__(self):
		order = 1
		#valueCreator = ValueCreator()
		self.globalFrame = GlobalFrame()
		
	def loadInstructions(self, root):
		for instrNode in root:
			# Debug info
			logger.debug("=============")
			logger.debug("{0} {1} ".format(instrNode.tag, instrNode.attrib))
			for arg in instrNode:
				logger.debug("{0} {1} {2}".format(arg.tag, arg.attrib,arg.text))
			
			instruction = Instruction(instrNode)
			instruction.execute()
			
	
class Instruction():
	def __init__(self, node):
		if node.tag != "instruction":
			errorExit(ERROR_IDK, "Wrong node loaded (Expected instruction)")
		
		# @todo here shuld be order chceck
		
		
		self.opCode = node.attrib["opcode"]	
		self.args = self.loadArguments(node)
		self.argCount = len(self.args)
		
		
	def loadArguments(self, instrNode):	
		args = []
		argIndex = 0	
		for argNode in instrNode:
			if argNode.tag != "arg{0}".format(argIndex+1):
				errorExit(ERROR_IDK, "Wrong node loaded (Expected arg{0})".format(argIndex+1))
		
			args.append(Argument(argNode.attrib["type"], argNode.text))
			argIndex = argIndex+1
		return(args)
	
	
	def checkArguments(self, *expectedArgs):
		# --- Checking arguments count ---
		if self.argCount != len(expectedArgs):
			errorExit(ERROR_IDK, "Invalid argument count")
			
		# --- Checking arguments type ---
		i = 0;
		for arg in self.args: # Check every argument
			# -- Replacing <symb> --
			if expectedArgs[i] == "symb":
				expectedArgs[i] = ["int", "bool", "string", "var"]
			
			
			argType = arg.getType()	# Saved argument's type
			
			# -- Only one allowed type --
			if type(expectedArgs[i]) == str:
				if argType != expectedArgs[i]:
					errorExit(ERROR_IDK, "Invalid argument type")
					
			# -- More allowed types --
			elif type(expectedArgs[i]) == list:
				if argType not in expectedArgs[i]:	# Check if used argument has one of expected types
					errorExit(ERROR_IDK, "Invalid argument type")
					
			# -- Wrong method parameters --
			else:
				errorExit(ERROR_IDK, "Illegal usage of Instruction.checkArguments()")
				
			i = i+1
	
	
	def execute(self):
		if self.opCode == "DEFVAR":
			self.DEFVAR()
		elif self.opCode == "ADD":
			self.ADD()
		elif self.opCode == "WRITE":
			self.WRITE()
		elif self.opCode == "MOVE":
			self.MOVE()
		else:	# @todo more instructions
			errorExit(ERROR_IDK, "Unkown instruction")
			
			
	#def __eq__(self, other): Dont need this anymore
	#	if self.opCode == other:
	#		return True
	#	return False
	
	
		
	# --- Instrcution DEFVAR ---
	def DEFVAR(self):
		self.checkArguments("var")
			
		if re.search(r"^GF@", self.args[0].value):	# Using .value instead of getValue because var is not yet in frame
			interpret.globalFrame.add(self.args[0].getName())	# @todo universal frame manager
		else:	# @todo more frames
			errorExit(ERROR_IDK, "Unkown frame in instruction DEFVAR")
		
	# --- Instrcution ADD ---
	def ADD(self):
		self.checkArguments("var", ["int", "var"], ["int", "var"])
		
		# @todo check if value in var is int number
			
		result = self.args[1].getValue() + self.args[2].getValue()	
			
		interpret.globalFrame.set(self.args[0].getName(), result)	# @todo universal frame manager
	
	# --- Instrcution WRITE ---
	def WRITE(self):
		self.checkArguments(["var", "str"])  # @todo <symb>
	
		print(self.args[0].getValue())

	# --- Instrcution MOVE ---
	def MOVE(self):
		self.checkArguments("var", "int")  # @todo <var> <symb>
	
		interpret.globalFrame.set(self.args[0].getName(), self.args[1].getValue())
		
main()
