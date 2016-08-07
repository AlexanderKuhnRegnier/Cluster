<?php
session_destroy();
echo PHP_EOL;
#session_save_path('/home/ahk114/testing');
#session_start();

#var_dump($argv);

//Acquiring the selection info from the command line input now, not from the URL!
function float2hex($float)
{
	if ($float==0)
		return array(0,0,0,0);
	$sign=$float>0?0:1;
	$float=abs($float);
	$exp=floor(log10($float)/log10(2));
	$remainder=8388608*(($float/pow(2,$exp))-1);
	$upperexp=(int)(($exp+127)/2);
	$lowerexp=(($exp+127)&1);
// 	return array(($sign*128) + $upperexp,
// 	             ($lowerexp*128)+(($remainder>>16)&127),
// 	             ($remainder>>8)&255,
// 	             $remainder&255);
	return array(	$remainder&255,
					($remainder>>8)&255,
					($lowerexp*128)+(($remainder>>16)&127),
					($sign*128) + $upperexp
				);

}

$shortopts  = "f:";

$options = getopt($shortopts);
var_dump($options);

if (array_key_exists("f",$options)){$float  = $options["f"];}
else {exit("Please enter a valid floating point number after -f".PHP_EOL);}

echo "Float selected:".$float.PHP_EOL;
echo "float2hex".PHP_EOL;
var_dump(float2hex($float));
echo PHP_EOL;
?>