<?php

$verbose=FALSE;

require 'headfoot.php';
require 'iso.php';

head("cluster");

require 'meta_file_functions.php';

define("EXTMODECOMMAND_INITIATE","SFGMJ059 SFGMJ064 SFGMSEXT");
define("EXTMODECOMMAND_TERMINATE","SFGMJ065 SFGMJ050");
define("INITIATE",1);
define("TERMINATE",2);
define("RAW","/cluster/data/raw/");
define("EXT","/cluster/data/extended/");

$filename=$_GET["filename"];

function fgetb($handle)
{
	return ord(fgetc($handle));
}

function ignore($handle,$count)
{
	for($n=0;$n<$count;$n++)
		fgetc($handle);
}

// Input time of Extended Mode Block *Dump* (as unix time in seconds)
// Output time of Extended Mode Entry (as Unix time in seconds)

function lastextendedmode($unixtime,$sc,$type)
{
	global $verbose;

	if ($type==INITIATE)
		$searchstring=EXTMODECOMMAND_INITIATE;
	elseif ($type==TERMINATE)
		$searchstring=EXTMODECOMMAND_TERMINATE;
	else
		$searchstring="";

	$fromday=(int)($unixtime/86400)*86400;
	$extmode=0;

	for($n=$fromday;$n>($fromday-10*86400);$n-=86400)
	{
		$filename=RAW.sprintf("%04d",date("Y",$n))."/".sprintf("%02d",date("m",$n))."/C".$sc."_".sprintf("%6s",date("ymd",$n))."_B.SCCH";
//		echo ">>".$filename."<<";
//		echo ">>".$filename."<<";
		if ($verbose)
			echo "<HR>".$n." ".$filename."<BR>";
		if (file_exists($filename))
		{
			$handle=fopen($filename,"r");
			if ($handle)
			{
				while (!feof($handle))
				{
					for($dummy=0;$dummy<15;$dummy++) fgetc($handle);
					$line[]=fgets($handle,256);
				}
				fclose($handle);
				rsort($line);
				for($m=0;$m<count($line);$m++)
				{
					if (strstr($line[$m],"FGM") && $verbose)
						echo "<FONT SIZE=-3>".$line[$m]."</FONT><BR>";
					if (strstr($searchstring,substr($line[$m],61,8)))
					{
						$event=mktime(substr($line[$m],11,2),substr($line[$m],14,2),substr($line[$m],17,2),substr($line[$m],5,2),substr($line[$m],8,2),substr($line[$m],0,4));
						if ($event<$unixtime)
						{
							$extmode=$event;
							break 2;
						}
					}
				}
			}
		}
	}

	return $extmode;
}

function spin($unixtime,$sc)
{
	$year=date("y",$unixtime);
	$month=date("m",$unixtime);
	$day=date("d",$unixtime);
	if (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_K.SATT'))
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_K.SATT';
	elseif (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_B.SATT'))
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_B.SATT';
	elseif (file_exists(RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_A.SATT'))
		$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_A.SATT';
	else
		return 4;

	if ($satt_h=fopen($satt_name,"rb"))
	{
		ignore($satt_h,15);
		$satt_line=fgets($satt_h,100);
		fclose($satt_h);
		return 60/substr($satt_line,61,9);
	}
	else
		return 4;
}


// echo $filename.".META";

$numberofblocks=read_meta($filename.".META","NumberOfBlocks");

$bits=explode("/",$filename);

// 01234567890
// C1_020304_B

$sc=substr($bits[count($bits)-1],1,1);
$vers=substr($bits[count($bits)-1],-1,1);
$src_date=mktime(0,0,0,substr($bits[count($bits)-1],5,2),substr($bits[count($bits)-1],7,2),substr($bits[count($bits)-1],3,2));

echo '<H1>Meta File: '.$filename.'</H1>';

for($n=0;$n<$numberofblocks;$n++)
{
	
	// The $filename.".META" metafile is at the location of the source data file, and contains the date of where the
	// Extended Mode starts in the $start variable.
	
	// The $where_filename metafile is at the location where Extended Mode starts from the $start variable and contains
	// the location of the source data file and block (from 
	
	echo "<B>Block ".$n."</B><BR>";
	$start=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,INITIATE);
	$end=lastextendedmode(read_meta($filename.".META","DumpStartTime_Unix",$n),$sc,TERMINATE);
	$part=read_meta($filename.".META","PartialStart",$n);


	
	$where_filename=EXT.date("Y/m/",$start)."C".$sc."_".date("ymd",$start)."_".date("His",$start)."_".$vers.".META";
	
	if (!file_exists(EXT.date("Y",$start)))			mkdir(EXT.date("Y",$start));
	if (!file_exists(EXT.date("Y/m",$start)))		mkdir(EXT.date("Y/m",$start));
	if (!file_exists($where_filename))				touch($where_filename);
	
	$found_date=read_meta($where_filename,"FoundDate_Unix");
	$found_block=read_meta($where_filename,"FoundBlock");
	if ($found_date!="")
	{
		if ($src_date<$found_date)
		{
			echo "This date/block is Better<BR>";
			$good_to_do_stage3=TRUE;
			write_meta($where_filename,"FoundDate_Unix",$src_date);
			write_meta($where_filename,"FoundDate_ISO",unix2iso($src_date));
			write_meta($where_filename,"FoundBlock",$n);
		}
		elseif ($src_date==$found_date)
		{
			if ($n<$found_block)
			{
				echo "This block is Better<BR>";
				$good_to_do_stage3=TRUE;
				write_meta($where_filename,"FoundBlock",$n);
			}
			elseif ($n==$found_block)
			{
				echo "This is the Existing (Date same then block same)<BR>";
				$good_to_do_stage3=TRUE;
			}
			else
			{
				echo "Existing is better (Date same then block greater)<BR>";
				$good_to_do_stage3=FALSE;
			}
		}
		else
		{
			echo "Existing is better (Date newer)<BR>";
			$good_to_do_stage3=FALSE;
		}
	}
	else
	{
		echo "This is New<BR>";
		$good_to_do_stage3=TRUE;
		write_meta($where_filename,"FoundDate_Unix",$src_date);
		write_meta($where_filename,"FoundDate_ISO",unix2iso($src_date));
		write_meta($where_filename,"FoundBlock",$n);
	}
	if ($good_to_do_stage3)
	{
		echo "<FONT COLOR=\"#00D000\"><B>This Block should be processed further</B></FONT><BR>";
	}
	
	echo "Dump Start ".read_meta($filename.".META","DumpStartTime_ISO",$n)."<BR>";
	if ($part=="TRUE")
		echo "<FONT COLOR=\"#F000C0\">Probable repeat copy</FONT><BR>";
	echo "Extended Mode Entry: ".date("Y-m-d\TH:i:s\Z",$start)."<BR>";
	echo "Extended Mode Exit: ".date("Y-m-d\TH:i:s\Z",$end)."<BR>";
	echo "Extended Mode Duration: ".date("H:i:s",$end-$start)."<BR>";
	$spin=spin($start,$sc);
	printf("Spin period: %0.6f<BR>",$spin);
	$calcvec=(int)(($end-$start)/$spin);
	$actualvec=read_meta($filename.".META","NumberOfVectors",$n);
	echo "Derived Number of vectors : ".$calcvec."<BR>";
	echo "Number of vectors in block : ".$actualvec."<BR>";
	if (abs($calcvec-$actualvec)>0)
	{
		if (abs($calcvec-$actualvec)>10)
			echo "<FONT COLOR=\"RED\">";
		else
			echo "<FONT COLOR=\"BLACK\">";
		echo "Timing suggests ".(int)(($calcvec-$actualvec)/444.5)." packets missing";
		if ($part)
			echo " - This block is partial, so this is not unexpected";
		echo "</FONT><BR>";
	}
	$miss=read_meta($filename.".META","MissingPacket",$n);
	if ($miss!=0)
		echo "<FONT COLOR=RED>State machine suggests, at least ".$miss." packets missing</FONT><BR>";
	$reset_start=read_meta($filename.".META","ResetCountStart",$n);
	$reset_stop=read_meta($filename.".META","ResetCountEnd",$n);
	printf("Reset range: %d-%d / %03X-%03X<BR>",$reset_start,$reset_stop,$reset_start,$reset_stop);
	echo "<P>";
	write_meta($filename.".META","ExtendedModeEntry_ISO",date("Y-m-d\TH:i:s\Z",$start),$n);
	write_meta($filename.".META","ExtendedModeEntry_Unix",$start,$n);
	write_meta($filename.".META","ExtendedModeExit_ISO",date("Y-m-d\TH:i:s\Z",$end),$n);
	write_meta($filename.".META","ExtendedModeExit_Unix",$end,$n);
	write_meta($filename.".META","SpinPeriod",round($spin,6));
	
	
}

foot("cluster");

?>