<?php
session_destroy();
ini_set('session.save_path',getcwd(). '/'. 'session/'); 
session_start();
echo PHP_EOL;
#session_save_path('/home/ahk114/testing');
#session_start();

#var_dump($argv);

//Acquiring the selection info from the command line input now, not from the URL!

$day = null;
$month = null;
$year = null;
$sc = null;
$version = null;

$shortopts  = "d:";
$shortopts .= "m:";
$shortopts .= "y:";
$shortopts .= "sc:";
$shortopts .= "ver:";

$options = getopt($shortopts);
#var_dump($options);

if (array_key_exists("y",$options)){$year  = $options["y"];}
else {exit("Please select a Year".PHP_EOL);}
if (array_key_exists("m",$options)){$month = $options["m"];}
else {exit("Please select a month".PHP_EOL);}
if (array_key_exists("d",$options)){$day   = $options["d"];}
else {exit("Please select a Day".PHP_EOL);}

#verification of input parameters, php automatically converts between string and int
if (array_key_exists("sc",$options))
{
	if ($sc > 4 || $sc < 1)
	{
		exit("Invalid Spacecraft".PHP_EOL);
	}
	else {$sc = $options["sc"];}
}
else
{
	echo "Setting default value for Spacecraft: Rumba (1)".PHP_EOL;
	$sc = 1;
}
if (array_key_exists("ver",$options))
{
	if (strtoupper($version) != 'A' || strtoupper($version) != 'B' || strtoupper($version) != 'K')
	{
		exit("Invalid Version".PHP_EOL);
	}
	else {$version = $option["ver"];}
}
else
{
	echo "Setting default value for Version: B".PHP_EOL;
	$version = 'B';
}
if ($month > 12 || $month < 1)
{
	exit("Invalid Month".PHP_EOL);
}
#possible issue with date()
if ($year > date("Y") || $year < 2000)
{
	exit("Invalid Year".PHP_EOL);
}
#beware of lacking support for calendars, but seems to be working (24/06/2016)
if ($options["d"] > cal_days_in_month(CAL_GREGORIAN,$month,$year) || $options["d"] < 1)
{
	exit("Number of days is invalid".PHP_EOL);
}

$jdcount = gregoriantojd($month, $day, $year);
$month_name = jdmonthname($jdcount,0);

echo "Year:       ".$year.PHP_EOL;
echo "Month:      ".$month_name.PHP_EOL;
echo "Day:        ".$day.PHP_EOL;
echo "Spacecraft: ".$sc.PHP_EOL;
echo "Version:    ".$version.PHP_EOL;

echo PHP_EOL;
session_destroy();
?>