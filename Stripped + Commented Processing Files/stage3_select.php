<?php
/*
Delete the following 3 lines, AND LAST LINE for deployment, or figure out why permission to normal session folder are denied
*/
session_destroy();
ini_set('session.save_path','/home/ahk114'. '/testing/'. 'session/'); 
session_start();

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

$filepicked = NULL;
$this_event_date = NULL;
$year=2016;
$month = 1;
$day = 1;
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

						if (abs($resetperiod-$vectorperiod)>(16*RESET_PERIOD))  // Reset Count only good to 16*RESET PERIOD
							#echo "<BR><FONT COLOR=RED>Vec/Reset Mismatch</FONT>";

						if ($bspc!=0)
							#echo "<BR><FONT COLOR=RED>BSPC : ".$bspc."</FONT>";

						$this_event_date=read_meta($filename.".META","ExtendedModeEntry_ISO",$ext);
						echo "Reading this event date: ".$filename.".META"."  ".$ext."     :".read_meta($filename.".META","ExtendedModeEntry_ISO",$ext).PHP_EOL;
						$this_event_block=$ext;
						
						$entry=read_meta($filename.".META","ExtendedModeEntry_Unix",$ext);

						$extmodeentrymetafile=EXT."/".date("Y",$entry)."/".date("m",$entry)."/C".$sc."_".date("ymd",$entry)."_".chr(ord("A")+$age).".META";
						
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
						
						if ((read_meta($extmodeentrymetafile,"EventTime_ISO",chr(ord("A")+$index))==$this_event_date) and (read_meta($extmodeentrymetafile,"Block",chr(ord("A")+$index))==$this_event_block))
							{	
							#echo "<FONT COLOR=\"#40FF40\"><B>Recommended</B></FONT>";
							$filepicked = $filename."/C".$sc."_".date("ymd",mktime(0,0,0,$month,$day,$year))."_".chr(ord("A")+$age).".E".$ext;
							break 3; 
							}
						
					#$used=TRUE;
					
					
					}
				}
			}
	}
}

echo "File picked: ".PHP_EOL;
echo $filepicked.PHP_EOL;



session_destroy();
?>
