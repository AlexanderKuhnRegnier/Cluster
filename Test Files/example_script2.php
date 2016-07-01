<?php
session_destroy();

$stdin_input=file_get_contents("php://stdin",'r');
echo "The stdin to example_script2:".PHP_EOL.$stdin_input;

$target_pos = strpos($stdin_input, "filename:");
echo "target_pos2: ".$target_pos.PHP_EOL;
$filename = substr($stdin_input,$target_pos+10,42);	#file picked starts after "target" string in the input
if (!(substr($filename,strlen($filename)-3,3) == ".BS"))
{
	exit("No filename supplied to example_script2".PHP_EOL);
}
else
{
echo "Input Filename:".$filename.PHP_EOL;
}
?>