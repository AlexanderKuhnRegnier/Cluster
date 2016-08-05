<?php
session_destroy();
#ini_set('session.save_path',getcwd(). '/'. 'session/'); 
#session_start();
echo PHP_EOL;

$day = null;
$month = null;
$year = null;
$sc = null;
$version = null;

$shortopts  = "d:";
$shortopts .= "m:";
$shortopts .= "y:";
$shortopts .= "s:";
$shortopts .= "n:";

$options = getopt($shortopts);

if (array_key_exists("y",$options)){$year  = $options["y"];}
else {exit("Please select a Year!".PHP_EOL);}
if (array_key_exists("m",$options)){$month = $options["m"];}
else {exit("Please select a Month!".PHP_EOL);}
if (array_key_exists("d",$options)){$day   = $options["d"];}
else {exit("Please select a Day!".PHP_EOL);}

#verification of input parameters, php automatically converts between string and int
if (array_key_exists("s",$options))
{
	$sc = sprintf('%1d',$options["s"]);
	#echo "Spacecraft number given: ".$sc.PHP_EOL;
	if ($sc > 4 || $sc < 1)
	{
		exit("Invalid Spacecraft!".PHP_EOL);
	}
}
else
{
	echo "Setting default value for Spacecraft: Rumba (1)".PHP_EOL;
	$sc = 1;
}

if ($month > 12 || $month < 1)
{
	exit("Invalid Month!".PHP_EOL);
}
#possible issue with date()
if ($year < 2000)
{
	$year += 2000;
}
if ($year > date("Y") || $year < 2000)
{
	exit("Invalid Year!".PHP_EOL);
}
#beware of lacking support for calendars, but seems to be working (24/06/2016)
if ($options["d"] > cal_days_in_month(CAL_GREGORIAN,$month,$year) || $options["d"] < 1)
{
	exit("Number of days is invalid!".PHP_EOL);
}

$jdcount = gregoriantojd($month, $day, $year);
$month_name = jdmonthname($jdcount,0);

$shortyear=sprintf("%02d",$year-2000);			
$month=sprintf("%02d",$month);
$day=sprintf("%02d",$day);

if (array_key_exists("n",$options))
{
	$number = (int)($options["n"]);
	#echo "Number input: ".$number.PHP_EOL;
	if (!($number == $options["n"])) {exit("Please enter a valid number of days!".PHP_EOL);}
}
else
{
	echo "processing 1 day".PHP_EOL;
	$number = 1;
}

echo "Start Date: ".PHP_EOL;
echo "Year:       ".$year.PHP_EOL;
echo "Month:      ".$month_name.PHP_EOL;
echo "Day:        ".$day.PHP_EOL;

echo "Spacecraft: ".$sc.PHP_EOL;
if ($number > 1){echo "Processing: ".$number." days".PHP_EOL;}
else{echo "Processing: ".$number." day".PHP_EOL;}

$initial_unix = mktime(0,0,0,$month,$day,$year);
$time_unix=$initial_unix;

$time_unix=$initial_unix;
#start at the earliest date always, so here start at $initial_unix

$counter=0;
$nr = sprintf('%03d',$counter);
$filename = '/home/ahk114/logs/date_range_stage3/'.'sc-'.$sc.'_'.'start_date-'.$year.$month.$day.'_duration_'.$number.'-days_'.($number/365.).'-years'.'__'.$nr.'.log';			
while (file_exists($filename))
{
	$counter+=1;
	$nr = sprintf('%03d',$counter);
	$filename = '/home/ahk114/logs/date_range_stage3/'.'sc-'.$sc.'_'.'start_date-'.$year.$month.$day.'_duration_'.$number.'-days_'.($number/365.).'-years'.'__'.$nr.'.log';			
}
echo "Logfile:".$filename.PHP_EOL;

for ($i=0; $i<abs($number); $i+=1)
{
	echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
	$year=  date("Y",$time_unix);
	$month= date("m",$time_unix);
	$day=   date("d",$time_unix);
	$option_string = ' '.$sc.' '.$year.' '.$month.' '.$day.' '.'Y'; #Y is just a dummy version here
	$cmd = "php ExtMode_stage3_cli_0_1.php ".$option_string;
	#$cmd = "php stage1.php".$option_string." | php stage2.php";		
	echo "Executing: ".$cmd.PHP_EOL;
	$output = array();
	exec($cmd,$output);
	$filtered_output = array();
	foreach($output as $value)
	{
		if(strpos($value,'Warning: Unknown:') !== false || strlen($value)<1)
		{
			continue;
		}
		else
		{
			$filtered_output[]=$value;
		}
	}
	$stringout = implode(PHP_EOL,$filtered_output);
	/*
	echo "Processing output".PHP_EOL."++++++++++++++++++++++++++++++++++++++++++++++++++++".PHP_EOL;
	echo $stringout.PHP_EOL;
	echo "++++++++++++++++++++++++++++++++++++++++++++++++++++".PHP_EOL;
	*/
	$time_unix = $time_unix + 86400;
	if (count($filtered_output)>0)
	{
		$logfile = fopen($filename,'a');
		if (!$logfile)
		{
			exit('Unable to open log file!');
		}
		fwrite($logfile,$stringout.PHP_EOL.PHP_EOL);
		fclose($logfile);
	}
}
echo PHP_EOL;
#session_destroy();
?>