<?php
/*
Delete the following 3 lines, AND LAST LINE for deployment, or figure out why permission to normal session folder are denied
*/
session_destroy();
#ini_set('session.save_path','/home/ahk114'. '/testing/'. 'session/'); 
#session_start();

set_time_limit(5);

require 'meta_file_functions.php';

define("RAW","/cluster/data/raw");
define("EXT",'/home/ahk114/extended');

define("RESET_PERIOD",5.152221);
define("SPIN_PERIOD",4);

function spinrate($year,$month,$day,$sc,$version)
{
	if ($year>=2000) $year-=2000;
	$satt_name=RAW.sprintf("/20%02d/%02d/C%1s_%02d%02d%02d",$year,$month,$sc,$year,$month,$day)."_".$version.'.SATT';

//	echo "<BR>".$satt_name."<BR>";

	if (file_exists($satt_name) && ($satt_h=fopen($satt_name,"rb")))
	{
		fseek($satt_h,15,SEEK_SET);
		$satt_line=fgets($satt_h,100);
		fclose($satt_h);
		$deltatime=60/substr($satt_line,61,9);
	}
	else
	{
		$deltatime=SPIN_PERIOD;
	}

	return $deltatime;
}

$stdin_input=file_get_contents("php://stdin",'r');

$target_pos = strpos($stdin_input, 'target');
if ($target_pos)
{
$filename = substr($stdin_input,$target_pos+6,41);	#file picked starts after "target" string in the input
}
else
{exit("No filename supplied to stage3_select".PHP_EOL);}

echo "Stage2 Input Filename (now in stage3_select): ".$filename.PHP_EOL;
$fileparts = explode("/",$filename);
$year=   substr(end($fileparts),3,2);
if ($year < 2000){$year+=2000;}
$month = substr(end($fileparts),5,2);
$day =   substr(end($fileparts),7,2);

echo "Selected Date: ".date("Y/m/d",mktime(0,0,0,$month,$day,$year)).PHP_EOL;

if (($year!="") && ($month!=""))
{
	for($sc=1;$sc<5;$sc++)
	{
		#echo "<TABLE>";
		unset($scused);
			$startrow=FALSE;
			for($ext=0;$ext<10;$ext++)
			{
				for($age=12;$age>=0;$age--)	#to iterate through letters A to M
				{
					$filename=EXT."/".sprintf("%04d",$year)."/".sprintf("%02d",$month)."/C".$sc."_".sprintf("%02d%02d%02d",$year-2000,$month,$day)."_".chr(ord("A")+$age);
					if ((file_exists($filename.".E".$ext)) && (filesize($filename.".E".$ext)!=0))
					{
						echo "filename: ".$filename.PHP_EOL;
						if (!$startrow) { $startrow=TRUE; }
	
						#echo "<A HREF=stage3_processing.php?filepicked=".$filename.".E".$ext."<C".$sc."_".date("ymd",mktime(0,0,0,$month,$day,$year))."_".chr(ord("A")+$age).".E".$ext."</A>";
						#$filepicked = $filename."/C".$sc."_".date("ymd",mktime(0,0,0,$month,$day,$year))."_".chr(ord("A")+$age).".E".$ext
						#eg. $filepicked=/cluster/data/extended/2016/01/C1_160101_B.E0

						$startreset=read_meta($filename.".META","ResetCountStart",$ext);
						$endreset=read_meta($filename.".META","ResetCountEnd",$ext);
						$numresets=$endreset-$startreset; if ($numresets<0) $numresets+=4096;
						$numresets*=16;
						$resetperiod=$numresets*RESET_PERIOD;
						$bspc=read_meta($filename.".META","	SunPacketCount",$ext);
						$numvec=read_meta($filename.".META","NumberOfVectors",$ext);
						$vectorperiod=$numvec*spinrate($year,$month,$day,$sc,chr(ord("A")+$age));

						#if (abs($resetperiod-$vectorperiod)>(16*RESET_PERIOD))  // Reset Count only good to 16*RESET PERIOD
							#echo "<BR><FONT COLOR=RED>Vec/Reset Mismatch</FONT>";

						#if ($bspc!=0)
							#echo "<BR><FONT COLOR=RED>BSPC : ".$bspc."</FONT>";
						
						#echo "return value of function: ".read_meta($filename.".META","ExtendedModeEntry_ISO",$ext).PHP_EOL;
						$this_event_date=read_meta($filename.".META","ExtendedModeEntry_ISO",$ext);
						echo "Reading this event date: ".$filename.".META"."  ".$ext."     :".$this_event_date.PHP_EOL;
						$this_event_block=$ext;
						$this_source=mktime(0,0,0,$month,$day,$year);
						
						$entry=read_meta($filename.".META","ExtendedModeEntry_Unix",$ext);

						$extmodeentrymetafile=EXT."/".date("Y",$entry)."/".date("m",$entry)."/C".$sc."_".date("ymd",$entry)."_".chr(ord("A")+$age).".META";
						echo "entry meta filename: ".$extmodeentrymetafile.PHP_EOL;
						
						// Search for usable Extended Mode
						$index=0;
						do
						{
							$use=read_meta($extmodeentrymetafile,"Use",chr(ord("A")+$index));
							if (!$use)
								$index++;
						}
						while(!$use and $index<100); #do while loop
						
						#echo "Use : ".$index;
						echo read_meta($extmodeentrymetafile,"EventTime_ISO",chr(ord("A")+$index)).PHP_EOL;
						echo $this_event_date.PHP_EOL;
						echo read_meta($extmodeentrymetafile,"Block",chr(ord("A")+$index)).PHP_EOL;
						echo $this_event_block.PHP_EOL;
						
						if ((read_meta($extmodeentrymetafile,"EventTime_ISO",chr(ord("A")+$index))==$this_event_date) and (read_meta($extmodeentrymetafile,"Block",chr(ord("A")+$index))==$this_event_block))
							{	
							#echo "<FONT COLOR=\"#40FF40\"><B>Recommended</B></FONT>";
							$filepicked = substr($filename,0,29)."/C".$sc."_".date("ymd",mktime(0,0,0,$month,$day,$year))."_".chr(ord("A")+$age).".E".$ext;
							echo "Stage 3 Selection: File picked: ".PHP_EOL;
							echo $filepicked.PHP_EOL;

							fwrite(STDOUT,"target".$filepicked.PHP_EOL);			#write filename base to stdout, for input into stage3!
							
							break 3; 
							}
						echo PHP_EOL;
					#$used=TRUE;
					
					
					}
				}
			}
	}
}

echo "Not found".PHP_EOL;

#session_destroy();
?>
