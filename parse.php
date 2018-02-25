#!/usr/bin/env php
<?php
	/**
	 * @file parse.php
	 * @author Jiri Furda (xfurda00)
	 */


	// Loading arguments
	// @todo

	
	// --- Loading first line (header) ---
	if(!$line = fgets(STDIN))
	{
		fputs(STDERR, "PARSE ERROR: No input\n"); // Error or success? @todo Ask on forum
		exit(11);
	}
	if(strtolower(trim($line)) != ".ippcode18")
	{
		fputs(STDERR, "PARSE ERROR: Invalid header\n");
		exit(21);
	}
	
	
	// --- XML beginning ---
	$dom = new DomDocument("1.0", "UTF-8");
	$dom->formatOutput = true;	// Better formatting
	
	$program_E = $dom->createElement("program");
	$language_A = $dom->createAttribute("language");
	$language_A->value = "IPPcode18";
	
	$program_E = $dom->appendChild($program_E);
	$program_E->appendChild($language_A);
	
	global $order;
	$order = 1;


	// --- Loading input ---
	while($line = fgets(STDIN))
	{
		$instruction = new Instruction($line);
		
		// -- Skipping commentary --
		if($instruction->isEmpty())
			continue;
	
		// -- Instruction node --
		$instruction_E = $dom->createElement("instruction");
		$program_E->appendChild($instruction_E);
		
		// -- Order node --
		$order_A = $dom->createAttribute("order");
		$instruction_E->appendChild($order_A);
		$order_A->value = $order++;
		
		
		
		// -- Opcode node --
		$opCode_A = $dom->createAttribute("opcode");
		$instruction_E->appendChild($opCode_A);
		$opCode_A->value = $instruction->getOpCode();
		
		// -- Arguments --
		$argCount = $instruction->getArgumentCount();
		for($i = 1; $i <= $argCount; $i++)
		{
			
			//$argValue = $instruction->getArgumentValue($i);
			$arg_E = $dom->createElement("arg".$i);	// e.g. <arg1>
			$instruction_E->appendChild($arg_E);
			
			$type_A = $dom->createAttribute("type");	// e.g. <arg1 type="var">
			$type_A->value = $instruction->getArgumentType($i);	
			$arg_E->appendChild($type_A);
			
			$arg_T = $dom->createTextNode($instruction->getArgumentValue($i)); // e.g. <arg1 type="var">LF@test
			$arg_E->appendChild($arg_T);
		}
	}

	$dom->save("php://stdout");
	exit(0);
	
	
	// =========
	class Instruction
	{
		private $opCode;
		private $arg = array();
		private $argCount;
		
		
		public function __construct($line)
		{
			$split = $this->split($line);
			
			if($split == null)	// Whole line is a commentary
				return;
			
			// Set opCode and create objects for arguments
			$this->setOpCode($split[0]);

			// Check arguments count
			if($this->argCount+1 != count($split))
			{
				global $order;
				fputs(STDERR, "PARSE ERROR: Too many arguments for instruction (#$order: \"$split[0]\")\n");	
				exit(21);					
			}
			
			// Set values for invidual arguments			
			for($i = 0; $i < $this->argCount; $i++)
			{
				$this->arg[$i]->setValue($split[$i+1]);
			}
		}
		
		
		private function split($line)
		{
			$array = preg_split("/[[:blank:]]+/", trim($line), 5);	// Split by spaces and tabs
			
			// Check for commentary
			$count = count($array);
			for($i = 0; $i < $count; $i++)
			{
				$found = 0;
				$array[$i] = @preg_replace("/#.*/", "", $array[$i], 1, $found);	// Search (and earse) a commentary (char '#') 
				if($found)
				{
					$length = ($array[$i] == "" ? $i : $i+1);	// New length of the array
					
					if($length == 0)
						$array = null;	// Empty array
					else
						$array = array_slice($array, 0, $length);	// Truncate the array
					break;
				}
			}	
			
			return $array;
		}
		
		
		private function setOpCode($opCode)
		{			
			switch($opCode)
			{
				// <var> <symb>
				case "MOVE":
				case "NOT":
				case "INT2CHAR":
				case "STRLEN":
				case "TYPE":
					$this->arg[0] = new VarArgument;
					$this->arg[1] = new SymbArgument;
				break;
				
				// none
				case "CREATEFRAME":
				case "PUSHFRAME":
				case "POPFRAME":
				case "RETURN":
				case "BREAK":
				break;
				
				// <var>
				case "DEFVAR":
				case "POPS":
					$this->arg[0] = new VarArgument;
				break;
				
				// <label>
				case "CALL":
				case "LABEL":
				case "JUMP":
					$this->arg[0] = new LabelArgument;
				break;
				
				// <label> <symb> <symb>
				case "JUMPIFEQ":
				case "JUMPIFNEQ":
					$this->arg[0] = new LabelArgument;
					$this->arg[1] = new SymbArgument;
					$this->arg[2] = new SymbArgument;
				break;
				
				// <symb>
				case "PUSHS":
				case "WRITE":
				case "DPRINT":
					$this->arg[0] = new SymbArgument;
				break;
				
				// <var> <symb> <symb>
				case "ADD":
				case "SUB":
				case "MUL":
				case "IDIV":
				case "LT":
				case "GT":
				case "EQ":
				case "AND":
				case "OR":
				case "STRI2INT":
				case "CONCAT":
				case "GETCHAR":
				case "SETCHAR":
					$this->arg[0] = new VarArgument;
					$this->arg[1] = new SymbArgument;
					$this->arg[2] = new SymbArgument;
				break;
				
				// <var> <type>
				case "READ":
					$this->arg[0] = new VarArgument;
					$this->arg[1] = new TypeArgument;
				break;
				
				// Error
				default:
					global $order;
					fputs(STDERR, "PARSE ERROR: Invalid instruction (#$order: \"$split[0]\")\n");
					exit(21);	
			}	
			$this->opCode = $opCode;
			$this->argCount = count($this->arg);
			return true;
		}
		
		public function getOpCode()
		{
			return $this->opCode;
		}
		
		public function isEmpty()
		{
			return $this->opCode == null;
		}
		
		public function getArgumentValue($num)
		{
			return $this->arg[$num-1]->getValue();
		}
		
		public function getArgumentType($num)
		{
			return $this->arg[$num-1]->getType();
		}
		
		public function getArgumentCount()
		{
			return $this->argCount;
		}
	}
	
	abstract class Argument
	{
		protected $value;
		protected $type;
		
		public function setValue($value)
		{
			if(!$this->processValue($value))
			{
				fputs(STDERR, "PARSE ERROR: Invalid argument");
				exit(21);
			}
			
			$this->value = $value;
		}
		
		public function getValue()
		{
			return $this->value;
		}

		public function getType()
		{
			return $this->type;
		}
		
		abstract protected function processValue($value);
	}
	
	class VarArgument extends Argument
	{
		protected function processValue($value)
		{
			$this->type = "var";
			return preg_match("/^(LF|TF|GF)@[[:alpha:]_\-$%*][[:alnum:]_\-$%*]*$/", $value);
		}
	}
	
	class SymbArgument extends Argument
	{
		public function setValue($value)
		{
			$this->processValue($value);	// Value is set in this function
		}
		
		
		protected function processValue($value)
		{
			$split = explode("@", $value, 3);
			
			// Check if explode is valid
			if(count($split) != 2)
			{
				fputs(STDERR, "PARSE ERROR: Too many '@' characters in constant definition\n");
				exit(21);
			}
			
			// Check if different types are valid
			if($split[0] == "int")
			{
				if(!preg_match("/^-?\d+$/", $split[1]))
				{
					fputs(STDERR, "PARSE ERROR: Invalid characters in int constant\n");
					exit(21);
				}
				$this->type = "int";
			}
			else if($split[0] == "bool")
			{
				if($split[1] != "true" || $split[1] != "false")
				{
					fputs(STDERR, "PARSE ERROR: Invalid characters in bool constant\n");
					exit(21);
				}
				$this->type = "bool";
			}
			else if($split[0] == "string")
			{
				// @todo waiting on reply on the forum
				$this->type = "string";
			}
			else if($split[0] == "LF" ||$split[0] == "TF" ||$split[0] == "GF")
			{
				if(!preg_match("/^[[:alpha:]_\-$%*][[:alnum:]_\-$%*]*$/", $split[1]))
				{
					fputs(STDERR, "PARSE ERROR: Invalid characters in var\n");
					exit(21);
				}				
				$this->type = "var";
				$this->value = $value;
				return;
			}
			// @todo maybe also "type"
			else
			{
				global $order;
				fputs(STDERR, "PARSE ERROR: Invalid constant type ('$split[0]' in instrcution #$order)\n");
				exit(21);
			}

			$this->value = $split[1];	// Watchout! Type "var" doesn't reach this line
		}
	}
	
	class LabelArgument extends Argument
	{
		protected function processValue($value)
		{
			$this->type = "label";
			return preg_match("/^[[:alpha:]_\-$%*][[:alnum:]_\-$%*]*$/", $value);
		}
	}
	
	class TypeArgument extends Argument
	{
		protected function processValue($value)
		{
			$this->type = "type";
			return ($value == "int" || $value == "string" ||$value == "bool");
		}
	}
?>
