#!/usr/bin/env php
<?php
	/**
	 * @file parse.php
	 * @author Jiri Furda (xfurda00)
	 */


	// --- Loading arguments ---
	$stats = loadArguments();
	
	
	// --- Loading first line (header) ---
	if(!$line = fgets(STDIN))
		errorExit(11, "PARSER ERROR: No input");
		
	$line = strtolower(trim(preg_replace("/#.*$/", "", $line, -1, $found)));	// Remove commentary, white characters and lower string
	if($line != ".ippcode18")
		errorExit(21, "PARSER ERROR: Invalid header");

	if($found)
		$stats->addComment();

	
	// --- XML beginning ---
	$dom = new DomDocument("1.0", "UTF-8");
	$dom->formatOutput = true;	// Better formatting
	
	$program_E = $dom->createElement("program");
	$program_E = $dom->appendChild($program_E);
	
	$language_A = $dom->createAttribute("language");
	$language_A->value = "IPPcode18";
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
			
		// -- Update stats --
		$stats->addInstruction();
	
		// -- Instruction element --
		$instruction_E = $dom->createElement("instruction");
		$program_E->appendChild($instruction_E);
		
		// -- Order attribute --
		$order_A = $dom->createAttribute("order");
		$order_A->value = $order++;
		$instruction_E->appendChild($order_A);
		
		// -- Opcode attribute --
		$opCode_A = $dom->createAttribute("opcode");
		$opCode_A->value = $instruction->getOpCode();
		$instruction_E->appendChild($opCode_A);
		
		// -- Arg elements --
		$argCount = $instruction->getArgumentCount();
		for($i = 1; $i <= $argCount; $i++)
		{
			// - Arg element -
			$arg_E = $dom->createElement("arg".$i);	
			$instruction_E->appendChild($arg_E);	// e.g. <arg1>
			
			// - Type attribute -
			$type_A = $dom->createAttribute("type");
			$type_A->value = $instruction->getArgumentType($i);	
			$arg_E->appendChild($type_A);	// e.g. <arg1 type="var">
			
			// - Text node -
			$arg_T = $dom->createTextNode($instruction->getArgumentValue($i));
			$arg_E->appendChild($arg_T);	// e.g. <arg1 type="var">LF@test
		}
	}

	// --- Print XML result and end ---
	$stats->writeStats();
	$dom->save("php://stdout");
	exit(0);
	
	
	// ===== Function declaration =====
	/**
	 * @brief Prints message to STDERR and exit script with specified return value
	 * @param retVal	Return value
	 * @param msg	Informative message
	 */
	function errorExit($retVal, $msg)
	{
		fputs(STDERR, "$msg\n");
		exit($retVal);
	}
	
	function loadArguments()
	{
		// --- Read arguments ---
		$options = array("help", "stats:", "loc", "comments");
		$usedOptions = getopt(null, $options);	
		
		
		// --- Process --help option ---
		global $argc;
		if(isset($usedOptions["help"]))	// If --help is used
		{
			if($argc == 2)	// If its the only argument used
			{
				fputs(STDOUT, "This script loads source code in IPPcode18 from standart input, checks\n");
				fputs(STDOUT, "lexical and syntax correctness and prints XML representation of the program\n");
				fputs(STDOUT, "on standart output\n");
				exit(0);
			}
			else
				errorExit(10, "Option --help can't be combinated with other arguments");
		}
		
		
		// --- Check stats options ---
		$usedOptionsCount = count($usedOptions);
		
		if($argc > 1)
		{
			if($argc != $usedOptionsCount+1 || $usedOptionsCount > 3)
				errorExit(10, "Too many or few arguments used");
			
			if(!isset($usedOptions["stats"]))
				errorExit(10, "Option --stats is missing");
		}
		
		// --- Create stats object ---
		return new Stats($usedOptions);
	}
	
	// ===== Class declaration =====
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
				errorExit(21, "PARSER ERROR: Too many arguments for instruction (#$order: \"$split[0]\")");					
			}
			
			// Set values for invidual arguments			
			for($i = 0; $i < $this->argCount; $i++)
			{
				$this->arg[$i]->setValue($split[$i+1]);
			}
		}
		
		/**
		 * @brief Splits loaded line by white characters and removes commentary
		 * @param line	Loaded line
		 * @return Array of splitted parts without commentary
		 */
		private function split($line)
		{
			$array = preg_split("/[[:blank:]]+/", trim($line), 5, PREG_SPLIT_NO_EMPTY);	// Split by spaces and tabs
			
			// Check for commentary
			$count = count($array);
			for($i = 0; $i < $count; $i++)
			{
				$found = 0;
				$array[$i] = @preg_replace("/#.*/", "", $array[$i], 1, $found);	// Search (and earse) a commentary (char '#') 
				if($found)
				{
					global $stats;
					$stats->addComment();	// Update stats
					
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
		
		/**
		 * @brief Sets operation code of the instruction, create empty argument objects and count number of arguments
		 * @param opCode	Operation code of the instruction
		 */
		private function setOpCode($opCode)
		{
			$opCode = strtoupper($opCode);
						
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
					errorExit(21, "PARSER ERROR: Invalid instruction (#$order: \"$opCode\")");
			}	
			$this->opCode = $opCode;
			$this->argCount = count($this->arg);
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
				errorExit(21, "PARSER ERROR: Invalid argument (type is \"".$this->type."\")");
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
			return preg_match("/^(LF|TF|GF)@[[:alpha:]_\-$&%*][[:alnum:]_\-$&%*]*$/", $value);
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
			$split = explode("@", $value, 2);
			
			// Check if explode is valid
			if(count($split) < 2)
			{
				print($value);
				errorExit(21, "PARSER ERROR: There must be a '@' character in constant definition'");
			}
			
			// Check if different types are valid
			switch($split[0])
			{
				case "int":
					if(!preg_match("/^[-+]?\d+$/", $split[1]))
					{
						errorExit(21, "PARSER ERROR: Invalid characters in int constant ('$split[1]')");
						exit(21);
					}
					break;
					
				case "bool":
					if($split[1] != "true" && $split[1] != "false")
					{
						errorExit(21, "PARSER ERROR: Invalid characters in bool constant (found: '$split[1]')");
					}
					break;
					
				case "string":	
					/* Regex legend
					 * ============
					 * (?!			// Ignore cases when
					 * \\\\0[012][0-9]	// From \000 to \099
					 * )			// End ignore cases
					 * [[:blank:]\\\\#]	// Search for white chars, \ or #
					 * =============
					 * \\\\ represents '\'
					*/ 
					
					if($split[1] != "")	// Ignore empty string
						if(preg_match("/(?!\\\\[0-9]{3})[[:blank:]\\\\#]/", $split[1]))	// Search for illegal characters
						{
							global $order;
							echo $split[1]."\n";
							errorExit(21, "PARSER ERROR: Invalid characters in string (instrcution #$order)");
						}	
					break;
					
				case "LF":
				case "TF":
				case "GF":
					if(!preg_match("/^[[:alpha:]_\-$&%*][[:alnum:]_\-$&%*]*$/", $split[1]))
					{
						global $order;
						errorExit(21, "PARSER ERROR: Invalid characters in var (instrcution #$order)");
					}				
					$split[0] = "var";	// "var" instead of e.g. "TF"
					$split[1] = $value;	// Because we need to save whole "LF@abc" not just "abc"
					break;
					
				default:
					global $order;
					errorExit(21, "PARSER ERROR: Invalid constant type ('$split[0]' in instrcution #$order)");
					break;
			}
			
			// Save the values
			$this->type = $split[0];
			$this->value = $split[1];	
		}
	}
	
	class LabelArgument extends Argument
	{
		protected function processValue($value)
		{
			$this->type = "label";
			return preg_match("/^[[:alpha:]_\-$&%*][[:alnum:]_\-$&%*]*$/", $value);
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
	
	class Stats
	{
		private $file;
		private $instructionCount = 0;
		private $instructionEnabled = false;
		private $commentCount = 0;
		private $commentEnabled = false;
		private $first;	// Define if instuctions or comments will be printed at first line
		
		public function __construct($array)
		{
			foreach($array as $key => $value)
			{
				switch($key)
				{
					case "stats":
						$this->file = $value;
						break;
					
					case "comments":
						if($this->first == null)
							$this->first = "comment";
						$this->commentEnabled = true;
					break;
					case "loc":
						if($this->first == null)
							$this->first = "instruction";
						$this->instructionEnabled = true;
					break;
				}
			}
		}
		
		public function addInstruction()
		{
			if($this->instructionEnabled == true)
				$this->instructionCount++;
		}
		public function addComment()
		{
			if($this->commentEnabled == true)
				$this->commentCount++;
		}
		
		public function writeStats()
		{
			if($this->instructionEnabled == true || $this->commentEnabled == true)
			{
				$file = fopen($this->file, "w");
				
				if(!$file)
					errorExit(12, "Could't open stats file");

				if($this->first == "comment")
				{
					$content = $this->commentCount;
					
					if($this->instructionEnabled == true)
						$content .= "\n".$this->instructionCount;
				}
				else
				{
					$content = $this->instructionCount;
					
					if($this->commentEnabled == true)
						$content .= "\n".$this->commentCount;
				}


				$written = fwrite($file, $content);
				if(!$written)
					errorExit(12, "Could't write to stats file");
				fclose($file);
			}		
		}
	}
?>
