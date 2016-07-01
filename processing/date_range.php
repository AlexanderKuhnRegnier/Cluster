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
$shortopts .= "t"; #testing option - skips pre processing!

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


define("FORWARDS","f");
define("BACKWARDS","b");

if (array_key_exists("n",$options))
{
	$number = (int)($options["n"]);
	#echo "Number input: ".$number.PHP_EOL;
	if (!($number == $options["n"])) {exit("Please enter a valid number of days!".PHP_EOL);}
	$direction = ($number > 0) ? FORWARDS:BACKWARDS; 
	#echo "CHOSEN DIRECTION: ".$direction.PHP_EOL;
	if ($direction != FORWARDS && $direction != BACKWARDS)
	{
		exit("Error - Invalid Direction - enter a valid number of days!".PHP_EOL);
	}
}
else
{
	echo "Setting direction to forwards, processing 1 day".PHP_EOL;
	$direction = FORWARDS;
	$number = 1;
}

if ($direction == FORWARDS) {echo "Start Date: ".PHP_EOL;}
if ($direction == BACKWARDS) {echo "End Date: ".PHP_EOL;}
echo "Year:       ".$year.PHP_EOL;
echo "Month:      ".$month_name.PHP_EOL;
echo "Day:        ".$day.PHP_EOL;

echo "Spacecraft: ".$sc.PHP_EOL;
if ($number > 1){echo "Processing: ".$number." days".PHP_EOL;}
else{echo "Processing: ".$number." day".PHP_EOL;}

$initial_unix = mktime(0,0,0,$month,$day,$year);
$direction_multiplier = ($direction == FORWARDS) ? 1:-1;
$time_unix=$initial_unix;

/*
Process stage1 and stage2 for 7 days prior to region of interest, in order to circumvent the problem that sometimes previous
days need to be processed this was in order for stage3 processing to work properly (and/or the selection process as well)
*/
if (array_key_exists("t",$options)){echo "Testing mode - pre-processing skipped!".PHP_EOL;}
else 
{
	echo "Pre-processing of days leading up to earliest selected date".PHP_EOL;
	if ($direction == FORWARDS)
	{
		#need to process additional days before the earliest date of interest
		for ($i=0; $i<7; $i+=1)
		{
		$time_unix = $time_unix - $i*86400;
		$year=  date("Y",$time_unix);
		$month= date("m",$time_unix);
		$day=   date("d",$time_unix);
		$option_string = " -y".$year." -m".$month." -d".$day." -s".$sc;
		$cmd = "php stage1.php".$option_string." | php stage2.php";
		echo "Executing: ".$cmd.PHP_EOL;	
		exec($cmd,$output);
		var_dump($output);
		}
	}
	elseif ($direction == BACKWARDS)
	{
		#need to process additional days before the earliest date of interest. Here, that is before the initial date!
		$time_unix = $time_unix - abs($number)*86400;
		for ($i=0; $i<7; $i+=1)
		{
		$year=  date("Y",$time_unix);
		$month= date("m",$time_unix);
		$day=   date("d",$time_unix);
		$option_string = " -y".$year." -m".$month." -d".$day." -s".$sc;
		$cmd = "php stage1.php".$option_string." | php stage2.php";
		echo "Executing: ".$cmd.PHP_EOL;	
		exec($cmd,$output);
		var_dump($output);
		$time_unix = $time_unix - $i*86400;
		}
	}
	else{exit("Direction not assigned".PHP_EOL);}

	echo "Finished pre-processing".PHP_EOL;
}


if ($direction == FORWARDS)
{	
	$time_unix=$initial_unix;
	#start at the earliest date always, so here start at $initial_unix
	for ($i=0; $i<abs($number); $i+=1)
	{
		echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
		$year=  date("Y",$time_unix);
		$month= date("m",$time_unix);
		$day=   date("d",$time_unix);
		$option_string = " -y".$year." -m".$month." -d".$day." -s".$sc;
		$cmd = "php stage1.php".$option_string." | php stage2.php | php stage3_select.php | php stage3.php";
		#$cmd = "php stage1.php".$option_string." | php stage2.php | php stage3_select.php";		
		echo "Executing: ".$cmd.PHP_EOL;
		exec($cmd,$output);
		var_dump($output);
		echo "Output: ".PHP_EOL.$output;
		$time_unix = $time_unix + 86400; 
	}
}
elseif ($direction == BACKWARDS)
{
	$time_unix=$initial_unix-(abs($number)-1)*86400;
	#need to start at earliest date, so go back in time from $initial_unix
	for ($i=0; $i<abs($number); $i+=1)
	{
		echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
		$year=  date("Y",$time_unix);
		$month= date("m",$time_unix);
		$day=   date("d",$time_unix);
		$option_string = " -y".$year." -m".$month." -d".$day." -s".$sc;
		$cmd = "php stage1.php".$option_string." | php stage2.php | php stage3_select.php | php stage3.php";
		#$cmd = "php stage1.php".$option_string." | php stage2.php | php stage3_select.php";		
		echo "Executing: ".$cmd.PHP_EOL;
		exec($cmd,$output);
		var_dump($output);
		echo "Output: ".PHP_EOL.$output;
		$time_unix = $time_unix + 86400; 
	}	
}
echo PHP_EOL;
#session_destroy();
?>