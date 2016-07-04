<?php
#, /* */AKR comments

/*
Delete the following line for deployment or figure out why permission to normal session folder are denied
*/
session_destroy();
require 'meta_file_functions.php';

define("RAW","/cluster/data/raw/");
define("EXT",'/home/ahk114/extended/');
define("CAL",'/cluster/caa/calibration/');

$verbose = TRUE;

function calfile_array($Year,$month,$day,$sc)
{	
	global $verbose;
	
	$cmd = 'find '.CAL.' -name "C'.$sc.'_CC_FGM_CALF__'.$Year.$month.$day.'_*'.'"';
	#$cmd = 'find '.CAL.' -name "C'.$sc.'_CC_FGM_CALF__'.$Year.$month.'*'.'"'; #this would be for a whole month -testing
	if ($verbose)
	{
		echo "Executing:".$cmd;
	}
	exec($cmd,$output);
	if ($verbose)
	{
		echo PHP_EOL."output:".PHP_EOL;
		var_dump($output);
		echo PHP_EOL;
	}
	$calfiles = array();
	$values = array();
	foreach ($output as $value)
	{
		if (substr($value,0,strlen(CAL)))
		{
			$calfiles[] = $value;
			if ($verbose)
			{
				echo "filename:                 ".$value.PHP_EOL;
			}
		}
		else
		{
			$values[] = $value;
			echo "No calfile:".$value.PHP_EOL;
		}
	}
	$output = array($calfiles,$values);
	return $output;
}	

function calfile_select($calfiles)
{
	global $verbose;
	
	if (count($calfiles) > 1)
	{
		echo "Multiple versions, calfile count:".count($calfiles).PHP_EOL;
		foreach ($calfiles as $calfile)
		{
			$versions[] = substr($calfile,strpos($calfile,"_V")+2,2);
		}
		echo "Versions array".PHP_EOL;
		var_dump($versions); 					#sort this array to get highest version, then use the index to get highest calfile
		arsort($versions);
		$keys = array_keys($versions);
		$highest_key = $keys[0];
		$calfile = $calfiles[$highest_key];
		return $calfile;
	}
	elseif(count($calfiles) == 1)
	{
		$calfile = $calfiles[0];
		return $calfile;
	}	
	else
	{
		return 0;
	}
}


#filepicked in my case, eg. /home/ahk114/extended/2016/01/C1_160101_B.E0
function getcalfile($filepicked)
{
	global $verbose;
	
	$block = substr($filepicked,strlen($filepicked)-1,1);
	$sc=substr(basename($filepicked),1,1);
	$meta_file = substr($filepicked,0,strlen($filepicked)-2).'META';
	echo "Meta File:".$meta_file.PHP_EOL;
	if (!(file_exists($meta_file))){exit("getcalfile, meta file not found!".PHP_EOL);}
	if (!(filesize($meta_file))){exit("getcafile, Meta file empty!".PHP_EOL);}
	$extmodeentry_unix = read_meta($meta_file,"ExtendedModeEntry_Unix",$block);
	if ($verbose && $extmodeentry_unix)
	{
		echo "Extended mode entry:".$extmodeentry_unix.PHP_EOL;
	}
	if (!($extmodeentry_unix))
	{
		exit("No extended mode data in this dump!".PHP_EOL);
	}
	$version_list = array('B','K','A');
	$found = FALSE;
	
	for($time_unix = $extmodeentry_unix; $time_unix > ($extmodeentry_unix-10*86400); $time_unix-=86400)
	{
		foreach ($version_list as $ver)
		{
			$steffile = RAW.date('Y',$time_unix).'/'.date('m',$time_unix).'/'.'C'.$sc.'_'.date('ymd',$time_unix).'_'.$ver.'.STEF';	
			if (file_exists($steffile) && filesize($steffile))
			{
				break;
			}
			else
			{
				echo "getcalfile, empty or missing stef file version ".$ver.PHP_EOL;
			}
		}
		#do we need to do anything if stef file doesn't exist/is empty? 
		#Or can we just look for the previous one as is being done atm?
		if ($verbose)
		{
			echo "getcalfile, trying to use:".$steffile.PHP_EOL;
		}

		$handle = fopen($steffile,"rb");
		if ($handle)
		{
			while (($line = fgets($handle)) !== false)	#reads file line by line until START REVOLUTION string is found
			{
				if (strpos($line, "START REVOLUTION"))
				{
					if ($verbose)
					{
						echo "found line:".$line;
					}
					$found = TRUE;
					break 2;
				}
			}
			echo "Trying to find START REVOLUTION entry in STEF file for previous day!".PHP_EOL;
		}
	}	
	
	$Year = substr($line,27,4);
	$month = substr($line,32,2);
	$day = substr($line,35,2);
	$hours = substr($line,38,2);
	$minutes = substr($line,41,2);
	$seconds = substr($line,44,2);
	if ($verbose)
	{
		echo "YYYY MM DD".PHP_EOL.$Year.' '.$month.' '.$day.PHP_EOL;	
	}
	$output = calfile_array($Year,$month,$day,$sc);
	$calfiles = $output[0];
	if ($calfile = calfile_select($calfiles))
	{
		echo "Calibration file selected:".$calfile.PHP_EOL;		
	}
	else
	{
		$halfday_unix = 86400/2;
		$day_unix = 86400;
		$daytime_unix = mktime($hours,$minutes,$seconds,$month,$day,$Year)-mktime(0,0,0,$month,$day,$Year);
			
		if ($daytime_unix < $halfday_unix && $daytime_unix > 0)
		{
			echo "No calibration file for the START REVOLUTION parameter time found, trying day before then after".PHP_EOL;
			$output = calfile_array($Year,$month,$day-1,$sc);
			$calfiles = $output[0];
			if ($calfile = calfile_select($calfiles))
			{
				echo "Calibration file selected:".$calfile.PHP_EOL;				
			}
			else
			{
				echo "No calibration file for day before found, trying day after".PHP_EOL;
				$output = calfile_array($Year,$month,$day+1,$sc);
				$calfiles = $output[0];
				if($calfile = calfile_select($calfiles))
				{
					echo "Calibration file selected:".$calfile.PHP_EOL;					
				}
				else
				{
					exit("No calibration file found for day, day before or day after!".PHP_EOL);
				}
			}
		}
		elseif ($daytime_unix >= $halfday_unix && $daytime_unix <= $day_unix)
		{
			echo "No calibration file for the START REVOLUTION parameter time found, trying day after then before".PHP_EOL;
			$output = calfile_array($Year,$month,$day+1,$sc);
			$calfiles = $output[0];
			if ($calfile = calfile_select($calfiles))
			{
				echo "Calibration file selected:".$calfile.PHP_EOL;				
			}
			else
			{
				echo "No calibration file for day before found, trying day after".PHP_EOL;
				$output = calfile_array($Year,$month,$day-1,$sc);
				$calfiles = $output[0];
				if($calfile = calfile_select($calfiles))
				{
					echo "Calibration file selected:".$calfile.PHP_EOL;					
				}
				else
				{
					exit("No calibration file found for day, day before or day after!".PHP_EOL);
				}
			}
		}
		else
		{
			exit("Timing information from stef file is wrong".PHP_EOL);
		}
	}
	return $calfile;
}

/* Testing */
/*
#$filepicked = "/home/ahk114/extended/2015/03/C4_150305_B.E0";
$filepicked = "/home/ahk114/extended/2016/01/C1_160108_B.E0";
getcalfile($filepicked);
*/
?>