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
		fputs(STDERR, "ERROR: No input\n"); // Error or success? @todo Ask on forum
		exit(11);
	}
	if(strtolower(trim($line)) != ".ippcode18")
	{
		fputs(STDERR, "ERROR: Invalid header\n");
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
		
		// -- Argumments --
		$arguments = $instruction->getArguments();
		// - Arg1 node -		
		if($arguments[0] == null)
			continue;
		$arg1_E = $dom->createElement("arg1");
		$instruction_E->appendChild($arg1_E);
		$arg1Text_E = $dom->createTextNode($arguments[0]);
		$arg1_E->appendChild($arg1Text_E);		
	}

	$dom->save("php://stdout");
	exit(0);
	
	
	// =========
	class Instruction
	{
		private $opCode;
		private $arg = array();
		
		
		public function __construct($line)
		{
			$split = $this->split($line);
			
			if($split == null)	// Whole line is a commentary
				return;
			
			// Set opCode and create objects for arguments
			$this->setOpCode($split[0]);

			// Check arguments count
			$argCount = count($this->arg);
			if($argCount+1 != count($split))
			{
				global $order;
				fputs(STDERR, "ERROR: Too many arguments for instruction (#$order: \"$split[0]\")\n");	
				exit(21);					
			}
			
			// Set values for invidual arguments			
			for($i = 0; $i < $argCount; $i++)
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
					fputs(STDERR, "ERROR: Invalid instruction (#$order: \"$split[0]\")\n");
					exit(21);	
			}	
			$this->opCode = $opCode;
			return true;
		}
		
		public function getOpCode()
		{
			return $this->opCode;
		}
		
		public function isEmpty()
		{
			fputs(STDERR, $this->opCode == null);
			return $this->opCode == null;
		}
		
		public function getArguments()
		{
			$return = array();
			
			foreach($this->arg as $current)
				$return[] = $current->printValue();
				
			return $return;
		}
	}
	
	abstract class Argument
	{
		private $value;
		
		public function setValue($value)
		{
			if(!$this->isValueValid($value))
			{
				fputs(STDERR, "ERROR: Invalid argument");
				exit(21);
			}
			
			$this->value = $value;
		}
		
		public function printValue()
		{
			return $this->value;
		}
		
		abstract protected function isValueValid($value);
	}
	
	class VarArgument extends Argument
	{
		protected function isValueValid($value)
		{
			return preg_match("/^(LF|TF|GF)@[[:alpha:]_\-$%*][[:alnum:]_\-$%*]*$/", $value);
		}
	}
	
	class SymbArgument extends Argument
	{
		protected function isValueValid($value)
		{
			return true;
			// @todo
		}
	}
	
	class LabelArgument extends Argument
	{
		protected function isValueValid($value)
		{
			return true;
			// @todo
		}
	}
	
	class TypeArgument extends Argument
	{
		protected function isValueValid($value)
		{
			return true;
			// @todo
		}
	}
?>
