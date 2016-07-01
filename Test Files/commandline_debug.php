<?php
session_destroy();
echo PHP_EOL;
$shortopts  = "d:";
$day = null;
$options = getopt($shortopts);

if (array_key_exists("d",$options)){$day   = $options["d"];}
else {exit("Please select a Day!".PHP_EOL);}

$option_string = " -d".$day;
$cmd = "php example_script.php".$option_string." | php example_script2.php | php example_script3.php";
#$cmd = "php example_script.php".$option_string." | php example_script2.php";
#$cmd = "php example_script.php".$option_string;
echo "Executing: ".$cmd.PHP_EOL;	
exec($cmd,$output);
echo "Output variable contents".PHP_EOL."+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++".PHP_EOL.PHP_EOL;
var_dump($output);
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++".PHP_EOL.PHP_EOL;

echo "Imploded array contents, added newline: ".PHP_EOL.PHP_EOL;
$stringout = implode("\n",$output);
echo $stringout;
echo PHP_EOL;
?>