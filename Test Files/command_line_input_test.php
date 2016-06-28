<?php
session_destroy();
ini_set('session.save_path',getcwd(). '/'. 'session/'); 
session_start();
echo PHP_EOL;
#session_save_path('/home/ahk114/testing');
#session_start();

#var_dump($argv);

$shortopts  = "d:";
$shortopts .= "m:";
$shortopts .= "y:";

$options = getopt($shortopts);
var_dump($options);
$month = $options["m"];
$year  = $options["y"];
$day   = $options["d"];
#verification of input parameters, php automatically converts between
#string and int

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

echo "Year: ".$year.PHP_EOL;
echo "Month: ".$month_name.PHP_EOL;
echo "Day: ".$day.PHP_EOL;


echo PHP_EOL;
session_destroy();
?>