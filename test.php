#!/usr/bin/env php
<?php
	/**
	 * @file test.php
	 * @author Jiri Furda (xfurda00)
	 */
	
	// --- Loading arguments ---
	$testManager = new TestManager();
	
	
	
	
	class Arguments
	{
		// @todo Test "./" if script is called from different location 
		public $testDir = "./";
		public $recursive = false;
		public $parsePath = "./parse.php";
		public $interpretPath = "./interpret.py";
		
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
				$this->testDir = $usedOptions["directory"];
				
				if(substr($this->testDir, -1) != "/")	// @todo Should use mb_substr but it's undefined :O
					$this->testDir = $this->testDir."/";	// Dir must always end with "/"
				
			if(isset($usedOptions["recursive"]))
				$this->recursive = true;
				
			if(isset($usedOptions["parse-script"]))
				$this->parsePath = $usedOptions["parse-script"];
				
			if(isset($usedOptions["int-script"]))
				$this->interpretPath = $usedOptions["int-script"];
		}
	}
	
	class TestManager
	{
		private $arguments;
		private $folders;
		private $results;
		
		public function __construct()
		{
			$this->arguments = new Arguments;
			$this->folders = array();
			$this->results = array();
			
			$this->scan($this->arguments->testDir);
		}
		
		private function scan($dir)
		{	
			// --- Check if folder exists ---
			if(!file_exists($dir))
				return;
			
			// --- Save information about folder ---
			$folderID = count($this->folders);
			$this->folders[$folderID]["name"] = $dir;
			$this->folders[$folderID]["total"] = 0;
			$this->folders[$folderID]["passed"] = 0;
			
			// --- Scan folder ---
			$files = scandir($dir);

			// --- Loop throught every element ---
			foreach($files as $file)
			{
				if(is_dir($dir.$file))	// Found directory
				{
					if($this->arguments->recursive == false)
						continue;
					else
					{
						if($file == "." || $file == "..")
							continue;	// Prevent loop	
							
						$this->scan($dir.$file."/");	// Use recursive scan
						
					}	
				}
				else	// Found file
				{
					if(preg_match("/.src$/", $file))
						$this->test(substr($file, 0, -4), $dir, $folderID);	// "01" instead of "01.src"
					else
						continue;	// Skips every file without .src suffix
				}
			}
		}
		
		private function test($name, $dir, $folderID)
		{
			$path = $dir.$name;	// Shortcut
		
			// --- Create missing files ---
			if(!file_exists($path.".in"))
				touch($path.".in");	// @todo check for not success
			if(!file_exists($path.".out"))
				touch($path.".out");	// @todo check for not success		
			if(!file_exists($path.".rc"))					
			{
				$file = fopen($path.".rc", "w");
				fwrite($file, "0");
				fclose($file);
			}		
			
			
			// --- Check .in file ---
			exec("php5.6 ".$this->arguments->parsePath." <\"$path.src\" >\"$path.tmp.in\"");
			exec("diff -q \"$path.in\" \"$path.tmp.in\"", $diff);
			
			if($diff != NULL)
				$in = "NOK";
			else
				$in = "OK";
			
			
			// --- Check .rc file ---	
			exec("python3.6 ".$this->arguments->interpretPath." --source=\"$path.tmp.in\" >\"$path.tmp.out\"");
			exec("echo $? | diff -q - \"$path.rc\"", $diff);
			if($diff != NULL)
				$rc = "NOK";
			else
				$rc = "OK";			 
			 
			 
			// --- Check .out file ---	
			exec("diff -q \"$path.out\" \"$path.tmp.out\"", $diff);
			
			if($diff != NULL)
				$out = "NOK";
			else
				$out = "OK";
				
				
			// --- Delete temporary files ---
			unlink("$path.tmp.in");
			unlink("$path.tmp.out");
				
				
			// --- Save results ---
			$this->results[$folderID][] = array($name, $in, $rc, $out);
			$this->folders[$folderID]["total"]++;
			if($in == "OK" && $out == "OK" && $rc == "OK")
				$this->folders[$folderID]["passed"]++;
		}
		
		public function printResults()
		{
			// --- Check if some folder was scanned ---
			if(count($this->folders) == 0)
			{
				print("Test folder opening wasn't successful\n>");
				return;
			}
			
			$folderID = 0;
			foreach($this->folders as $dir)
			{
?>
			<p>
				<div class="folder">
					<h2>Folder "<?php echo $dir["name"]; ?>" (passed: <?php echo $dir["passed"]."/".$dir["total"]; ?>)</h2>
<?php
				if(!isset($this->results[$folderID]))
				{
					print("No tests found in this folder\n</div>\n");
					$folderID++;
					continue;
				}
?>					
					<table>
						<tr>
							<th>Test name</th>
							<th>IN</th> 
							<th>OUT</th> 
							<th>RC</th> 
						</tr>			
<?php

				foreach($this->results[$folderID] as $row)
				{
?>
						<tr>
							<td><?php echo $row[0]; ?></td>
							<td class="result" id="<?php echo $row[1]; ?>">&nbsp;</td>
							<td class="result" id="<?php echo $row[2]; ?>">&nbsp;</td>
							<td class="result" id="<?php echo $row[3]; ?>">&nbsp;</td>
						</tr>
<?php
				}
?>				
					</table>
				</div>
			</p>
<?php
				$folderID++;
			}
		}
	}
	
?>
<!DOCTYPE HTML>
<html lang="cs">
	<head>
		<meta charset="utf-8" />
		<style>
		body
		{
			background-color: #b2c2bf;
			margin: 30px;
		}
		
		h1
		{
			font-size: 40px;
			font-family: "Segoe UI",Arial,sans-serif;
		}

		h2
		{
			line-height: 0px;
			font-family: "Segoe UI",Arial,sans-serif;
		}
		
		.container
		{
			margin: auto;
			width: 50%;
			box-shadow: 10px 10px 5px grey;
		}
		
		.header
		{
			background-color: #c0ded9;
			text-align: center;
			padding: 10px;
		}
		
		.content
		{
			background-color: #eaece5;
			padding: 15px;
		}
		
		.folder
		{
			background-color: #ffffff;
			padding: 15px;
		}
		
		table th
		{
			background-color: lightgrey;
		}
		table tr:nth-child(even)
		{
			background-color: #eee;
		}
		table tr:nth-child(odd)
		{
			background-color: #fff;
		}
		
		.result
		{
			width: 40px;
		}
		
		#OK
		{
			background-color: #6B8E23;
		}
		
		#NOK
		{
			background-color: #ff1700;
		}		
		</style>
		<title></title>
	</head>
	<body>
		<div class="container">
			<div class="header">
				<h1>IPP project automatic tests</h1>
			</div>
			<div class="content">
				<?php $testManager->printResults(); ?>
			</div>
		</div>
	</body>
</html>
