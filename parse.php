#!/usr/bin/env php
<?php
	/**
	 * @file parse.php
	 * @author Jiri Furda (xfurda00)
	 */


	// Loading arguments
	// @todo

	
	// Loading first line (header)
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
	

	// Loading input
	while($line = fgets(STDIN))
	{
		$split = preg_split("/[[:blank:]]+/", trim($line));
		$wordcount = count($split);
		for($i = 0; $i < $wordcount; $i++)
		{
			fputs(STDOUT, $split[$i]);
			fputs(STDOUT, " ");
		}
		fputs(STDOUT, "\n");
	}


	
	fputs(STDOUT, "====SUCCESSFUL END====\n");
	exit(0);
?>
