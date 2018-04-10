#!/usr/bin/env php
<?php
	/**
	 * @file test.php
	 * @author Jiri Furda (xfurda00)
	 */
	
	// --- Loading arguments ---
	$arguments = Arguments();
	
	
	
	
	
	class Arguments()
	{
		// @todo Test "./" if script is called from different location 
		private $testDir = "./";
		private $recursive = false;
		private $parsePath = "./parse.php" 
		private $interpretPath = "./interpret.py"
		
		public function __construct()
		{
			// --- Read arguments ---
			$options = array("help", "directory:", "recursive", "parse-script:", "int-script:");
			$usedOptions = getopt(null, $options);
			
			// --- Process --help option ---
			global $argc;
			if(isset($usedOptions["help"]))	// If --help is used
			{
				if($argc == 2)	// If its the only argument used
				{
					fputs(STDOUT, "@todo\n");
					exit(0);
				}
				else
					errorExit(10, "Option --help can't be combinated with other arguments");
			}			
		}
	}
?>

