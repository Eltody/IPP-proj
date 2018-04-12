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
	
	logger.debug("=======================\nfile: {0}\n=====================\n".format(filePath))
	
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

class Stack():
	def __init__(self):
		self.content = []
		
	def pop(self, dest):
		if len(self.content) == 0:
			errorExit(ERROR_MISSINGVALUE, "Cannot pop empty stack")
		
		value = self.content.pop()	# Pop top of the stack
		
		interpret.globalFrame.set(dest, value)	# Set the value
		
		
	def push(self, value):
		self.content.append(value)
		
		
	
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
			
		# --- Converting tuple to list ---
		expectedArgs = list(expectedArgs)	
			
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
		elif self.opCode == "PUSHS":
			self.PUSHS()
		elif self.opCode == "POPS":
			self.POPS()
		else:	# @todo more instructions
			errorExit(ERROR_IDK, "Unkown instruction")	
	
		
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
	
		print(self.args[0].getValue(), end='')	# end='' means no \n at the end

	# --- Instrcution MOVE ---
	def MOVE(self):
		self.checkArguments("var", "int")  # @todo <var> <symb>
		
		interpret.globalFrame.set(self.args[0].getName(), self.args[1].getValue())
		
	# --- Instrcution PUSHS ---
	def PUSHS(self):
		self.checkArguments("symb")
	
		interpret.stack.push(self.args[0].getValue())

	# --- Instrcution POPS ---
	def POPS(self):
		self.checkArguments("var")
	
		interpret.stack.pop(self.args[0].getName())
		
main()
