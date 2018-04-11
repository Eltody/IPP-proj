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
		public $testDir = "./";
		public $recursive = false;
		public $parsePath = "./parse.php" 
		public $interpretPath = "./interpret.py"
		
		public function __construct()
		{
			global $argc;
			
			// --- Read arguments ---
			$options = array("help", "directory:", "recursive", "parse-script:", "int-script:");
			$usedOptions = getopt(null, $options);
			
			// --- Process --help option ---
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
			
			if(isset($usedOptions["directory"]))
				$this.testDir = $usedOptions["testdir"];
				
			if(isset($usedOptions["recursive"]))
				$this.recursive = true;
				
			if(isset($usedOptions["parse-script"]))
				$this.parsePath = $usedOptions["parse-script"];
				
			if(isset($usedOptions["int-script"]))
				$this.interpretPath = $usedOptions["int-script"];
		}
	}
	
	class TestManager()
	{
		private $directories;
		
		public function __construct($arguments)
		{
			$arguments;		
		}
		
		private function scan($testDir, $recursive)
		{
			$files = scandir($testDir);
			$subdirectories = array();
			
			for($files as $file)
			{
				if(is_dir($file))
					array_push($subdirectories, $file)
				else
					$this.test($file);
			}
		}
		
		private function test($file)
		{
			
		}
	}
	
?>

