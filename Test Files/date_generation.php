<?php
session_destroy();
ini_set('session.save_path',getcwd(). '/'. 'session/'); 
session_start();
echo PHP_EOL;


$day = 1;
$month = 1;
$year = 2016;

for ($i=0;$i<1;$i+=1)
{
	echo "Input date: ".date("Y/m/d",mktime(0,0,0,$month,$day,$year)).PHP_EOL;
	$cmd = "php /home/ahk114/Cluster/Test\ Files/command_line_input_test.php -y".$year." -m".$month." -d".$day;	
	echo "Executing: ".$cmd.PHP_EOL;
	exec($cmd,$output);
	var_dump($output);
	echo "Output: ".PHP_EOL.$output;
}

echo PHP_EOL;
session_destroy();
?>