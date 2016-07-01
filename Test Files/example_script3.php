<?php
session_destroy();

$stdin_input=file_get_contents("php://stdin",'r');
echo "The stdin to example_script3:".PHP_EOL."start3".PHP_EOL.$stdin_input;
echo "end3".PHP_EOL;
echo "Internal echo for example_script3:".PHP_EOL;
$target_pos = strpos($stdin_input, "Input Filename:");
echo "target_pos3: ".$target_pos.PHP_EOL;
$filename = substr($stdin_input,$target_pos+strlen("Input Filename:"),42);	#file picked starts after "target" string in the input
if (!(substr($filename,strlen($filename)-3,3) == ".BS"))
{
	exit("No filename supplied to example_script3".PHP_EOL);
}
else
{
echo "Input Filename:".$filename.PHP_EOL;
}

?>