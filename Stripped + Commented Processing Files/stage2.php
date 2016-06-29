<?php
# comments are Cary Colgan's when reviewing the code as a UROP placement in the Summer 2015. Detail specific actions in a line, form the point of view of someone familiar with coding, but not immediately with the php language.
/** comments are Cary Colgan's (Summer 2015) synoptic comments of the code, if a review is needed at a quick glance. Used in the form of function blurbs */
// comments are the original in line comments added by Tim Oddy when he originally wrote the code, circa 2001.
##AKR commments

/*
Delete the following 3 lines, AND LAST LINE for deployment, or figure out why permission to normal session folder are denied
*/
session_destroy();
ini_set('session.save_path','/home/ahk114'. '/testing/'. 'session/'); 
session_start();
$verbose=TRUE;																	#global boolean, set if debugging required, ignore commands involving it

echo "Starting Stage2".PHP_EOL;

require 'meta_file_functions.php';

define("EXTMODECOMMAND_INITIATE","SFGMJ059 SFGMJ064 SFGMSEXT");					#string to recognise extended mode commands in the .SCCH files
define("EXTMODECOMMAND_TERMINATE","SFGMJ065 SFGMJ050");
define("INITIATE",1);
define("TERMINATE",2);
define("RAW","/cluster/data/raw/");												#shortcut to raw data directory

#eg. /cluster/data/extended/2016/01/C1_160101_B
# in my case, /home/ahk114/extended/2016/01/C1_160101_B
$stdin_input=file_get_contents("php://stdin",'r');
$filename = substr($stdin_input,strpos($stdin_input, 'target')+6,41);			#now extracts filename from stdin, not URL

function fgetb($handle)
	/** Returns the ASCII value of the current character in the handle (Handle is often the .SCCH file). ##.SCCH files are S/C command files.
	
	This function is NOT used in this script, but was important in stage1_processing.php. I assume it can be deleted here.
	*/
{
	return ord(fgetc($handle));
}

function ignore($handle,$count)				
	/** Used to ignore the first $count characters in the handle. Doesn't return anything, just effectively shifts "cursor" through file. 
	
	Used in this script to skip binary information at the start of the .SATT file as this would corrupt the data if you attempted to import 
	it as a string. This .SATT file has important information about the spin period. You have the same issue with importing information from 
	the .SCCH files, but the code is repeated rather than the function called. I assume this was accidental.
	*/
{
	for($n=0;$n<$count;$n++)
		fgetc($handle); #moves character along handle n places from the start
}

// Input time of Extended Mode Block *Dump* (as unix time in seconds)
// Output time of Extended Mode Entry (as Unix time in seconds)

function lastextendedmode($unixtime,$sc,$type)
	/** Takes as inputs a unixtime (in seconds), a spacecraft number and a command (Either initiate or terminate extended mode).
	Returns a unixtime (in seconds) of when the command was executed.
	
	This function is used in THIS script by reading the DumpStartTime_Unix from the .META file (this variable is created in 
	stage1_processing.php in the WriteEntireBlock() function) to find the extended mode command times, and hence the extended mode interval.
	The DumpStartTime_Unix is the time of the BM3 dump and the function looks back over all the commands 10 days prior to this time.
	
	Potential issue as only checks the last 10 days prior to the BM3 dump time?
	Potential issue as assumes the time of the LATEST command is always the true time the extended mode switch occurred. Is this always true?
	Potential issue as dictated by BM3 dump times, so assumes all extended mode data is given in a BM3 dump and that a BM3 dump always follows 
	an extended mode termination, before the next extended mode starts. Was this true when extended mode first started being implemented?
	*/
{
	global $verbose;															
	
	if ($type==INITIATE){
		$searchstring=EXTMODECOMMAND_INITIATE;
		}
	elseif ($type==TERMINATE){
		$searchstring=EXTMODECOMMAND_TERMINATE;
		}
	else
		$searchstring="";														#Just a back up. Only first two types are ever used, but type can be third type which is "partially started" - see stage1_processing.php WriteEntireBlock() function

	$fromday=(int)($unixtime/86400)*86400;										#rounds down to find the day (86,400s) that $unixtime corresponds to
	$extmode=0;

	for($n=$fromday;$n>($fromday-10*86400);$n-=86400)							#iterates the following process counting back from current day number to 10th day prior - in case no command issued day before mode switch
	{
		$filename=RAW.sprintf("%04d",date("Y",$n))."/".sprintf("%02d",date("m",$n))."/C".$sc."_".sprintf("%6s",date("ymd",$n))."_B.SCCH";	#SCCH file address in the raw data directory
		if ($verbose)
			echo $n." ".$filename.PHP_EOL;
		if (file_exists($filename))												#If the .SCCH for that day even exists
		{
			$handle=fopen($filename,"r");										#if it exists open that .SCCH. $handle is the currently open .SCCH file

			if ($handle)														#just incase opening the file is invalid
			{
				while (!feof($handle)){											#iterating through to the end of the .SCCH file
				
					for($dummy=0;$dummy<15;$dummy++) fgetc($handle);			#cuts out the first 15 characters of the .SCCH file. Whatever these characters are (binary?), they can't be easily displayed in HTML either. #by specifying $dummy++ in the for loop, it calls the argument BEFORE incrementing, so loop is effectively while 0<n<15.
					$line[]=fgets($handle,256);									#appends the rest of that entire line to an array, so array gradually built up.
				}
				fclose($handle);												#closes the .SCCH file
				rsort($line);													##sorts array from highest to lowest (reverse order)
				for($m=0;$m<count($line);$m++)									#iterating over the entire length of the array, but breaks at first entry
				{
					if (strstr($searchstring,substr($line[$m],61,8)))			#checks column 61 of the copy of the line in the .SCCH file. This is where the extended mode switch command will be
					{
						$event=mktime(substr($line[$m],11,2),substr($line[$m],14,2),substr($line[$m],17,2),substr($line[$m],5,2),substr($line[$m],8,2),substr($line[$m],0,4));
						#event is a unix timestamp using the relevant information from when the command was issued in the 
						
						if ($event<$unixtime)									#The command cannot have occurred before the BM3 dump.
						{														#breaks loop after finding first, so last in actual time, valid entry.
							$extmode=$event;
							break 2;											#so if this is invalid for the day prior to the extended mode switch, then checks the day before etc.
						}														##break2 breaks out of 2 nexted enclosing structures
					}
				}
			}
		}
	}
	if ($verbose)
		echo "Return value: ".$extmode.PHP_EOL;
	return $extmode;
}


function spin($unixtime,$sc)
	/** Takes as input a unixtime (in seconds) and a spacecraft number.
	Returns a spin period based on the data in the Satellite Attitude File (.SATT) corresponding to the unixtime given.
	Priority is given to the CD version (_K), then to the 10 day pull (_B), then to the single day pull (_A) files to get the relevant spin period.
	If no such .SATT file exists then the period of the spin is defaulted to be 4s.
	
	This function is used in THIS script, to find the "Derived Number of Vectors" (As printed on the HTML) by taking the time elapsed in 
	extended mode and dividing by the spin time period, found by this function. This is then the expected number of spin averaged vectors in the 
	extended mode data. This can be compared with the "Actual Number of Vectors" as calculated for each block in stage1_processing.php and indicates
	missing data etc. 
	
	Possible issue as script later pins difference between the Actual and Derived to be due to a partial packet (as described in stage1_processing.php)
	but is this always the sole culprit?
	
	How is this spin period obtained for the .SATT file? Is this an average over an entire packet?
	Is it important for the extended mode data to reflect changes in this period?
	What about eclipse intervals? In the spin period still reliable then?
	*/
{
	$year=date("y",$unixtime);
	$month=date("m",$unixtime);
	$day=date("d",$unixtime);
	if (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_K.SATT'))				#Series of statements to get the corresponding attitude file. 
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_K.SATT';					#Priority given to _K.SATT, then to _B, then to _A.
	elseif (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_B.SATT'))
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_B.SATT';
	elseif (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_A.SATT'))
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_A.SATT';
	else
		return 4;																						#As this is an approximate spin period for any of Cluster spacecraft

	if ($satt_h=fopen($satt_name,"rb"))																	#open the .SATT file as a binary file
	{
		ignore($satt_h,15);																				#ignore function to skip 15 characters in (as these are un-viewable)
		$satt_line=fgets($satt_h,100);																	#gets the 100 character line
		fclose($satt_h);
		return 60/substr($satt_line,61,9);																#Character 61 of the first line contains the spin period in 9 digits
	}																									#Spin value in the .SATT file is (average?) number of spins in 60s
	else
		return 4;
}

$numberofblocks=read_meta($filename.".META","NumberOfBlocks");				#stage1_processing.php calculates the block count in extended mode and writes it to the .META file

$bits=explode("/",$filename);												#Each section (defined by the separator /) is written as separate elements of an array

$sc=substr($bits[count($bits)-1],1,1);										#searches the sections of the HTML web address for the spacecraft number.

echo "number of blocks: ".$numberofblocks.PHP_EOL;

for($n=0;$n<$numberofblocks;$n++)											#iterate over the number of blocks in the extended mode data as found by stage1_processing.php
{
	$start=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,INITIATE);
	$end=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,TERMINATE);
	$part=read_meta($filename.".META","PartialStart",$n);
	$cary["Extended Mode Entry "."$n".":"] = date("Y-m-d\TH:i:s\Z",$start);
	$cary["Extended Mode Exit "."$n".":"] = date("Y-m-d\TH:i:s\Z",$end);
	$cary["Extended Mode Duration "."$n".":"] = date("H:i:s",$end-$start);
	$spin=spin($start,$sc);
	$cary["spin period "."$n".":"] = $spin;
	$calcvec=(int)(($end-$start)/$spin);												#number of vectors found from duration of extended mode and spin period NOT from extended mode data.
	$actualvec=read_meta($filename.".META","NumberOfVectors",$n);						#number of vectors as found from the extended mode data via stage1_processing.php	
	$miss=read_meta($filename.".META","MissingPacket",$n);								#variable created in stage1_processing.php
	$reset_start=read_meta($filename.".META","ResetCountStart",$n);						#Counts of the 5.152s reset pulse sent to instrument. Found in stage1_processing.php
	$reset_stop=read_meta($filename.".META","ResetCountEnd",$n);

	write_meta($filename.".META","ExtendedModeEntry_ISO",date("Y-m-d\TH:i:s\Z",$start),$n);		#?? used later on- but not utilised at the moment
	write_meta($filename.".META","ExtendedModeEntry_Unix",$start,$n);
	write_meta($filename.".META","ExtendedModeExit_ISO",date("Y-m-d\TH:i:s\Z",$end),$n);
	write_meta($filename.".META","ExtendedModeExit_Unix",$end,$n);
	write_meta($filename.".META","SpinPeriod",round($spin,6));
	
	if ($verbose)
	{
		$linecounter = 1;
		echo PHP_EOL;
		echo "++------------------------------------------------------------".PHP_EOL;
		echo "BLOCK NUMBER: ".$n.PHP_EOL;
		echo $linecounter.":".$start.PHP_EOL;
		$linecounter += 1;
		echo $linecounter.":".$end.PHP_EOL;
		$linecounter += 1;
		echo $linecounter.":".$part.PHP_EOL;
		$linecounter += 1;
		echo $linecounter.":".$spin.PHP_EOL;
		$linecounter += 1;
		echo $linecounter.":".$calcvec.PHP_EOL;
		$linecounter += 1;
		echo $linecounter.":".$actualvec.PHP_EOL;
		echo "--------------------------------------------------------------".PHP_EOL;
		echo PHP_EOL;
	}
}

#writing info to file
$carykeys = array_keys($cary);
$caryvalues = array_values($cary);
for($i=0; $i<=(count($cary)-1); $i++)
	$caryfinal[] = "$carykeys[$i]"." "."$caryvalues[$i]";
$impcary = implode("\n", $caryfinal);
$alexfilepath = substr($filename,0,30);
file_put_contents($alexfilepath."_information.txt", $impcary);

if ($verbose)
{
	echo "Writing to info file: ".PHP_EOL;
	echo $impcary.PHP_EOL;
}

session_destroy();
?>