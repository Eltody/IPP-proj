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
			sys.exit(ERROR_IDK)	# Variable already exist
		self.frame[name] = None;
		
	def set(self, name, value):
		if name not in self.frame:
			sys.exit(ERROR_IDK)	# Variable does not exist
			
		# @todo Check types
		self.frame[name] = value;
		
		
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
		else:
			errorExit(ERROR_IDK, "Unkown argument type")
			
		self.value = inValue
	
		
	
class Interpret():
	def __init__(self):
		order = 1
		valueCreator = ValueCreator()
		
	def loadInstructions(self, root):
		for instrNode in root:
			# Debug info
			logger.debug("=============")
			logger.debug("{0} {1} ".format(instrNode.tag, instrNode.attrib))
			for arg in instrNode:
				logger.debug("{0} {1} {2}".format(arg.tag, arg.attrib,arg.text))
			
			instruction = Instruction(instrNode)
		# 	
	
	#def decodeInstruction(self, instrNode):  # @todo Here on in interpret?
		# Check if instruction order is right 
#		if "order" not in instrNode.attrib or int(instrNode.attrib["order"]) != order:
#			errorExit(ERROR_STRUCTURE, "Invalid order value")
#		order = order+1
		
	#def checkOperands(self):
	
class Instruction():
	def __init__(self, node):
		if node.tag != "instruction":
			errorExit(ERROR_IDK, "Wrong node loaded (Expected instruction)")
		
		# @todo here shuld be order chceck
		
		
		self.decodeOpCode(node.attrib["opcode"]) # @todo What does happen when there is no opcode attribut?
		self.decodeArguments(node)
	
	def decodeOpCode(self, opCode):
		if opCode == "DEFVAR":
			self.expectedArgs = ["var"]
		else:
			errorExit(ERROR_IDK, "Wrong opcode")
		
		self.args = []
		self.opCode = opCode
		
	def decodeArguments(self, instrNode):
		if len(instrNode) != len(self.expectedArgs):
			errorExit(ERROR_IDK, "Expected different amount of arguments")
		
		i = 0	
		for argNode in instrNode:
			if argNode.tag != "arg{0}".format(i+1):
				errorExit(ERROR_IDK, "Wrong node loaded (Expected arg{0})".format(i+1))
			
			if argNode.attrib["type"] != self.expectedArgs[i]:  # @todo What does happen when there is no type attribut?
				errorExit(ERROR_IDK, "Wrong argument type".format(self.expectedArgs[i]))

			
			self.args.append(Argument(argNode.attrib["type"], argNode.text))
			i = i+1 
		
		
main()
