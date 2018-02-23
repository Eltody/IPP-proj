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
	}

	$dom->save("php://stdout");

	fputs(STDOUT, "====SUCCESSFUL END====\n");
	exit(0);
	
	
	// =========
	class Instruction
	{
		private $opCode;
		private $arg1;
		private $arg2;
		private $arg3;
		
		public function __construct($line)
		{
			$split = $this->split($line);
			
			if($split == null)	// Whole line is a commentary
				return;
			
			if(!$this->checkOpCode($split[0]))
			{
				global $order;
				fputs(STDERR, "ERROR: Invalid instruction (#$order: \"$split[0]\")\n");
				exit(21);					
			}
			
			$this->opCode = $split[0];
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
		
		private function checkOpCode($opCode)
		{
			$legalOpCodes = array("MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL", "RETURN",
			"PUSHS", "POPS", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "CHAR2INT",
			"STRI2INT", "READ", "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP",
			"JUMPIFEQ", "JUMPIFNEQ", "DPRINT", "BREAK");
			
			foreach($legalOpCodes as $legalOpCode)
				if($opCode == $legalOpCode)
					return true;
			return false;
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
	}
?>
