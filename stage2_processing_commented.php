<?php
# comments are Cary Colgan's when reviewing the code as a UROP placement in the Summer 2015. Detail specific actions in a line, form the point of view of someone familiar with coding, but not immediately with the php language.
/** comments are Cary Colgan's (Summer 2015) synoptic comments of the code, if a review is needed at a quick glance. Used in the form of function blurbs */
// comments are the original in line comments added by Tim Oddy when he originally wrote the code, circa 2001.
##AKR commments

$verbose=FALSE;																	#global boolean, set if debugging required, ignore commands involving it

require 'headfoot.php';															#php file constructing the HTML banners

head("cluster");

require 'meta_file_functions.php';

define("EXTMODECOMMAND_INITIATE","SFGMJ059 SFGMJ064 SFGMSEXT");					#string to recognise extended mode commands in the .SCCH files
define("EXTMODECOMMAND_TERMINATE","SFGMJ065 SFGMJ050");
define("INITIATE",1);
define("TERMINATE",2);
define("RAW","/cluster/data/raw/");												#shortcut to raw data directory

$filename=$_GET["filename"];													#This assigns the variable to the information in the web address. Automatically super global.
																				#$filename is only then changed in one scope when using the corresponding .SCCH file
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
			echo "<HR>".$n." ".$filename."<BR>";
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
				rsort($line);													#reverses array
				for($m=0;$m<count($line);$m++)									#iterating over the entire length of the array, but breaks at first entry
				{
					if (strstr($line[$m],"FGM") && $verbose)
						echo "<FONT SIZE=-3>".$line[$m]."</FONT><BR>";
					if (strstr($searchstring,substr($line[$m],61,8)))			#checks column 61 of the copy of the line in the .SCCH file. This is where the extended mode switch command will be
					{
						$event=mktime(substr($line[$m],11,2),substr($line[$m],14,2),substr($line[$m],17,2),substr($line[$m],5,2),substr($line[$m],8,2),substr($line[$m],0,4));
						#event is a unix timestamp using the relevant information from when the command was issued in the 
						
						if ($event<$unixtime)									#The command cannot have occurred before the BM3 dump.
						{														#breaks loop after finding first, so last in actual time, valid entry.
							$extmode=$event;
							break 2;											#so if this is invalid for the day prior to the extended mode switch, then checks the day before etc.
						}
					}
				}
			}
		}
	}
	
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


// echo $filename.".META";

$numberofblocks=read_meta($filename.".META","NumberOfBlocks");				#stage1_processing.php calculates the block count in extended mode and writes it to the .META file

$bits=explode("/",$filename);												#Each section (defined by the separator /) is written as separate elements of an array

$sc=substr($bits[count($bits)-1],1,1);										#searches the sections of the HTML web address for the spacecraft number.

echo '<H1>Meta File: '.$filename.'</H1>';									#header across the web page of file

for($n=0;$n<$numberofblocks;$n++)											#iterate over the number of blocks in the extended mode data as found by stage1_processing.php
{
	echo "<B>Block ".$n."</B><BR>";
	$start=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,INITIATE);
	echo "$start";
	$end=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,TERMINATE);
	$part=read_meta($filename.".META","PartialStart",$n);
	echo "Dump Start ".read_meta($filename.".META","DumpStartTime_ISO",$n)."<BR>";		#Gets the extended mode command times using the function above
	if ($part=="TRUE")
		echo "<FONT COLOR=\"#F000C0\">Probable repeat copy</FONT><BR>";					#prints a pink alert on the webpage of partial block ??What is part? Partial block? Partial extended mode duration overlap in time?
	echo "Extended Mode Entry: ".date("Y-m-d\TH:i:s\Z",$start)."<BR>";
	$cary["Extended Mode Entry "."$n".":"] = date("Y-m-d\TH:i:s\Z",$start);
	echo "Extended Mode Exit: ".date("Y-m-d\TH:i:s\Z",$end)."<BR>";
	$cary["Extended Mode Exit "."$n".":"] = date("Y-m-d\TH:i:s\Z",$end);
	echo "Extended Mode Duration: ".date("H:i:s",$end-$start)."<BR>";					#duration time found from subtracting start from the end time
	$cary["Extended Mode Duration "."$n".":"] = date("H:i:s",$end-$start);
	$spin=spin($start,$sc);
	printf("Spin period: %0.6f<BR>",$spin);												#this is acquired from the .SATT file
	$cary["spin period "."$n".":"] = $spin;
	$calcvec=(int)(($end-$start)/$spin);												#number of vectors found from duration of extended mode and spin period NOT from extended mode data.
	$actualvec=read_meta($filename.".META","NumberOfVectors",$n);						#number of vectors as found from the extended mode data via stage1_processing.php
	echo "Derived Number of vectors : ".$calcvec."<BR>";
	echo "Number of vectors in block : ".$actualvec."<BR>";
	
	$carykeys = array_keys($cary);
	$caryvalues = array_values($cary);
	$m = count($cary);
	for($i=0; $i<=($m-1); $i++)
		$caryfinal[] = "$carykeys[$i]"." "."$caryvalues[$i]";
	
	if (abs($calcvec-$actualvec)>0)
	{
		if (abs($calcvec-$actualvec)>10)												#If expected number of vectors (from .SATT) is greater than the actual data recieved by 10 then;
			echo "<FONT COLOR=\"RED\">";												#?? Why 10 the threshold for a cause for alarm, arbitrary choice?
		else
			echo "<FONT COLOR=\"BLACK\">";
		echo "Timing suggests ".(int)(($calcvec-$actualvec)/444.5)." packets missing";	#???444.5 number of vectors in a packet in extended mode. As BM3 packet contains 3562 bytes of data one complete vector is 64 bits long.
		if ($part)
			echo " - This block is partial, so this is not unexpected";					#??Cause for difference is always blamed on the partial block. Is this always the case?
		echo "</FONT><BR>";																#linebreak in HTML regardless of error messages posted or not
	}
	$miss=read_meta($filename.".META","MissingPacket",$n);								#variable created in stage1_processing.php
	if ($miss!=0)
		echo "<FONT COLOR=RED>State machine suggests, at least ".$miss." packets missing</FONT><BR>";	#?? state machine involved in stage1_processing.php
	$reset_start=read_meta($filename.".META","ResetCountStart",$n);						#Counts of the 5.152s reset pulse sent to instrument. Found in stage1_processing.php
	$reset_stop=read_meta($filename.".META","ResetCountEnd",$n);
	printf("Reset range: %d-%d / %03X-%03X<BR>",$reset_start,$reset_stop,$reset_start,$reset_stop);		#prints reset range in decimal and hexadecimal 
	echo "<P>";																					#finishes by printing small white space on webpage
	write_meta($filename.".META","ExtendedModeEntry_ISO",date("Y-m-d\TH:i:s\Z",$start),$n);		#?? used later on- but not utilised at the moment
	write_meta($filename.".META","ExtendedModeEntry_Unix",$start,$n);
	write_meta($filename.".META","ExtendedModeExit_ISO",date("Y-m-d\TH:i:s\Z",$end),$n);
	write_meta($filename.".META","ExtendedModeExit_Unix",$end,$n);
	write_meta($filename.".META","SpinPeriod",round($spin,6));
	
	$impcary = implode(", ", $caryfinal);
	$caryfilename = substr($filename, -11);
	file_put_contents("$caryfilename"."_information.txt", $impcary);					#saves to my www directory - permission denied in my own directory
}

foot("cluster");

?>