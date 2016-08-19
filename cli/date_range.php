<?php
session_destroy();
#ini_set('session.save_path',getcwd(). '/'. 'session/'); 
#session_start();
define('LOG','/home/ahk114/logs/date_range/');

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
$shortopts .= "v:"; #version
$shortopts .= "c";

$longopts = array("clean");
$options = getopt($shortopts,$longopts);

if (array_key_exists("y",$options)){$year  = $options["y"];}
else {exit("Please select a Year!".PHP_EOL);}
if (array_key_exists("m",$options)){$month = $options["m"];}
else {exit("Please select a Month!".PHP_EOL);}
if (array_key_exists("d",$options)){$day   = $options["d"];}
else {exit("Please select a Day!".PHP_EOL);}

if (array_key_exists("v",$options))
{
	$versions = array();
	for ($i=0; $i<strlen($options["v"]);$i+=1)
	{
		$versions[] = strtoupper($options["v"][$i]);
	}
}
else
{
	echo "Setting default versions numbers to BKA".PHP_EOL;
	$versions=array('B','K','A');
}
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
echo "Versions:".PHP_EOL;
echo var_dump($versions);
echo PHP_EOL;
if ($number > 1){echo "Processing: ".$number." days".PHP_EOL;}
else{echo "Processing: ".$number." day".PHP_EOL;}

$initial_unix = mktime(0,0,0,$month,$day,$year);
$created_dir=False;
if (!is_dir(LOG))
{
	mkdir(LOG,0750,true);
	$created_dir=True;
}
$counter=0;
$nr = sprintf('%03d',$counter);
$filename = LOG.'sc-'.$sc.'_'.'start_date-'.$year.$month.$day.'_duration_'.$number.'-days_'.sprintf('%06.3f',($number/365.25)).'-years'.'__'.$nr.'.log';			
while (file_exists($filename))
{
	$counter+=1;
	$nr = sprintf('%03d',$counter);
	$filename = LOG.'sc-'.$sc.'_'.'start_date-'.$year.'_'.$month.'_'.$day.'_duration_'.$number.'-days_'.sprintf('%06.2f',($number/365.25)).'-years'.'__'.$nr.'.log';			
}
echo "Logfile:".$filename.PHP_EOL;
if ($created_dir)
{
	$logfile = fopen($filename,'a');
	if (!$logfile)
	{
		exit('Unable to open log file!'.PHP_EOL);
	}
	fwrite($logfile,PHP_EOL."Created logfile directory:".LOG.PHP_EOL);
	fclose($logfile);	
}
######################Stage 1 Processing####################
$pad_days = 5;
$time_unix=$initial_unix-$pad_days*86400;
#for stage1, start at a prior date always, since this is needed to get correct info in some cases.
$logfile = fopen($filename,'a');
if (!$logfile)
{
	exit('Unable to open log file!'.PHP_EOL);
}
fwrite($logfile,PHP_EOL.'STARTING STAGE 1 PROCESSING'.PHP_EOL.PHP_EOL);
fclose($logfile);
for ($i=0; $i<($number+$pad_days); $i+=1)
{
	echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
	$year=  date("Y",$time_unix);
	$month= date("m",$time_unix);
	$day=   date("d",$time_unix);
	foreach ($versions as $version)
	{
		$option_string = ' '.$sc.' '.$year.' '.$month.' '.$day.' '.$version; 
		$cmd = "php ExtMode_stage1_cli_0_1.php ".$option_string;		
		echo "Executing: ".$cmd.PHP_EOL;
		$output = array();
		$return = null;
		exec($cmd,$output,$return);
		if ($return==1)
		{
			$filtered_output = array();
			foreach($output as $value)
			{
				if(strpos($value,'Warning: Unknown:') !== false || strlen($value)<1) #bodge to get rid of warning messages in log
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
			if (count($filtered_output)>0)
			{
				$logfile = fopen($filename,'a');
				if (!$logfile)
				{
					exit('Unable to open log file!'.PHP_EOL);
				}
				fwrite($logfile,$stringout.PHP_EOL.PHP_EOL);
				fclose($logfile);
			}
			break 1; #still needs to increment time_unix
		}
		else
		{
			echo "Error:".$return;
			echo "Version:".$version.PHP_EOL;
			$logfile = fopen($filename,'a');
			if (!$logfile)
			{
				exit('Unable to open log file!'.PHP_EOL);
			}
			fwrite($logfile,"Error for command:".$cmd.PHP_EOL);
			if ($return==255)
			{
				$return='Unable to open file'.PHP_EOL;
			}
			fwrite($logfile,$return.PHP_EOL);
			fclose($logfile);	
		}
	}
	$time_unix = $time_unix + 86400;
}
echo PHP_EOL;

######################Stage 2 Processing####################
$time_unix=$initial_unix; #here just start from the intended date
$logfile = fopen($filename,'a');
if (!$logfile)
{
	exit('Unable to open log file!'.PHP_EOL);
}
fwrite($logfile,'-------------------------------------------------------------------------------------------------');
fwrite($logfile,PHP_EOL.'STARTING STAGE 2 PROCESSING'.PHP_EOL.PHP_EOL);
fclose($logfile);
for ($i=0; $i<($number); $i+=1)
{
	echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
	$year=  date("Y",$time_unix);
	$month= date("m",$time_unix);
	$day=   date("d",$time_unix);
	foreach ($versions as $version)
	{
		$option_string = ' '.$sc.' '.$year.' '.$month.' '.$day.' '.$version;
		$cmd = "php ExtMode_stage2_cli_0_1.php ".$option_string;		
		echo "Executing: ".$cmd.PHP_EOL;
		$output = array();
		$return = null;
		exec($cmd,$output,$return);
		if ($return==1)
		{
			$filtered_output = array();
			foreach($output as $value)
			{
				if(strpos($value,'Warning: Unknown:') !== false || strlen($value)<1) #bodge to get rid of warning messages in log
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
			if (count($filtered_output)>0)
			{
				$logfile = fopen($filename,'a');
				if (!$logfile)
				{
					exit('Unable to open log file!'.PHP_EOL);
				}
				fwrite($logfile,PHP_EOL.'Stage 2'.PHP_EOL);
				fwrite($logfile,$stringout.PHP_EOL.PHP_EOL);
				fclose($logfile);
			}
			break 1;
		}
		else
		{
			echo "Error:".$return;
			echo "Version:".$version.PHP_EOL;
			$logfile = fopen($filename,'a');
			if (!$logfile)
			{
				exit('Unable to open log file!'.PHP_EOL);
			}
			fwrite($logfile,"Error for command:".$cmd.PHP_EOL);
			if ($return==255)
			{
				$return='Unable to open file'.PHP_EOL;
			}
			fwrite($logfile,$return.PHP_EOL);
			fclose($logfile);	
		}
	}
	$time_unix = $time_unix + 86400;
}
echo PHP_EOL;

######################Stage 3 Processing####################
$time_unix=$initial_unix; #here just start from the intended date
$logfile = fopen($filename,'a');
if (!$logfile)
{
	exit('Unable to open log file!'.PHP_EOL);
}
fwrite($logfile,'-------------------------------------------------------------------------------------------------');
fwrite($logfile,PHP_EOL.'STARTING STAGE 3 PROCESSING'.PHP_EOL.PHP_EOL);
fclose($logfile);
for ($i=0; $i<($number); $i+=1)
{
	echo "Input date: ".date("Y/m/d",$time_unix).PHP_EOL;
	$year=  date("Y",$time_unix);
	$month= date("m",$time_unix);
	$day=   date("d",$time_unix);

	$option_string = ' '.$sc.' '.$year.' '.$month.' '.$day.' '.'Y';#Y is just dummy version
	$cmd = "php ExtMode_stage3_cli_0_1.php ".$option_string;		
	echo "Executing: ".$cmd.PHP_EOL;
	$output = array();
	$return = null;
	exec($cmd,$output,$return);
	$filtered_output = array();
	foreach($output as $value)
	{
		if(strpos($value,'Warning: Unknown:') !== false || strlen($value)<1) #bodge to get rid of warning messages in log
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
			exit('Unable to open log file!'.PHP_EOL);
		}
		fwrite($logfile,$stringout.PHP_EOL);
		fclose($logfile);
	}
	if ($return != 1)
	{
		echo "Error:".$return;
		$logfile = fopen($filename,'a');
		if (!$logfile)
		{
			exit('Unable to open log file!'.PHP_EOL);
		}
		fwrite($logfile,"Error for command:".$cmd.PHP_EOL);
		fwrite($logfile,$return.PHP_EOL);
		fclose($logfile);		
	}
}
echo PHP_EOL;

if ((array_key_exists("c",$options)) || (array_key_exists("clean",$options)))
{
	echo "Cleaning appended files!".PHP_EOL;
	$output=null;
	exec("python clean_appended.py",$output);
	$stringout = implode(PHP_EOL,$output);
	echo $stringout.PHP_EOL;
	$logfile = fopen($filename,'a');
	if (!$logfile)
	{
		exit('Unable to open log file!'.PHP_EOL);
	}
	fwrite($logfile,PHP_EOL.'Cleaning Appended Files'.PHP_EOL);
	fwrite($logfile,$stringout.PHP_EOL.PHP_EOL);
	fclose($logfile);	
}
else
{
	echo "To clean files which have been appended to, run the following command:".PHP_EOL;
	echo "python clean_appended.py".PHP_EOL;
}

?>