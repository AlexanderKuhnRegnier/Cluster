<?php
session_destroy();
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

$a = 100.15;
$b = 200.1;
$c = 1000.25;
$d = 5.2;
var_dump(float2hex($a));
var_dump(float2hex($b));
var_dump(float2hex($c));
var_dump(float2hex($d));
?>
