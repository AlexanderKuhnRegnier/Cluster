<?php
session_destroy();

$shortopts  = "d:";
$day = null;
$options = getopt($shortopts);

if (array_key_exists("d",$options)){$day   = sprintf("%02d",$options["d"]);}
else {exit("Please select a Day!".PHP_EOL);}

$filepicked = "/cluster/data/extended/2016/01/example".$day.".BS";
#$filepicked = "/cluster/data/extended/2016/01/example01.BS";
echo "filename:".$filepicked.PHP_EOL;
?>