<?php

#, /* */AKR comments

define("RESETPERIOD",5.152);

define("PREREAD",32768);

require 'meta_file_functions.php';

set_time_limit(120);

// Take a floating point value, and return an array with four bytes (to be passed into the C
// functions which require data types such as fgmtvec.  See the "FGM Data Processing Handbook".

function float2hex($float)
{
	if ($float==0)
		return array(0,0,0,0);
	$sign=$float>0?0:1;
	$float=abs($float);
	$exp=floor(log10($float)/log10(2));
	$remainder=8388608*(($float/pow(2,$exp))-1);
	$upperexp=(int)(($exp+127)/2);
	$lowerexp=(($exp+127)&1);
// 	return array(($sign*128) + $upperexp,
// 	             ($lowerexp*128)+(($remainder>>16)&127),
// 	             ($remainder>>8)&255,
// 	             $remainder&255);
	return array(	$remainder&255,
					($remainder>>8)&255,
					($lowerexp*128)+(($remainder>>16)&127),
					($sign*128) + $upperexp
				);

}

// Take an integer value, and return an array with four bytes (to be passed into the C functions
// which require data types such as fgmtvec.  See the "FGM Data Processing Handbook".

function integer2hex($int)
{
	$int=(int)$int;
//	return array($int>>24,($int>>16)&255,($int>>8)&255,$int&255);
	return array(	$int&255,
					($int>>8)&255,
					($int>>16)&255,
					$int>>24
				);
}

// Extract just the element of a floating point value that is to the right of the decimal point.

function floatbit($real)
{
	$int=(int)$real;
	return $real-$int;
}

// Output a single byte (very inefficient)

function fputb($handle,$value)
{
	fputs($handle,chr($value),1);
}

// Retrieve a single byte, with some handling of constants that I don't think will work with the
// current installation of PHP, so may be utterly redundant!

function fgetb($handle)
{
	global $BUFFER,$AVAILABLE,$HANDLE;

	if (!isset($HANDLE))
	{
		$HANDLE==$handle;
		$AVAILABLE==0;
	}

	if ($handle!=$HANDLE)
	{
		return ord(fgetc($handle));
	}
	else
	{
		if ($AVAILABLE==0)
		{
			$BUFFER=fread($handle,PREREAD);
			$AVAILABLE=strlen($BUFFER);
		}
		return ord(substr($BUFFER,strlen($BUFFER)-($AVAILABLE--),1));
	}
}

// Ignore a number of bytes (probably better done by simply inserting the fseek command directly
// into the code).

function ignore($handle,$count)
{
	fseek($handle,$count,SEEK_CUR);
}

function lastextendedmode($year,$month,$day,$hour,$minute,$second,$sc,$version="B")
{
	$from=mktime($hour,$minute,0,$month,$day,$year);
	$fromday=(int)($from/86400)*86400;
	$extmode=0;

	for($n=$fromday;$n>($fromday-10*86400);$n-=86400)
	{
		$filename=RAW.sprintf("%04d",date("Y",$n))."/".sprintf("%02d",date("m",$n))."/C".$sc."_".sprintf("%6s",date("ymd",$n))."_".$version.".SCCH";
		echo "<HR>".$n." ".$filename."<BR>";
		if (file_exists($filename))
		{
			$handle=fopen($filename,"r");
			if ($handle)
			{
				while (!feof($handle))
				{
					ignore($handle,15);
//					for($dummy=0;$dummy<15;$dummy++) fgetc($handle);
					$line[]=fgets($handle,256);
				}
				fclose($handle);
				rsort($line);
				for($m=0;$m<count($line);$m++)
				{
					if (strstr($line[$m],"FGM"))
						echo "<FONT SIZE=-3>".$line[$m]."</FONT><BR>";
					if (strstr(EXTMODECOMMAND,substr($line[$m],61,8)))
					{
						$event=mktime(substr($line[$m],11,2),substr($line[$m],14,2),substr($line[$m],17,2),substr($line[$m],5,2),substr($line[$m],8,2),substr($line[$m],0,4));
						if ($event<$from)
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
	
function getcal($sc)
{
	global $gainx,$gainy,$gainz,$offsetx,$offsety,$offsetz;

	// [adc 1..2][sensor 0..1 (OB..IB)][sc 1..4][range 2..5]
	//
	// Order in Cal File
	// OB     ADC1
	//    IB  ADC1
	// OB          ADC2
	//    IB       ADC2
	//
	// Range 2, 3, 4, 5, 7
	//
	// Offset X
	// Offset Y
	// Offset Z
	//
	// Gain X
	// ----
	// ----
	//
	// ----
	// Gain Y
	// ----
	//
	// ----
	// ----
	// Gain Z


	echo "Get Calibration for S/C ".$sc."<BR>";
	$cal=fopen("/cluster/operations/calibration/default/C".$sc.".fgmcal","rb");
	if ($cal)
	{
		$dummy=fgets($cal,256); 												#skips first line
		for($adc=1;$adc<3;$adc++)
		{
			for($sensor=0;$sensor<2;$sensor++)
			{
				fscanf($cal,"%f %f %f %f %f %s",&$offsetx[$adc][$sensor][2],	#only takes into account ranges 2,3,4,5 - skips range 7
				                                &$offsetx[$adc][$sensor][3],
				                                &$offsetx[$adc][$sensor][4],
				                                &$offsetx[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);				#here,range 7 and identifier string is skipped (eg. S2_32)

				fscanf($cal,"%f %f %f %f %f %s",&$offsety[$adc][$sensor][2],
				                                &$offsety[$adc][$sensor][3],
				                                &$offsety[$adc][$sensor][4],
				                                &$offsety[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);

				fscanf($cal,"%f %f %f %f %f %s",&$offsetz[$adc][$sensor][2],
				                                &$offsetz[$adc][$sensor][3],
				                                &$offsetz[$adc][$sensor][4],
				                                &$offsetz[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);

				fscanf($cal,"%f %f %f %f %f %s",&$gainx[$adc][$sensor][2],
				                                &$gainx[$adc][$sensor][3],
				                                &$gainx[$adc][$sensor][4],
				                                &$gainx[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);

				$dummy=fgets($cal,256); $dummy=fgets($cal,256); $dummy=fgets($cal,256);	#skips 3 lines (IB sensor values)

				fscanf($cal,"%f %f %f %f %f %s",&$gainy[$adc][$sensor][2],
				                                &$gainy[$adc][$sensor][3],
				                                &$gainy[$adc][$sensor][4],
				                                &$gainy[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);

				$dummy=fgets($cal,256); $dummy=fgets($cal,256); $dummy=fgets($cal,256);

				fscanf($cal,"%f %f %f %f %f %s",&$gainz[$adc][$sensor][2],
				                                &$gainz[$adc][$sensor][3],
				                                &$gainz[$adc][$sensor][4],
				                                &$gainz[$adc][$sensor][5],
				                                &$dummy1,&$dummy2);
			}
		}
	}
	else
	{
		for($adc=1;$adc<3;$adc++)
			for($sensor=0;$sensor<2;$sensor++)
				for($range=2;$range<6;$range++)
				{
					$offsetx[$adc][$sensor][$range]=0;
					$offsety[$adc][$sensor][$range]=0;
					$offsetz[$adc][$sensor][$range]=0;
					$gainx[$adc][$sensor][$range]=1;
					$gainy[$adc][$sensor][$range]=1;
					$gainz[$adc][$sensor][$range]=1;
				}
	}
}


function modifycal($sc)
/*
Takes obtained calibration parameters from getcal() and adapts it to use for the spin-averaged vectors 
obtained in Extended Mode. It is assumed that the offsets in the spin plane cancel due to the 
averaging. Thus, they are assigned 0. The gains in the spin plane are both taken to be the 
average gain of the two spin plane components.
The spin axis component is left unchanged, as it is assumed that averaging has a negligible 
influence on this component.
*/
{
	global $gainx,$gainy,$gainz,$offsetx,$offsety,$offsetz;

	echo "Modify Calibration for S/C ".$sc."<BR>";
	for($adc=1;$adc<3;$adc++)
		for($sensor=0;$sensor<2;$sensor++)
			for($range=2;$range<6;$range++)
			{
				$offsety[$adc][$sensor][$range]=0;
				$offsetz[$adc][$sensor][$range]=0;

				$n=$gainy[$adc][$sensor][$range];
				$m=$gainz[$adc][$sensor][$range];

				$gainy[$adc][$sensor][$range]=($n+$m)/2;
				$gainz[$adc][$sensor][$range]=($n+$m)/2;
			}
}

function displaycal($sc)
{
	global $gainx,$gainy,$gainz,$offsetx,$offsety,$offsetz;

	for($adc=1;$adc<3;$adc++)
	{
		for($sensor=0;$sensor<2;$sensor++)
		{
			echo "S/C ".$sc." ADC ".$adc." Sensor ".$sensor."<BR>";
			for($range=2;$range<6;$range++)
			{
				printf("%d : <FONT COLOR=GRAY>%3.3f,%3.3f,%3.3f %3.3f %3.3f %3.3f</FONT> ",$range,$gainx[$adc][$sensor][$range],$gainy[$adc][$sensor][$range],$gainz[$adc][$sensor][$range],$offsetx[$adc][$sensor][$range],$offsety[$adc][$sensor][$range],$offsetz[$adc][$sensor][$range]);
			}
				echo "<BR>";
		}
	}
}


define("RAW","/cluster/data/raw/");
define("EXTMODECOMMAND","SFGMJ059 SFGMJ064 SFGMSEXT SFGMM002");
define("EXT",'/cluster/data/extended/');
define("PROC",'/cluster/data/reference/');

define("COORD",1);

require("headfoot.php");

head("cluster");

$extsensor=0;
$extadc=1;

$filepicked=$_GET["filepicked"];

echo '<H1>'.$filepicked.'</H1>';

$year=substr(basename($filepicked),3,2);
$month=substr(basename($filepicked),5,2);
$day=substr(basename($filepicked),7,2);
$sc=substr(basename($filepicked),1,1);
$version=substr(basename($filepicked),10,1);

getcal($sc);
echo '<PRE><FONT SIZE=-1>';
displaycal($sc);
echo '</PRE></FONT>';

modifycal($sc);
echo '<PRE><FONT SIZE=-1>';
displaycal($sc);
echo '</PRE></FONT>';


$satt_name=RAW.'20'.$year.'/'.$month.'/C'.$sc.'_'.$year.$month.$day.'_'.$version.'.SATT';

if (file_exists($satt_name) && ($satt_h=fopen($satt_name,"rb")))
{
	ignore($satt_h,15);
	$satt_line=fgets($satt_h,100);
	fclose($satt_h);
	$deltatime=60/substr($satt_line,61,9);
	echo 'Spacecraft Period is '.$deltatime.' seconds.<P>';
}
else
{
	$deltatime=4;
	echo 'Spacecraft Period is 4 seconds (Default).<P>';
}


// $datefile=basename($filepicked);
// $datefile{12}='D';

// $handle=fopen(EXT.'20'.$year.'/'.$month.'/'.$datefile,'rb');
// if ($handle)
// {
	// $dtc=fgets($handle,20);
	// fclose($handle);
// }
// else
	// $dtc=0;

// $start=lastextendedmode(date('Y',$dtc),date('m',$dtc),date('d',$dtc),date('H',$dtc),date('i',$dtc),date('s',$dtc),$sc,$version);

$section=substr($filepicked,-1,1);

echo "META File : ".EXT.'20'.$year.'/'.$month.'/'.substr(basename($filepicked),0,-3).".META"."<BR>";

$start=read_meta(EXT.'20'.$year.'/'.$month.'/'.substr(basename($filepicked),0,-3).".META","ExtendedModeEntry_Unix",$section);

echo "\$start=".$start."<BR>";

$current=$start;

echo "Extended mode entered : ".date("j M Y H:i:s\Z",$start);

// Input format .En
// 0         1         2         3         4         5         6
// 0123456789012345678901234567890123456789012345678901234567890
//
// DDDDDD DDDDDD DDDDDD D SSSSSSSSSSSSSSSSS.........
//   2099  62384  62444 2 WHOLE EVEN 0
//  11691  56725  52276 2 WHOLE EVEN 1
//  11694  56729  52271 2 WHOLE EVEN 2
//  11698  56731  52275 2 WHOLE EVEN 3

// Output format .EXT
// 0         1         2         3         4         5         6
// 0123456789012345678901234567890123456789012345678901234567890
//
// SSSSSSSSSSSSSSSSSSSSSSSS FFFF.FFF FFFF.FFF FFFF.FFF
// 2001-11-16T19:45:56.740Z   15.091    0.000    0.000
// 2001-11-16T19:46:00.750Z   26.887    0.000    0.000
// 2001-11-16T19:46:04.760Z   26.829    0.000    0.000
// 2001-11-16T19:46:08.772Z   26.800    0.000    0.000





$extfile=file($filepicked);

echo '<P>Opening : '.EXT.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT</P>';

if (!is_dir(EXT.date('Y',$start)))
	mkdir(EXT.date('Y',$start),0750);

if (!is_dir(EXT.date('Y/m',$start)))
	mkdir(EXT.date('Y/m',$start),0750);

////////////////////////////////////// *************************

echo ">>>> ".EXT.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT';

$outhandle=fopen(EXT.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT','ab');
if (!$outhandle)
{
	echo '<FONT COLOR=RED>Bugger</FONT>';
	exit -1;
}

$tmp=tempnam('/var/tmp','ExtProcRaw_');
$testhandle=fopen($tmp,'wb'); // NB wb not ab
if (!$testhandle)
{
	echo "BUGGER";
	exit -1;
}


$sattfile=RAW.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.SATT';
$stoffile=RAW.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.STOF';
$procfile=PROC.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT.GSE';

//$testhandle=fopen(EXT.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.G','wb'); // NB wb not ab


//$sattfile=RAW.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.SATT';
//$stoffile=RAW.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.STOF';
//$procfile=PROC.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT.GSE';
//$tmp=tempnam('/var/tmp','ExtProc');
//
// $pipe_h=popen("/raid/cluster/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /raid/cluster/software/dp/bin/fgmpos -p ".$stoffile." | /raid/cluster/software/dp/bin/igmvec -o ".$tmp." ; cat ".$tmp." >> ".$procfile,"wb");


$k=pi()*pi()/16;
$k2=pi()/4;
$time=$start;
// $deltatime=60/$rpm;
echo '<PRE>';

$lastreset=999999;

$loopsize=count($extfile);
$onepercent=(int)($loopsize/100);

for($n=0;$n<$loopsize;$n++)
{
//	echo "\"".trim($extfile[$n])."\"";
	
	sscanf($extfile[$n],"%d %d %d %d %d %s",&$instrx,&$instry,&$instrz,&$range,&$reset,&$comment);

//	echo "   ".$instrx.",".$instry.",".$instrz.",".$range."<BR>";
	
	if (!(($instrx==0 && $instry==0 && $instrz==0 && $range==0) || $range<2 || $range>6 ))
	{
		$deltareset=($reset-$lastreset+4096)%4096; // allow for -ve values (wraparound)

		if (($deltareset)>1 and ($lastreset!=999999))
		{
			// OK, if reset goes up by more than one, then are missing resets for some reason

			// Since Reset count only incs every 16 resets (so every 5.152*16), take this and divide by
			// spin to get rough time/reset increment.

			$time+=$deltatime*($deltareset-1)*16*RESETPERIOD/$deltatime; // remove 1, since already added deltatime on previous iteration

			echo "<FONT COLOR=RED>BIG RESET JUMP : Ammending time by ".($deltareset-1)*16*RESETPERIOD/$deltatime." seconds.</FONT><BR>";


		}

		$lastreset=$reset; // Set lastreset to reset

		$scale=(512>>(($range-2)*2))/2;

		if ($instrx>32767)
			$bx=($instrx-65536)/$scale;
		else
			$bx=$instrx/$scale;

		if ($instry>32767)
			$by=($instry-65536)/$scale;
		else
			$by=$instry/$scale;

		if ($instrz>32767)
			$bz=($instrz-65536)/$scale;
		else
			$bz=$instrz/$scale;

		$bx=$bx*$gainx[$extadc][$extsensor][$range]-$offsetx[$extadc][$extsensor][$range];
//		$bx=$bx-$offsetx[$extadc][$extsensor][$range];
		$by=$by*$k2*$gainy[$extadc][$extsensor][$range]-$offsety[$extadc][$extsensor][$range];
		$bz=$bz*$k2*$gainz[$extadc][$extsensor][$range]-$offsetz[$extadc][$extsensor][$range];
// -> Last Line Removed echo "<BR><FONT COLOR=SILVER>".$gainx[$extadc][$extsensor][$range].",".$gainy[$extadc][$extsensor][$range].",".$gainz[$extadc][$extsensor][$range]." / ".$offsetx[$extadc][$extsensor][$range].",".$offsety[$extadc][$extsensor][$range].",".$offsetz[$extadc][$extsensor][$range]."</FONT><BR>";
//		$stuff=date("Y-m-d\TH:i:s",$time).'.'.sprintf("%03d",((int)(1000*($time-(int)$time)))).'Z '.sprintf("%4.3f %4.3f %4.3f\n",2*sqrt($bx*$bx+$k*$by*$by+$k*$bz*$bz),0,0);
		$stuff=date("Y-m-d\TH:i:s",$time).'.'.sprintf("%03d",((int)(1000*($time-(int)$time)))).'Z '.sprintf("%4.3f %4.3f %4.3f\n",$bx,$by,$bz);

// Hereabouts need to do Reference Frame conversion

	$hexbx=float2hex($bx);
	$hexby=float2hex($by);
	$hexbz=float2hex($bz);
	$time1=integer2hex($time);
	$time2=integer2hex(floatbit($time)*1e9);


// 	$teststuff=array( (($sc-1)<<6)+1,128+(COORD&7),16,($range<<4)+14,
// 	                  $time1[0],$time1[1],$time1[2],$time1[3],
// 	                  $time2[0],$time2[1],$time2[2],$time2[3],
// 	                  $hexbx[0],$hexbx[1],$hexbx[2],$hexbx[3],
// 	                  $hexby[0],$hexby[1],$hexby[2],$hexby[3],
// 	                  $hexbz[0],$hexbz[1],$hexbz[2],$hexbz[3],
// 	                  0,0,0,0,
// 	                  0,0,0,0);
	$teststuff=array(	($range<<4)+14,
						16,
						128+(COORD&7),
						(($sc-1)<<6)+1,
	                  $time1[0],$time1[1],$time1[2],$time1[3],
	                  $time2[0],$time2[1],$time2[2],$time2[3],
	                  $hexbx[0],$hexbx[1],$hexbx[2],$hexbx[3],
	                  $hexby[0],$hexby[1],$hexby[2],$hexby[3],
	                  $hexbz[0],$hexbz[1],$hexbz[2],$hexbz[3],
	                  0,0,0,0,
	                  0,0,0,0);

	}
	else
	{
		$stuff=date("Y-m-d\TH:i:s",$time).'.'.sprintf("%03d",((int)(1000*($time-(int)$time)))).'Z '.sprintf("%4.3f %4.3f %4.3f\n",0,0,0);
// 		$teststuff=array( ($sc-1)<<6+1,128+3,128,14,
// 		                  integer2hex($time),integer2hex(floatbit($time)/1e9),
// 		                  0,0,0,0,
// 		                  0,0,0,0,
// 		                  0,0,0,0,
// 		                  0,0,0,0,
// 		                  0,0,0,0);
		$teststuff=array( 	14,
							128,
							128+3,
							($sc-1)<<6+1,
		                  integer2hex($time),integer2hex(floatbit($time)/1e9),
		                  0,0,0,0,
		                  0,0,0,0,
		                  0,0,0,0,
		                  0,0,0,0,
		                  0,0,0,0);

	}

	fputs($outhandle,$stuff);
	for($i=0;$i<32;$i++)
		fputb($testhandle,$teststuff[$i]);
	// echo substr(str_pad(substr($extfile[$n],0,-1),80,' '),0,80).' <FONT COLOR=GRAY>'.$stuff.'</FONT>';

	if (isset($flibble))
		$flibble++;
	else
		$flibble=1;
	if (($flibble%$onepercent)==0) { echo (int)$flibble/$onepercent."% "; flush(); }
	if ($flibble==($loopsize-1)) echo "<BR>";

	$time+=$deltatime;
	if (date("d",$current)!=date("d",$time))
	{
		echo '<P><FONT COLOR=MAROON>Closing file for '.date("ymd",$current).' and opening file for '.date("ymd",$time).'.</FONT></P>';
		$current=$time;
		fclose($outhandle);
		fclose($testhandle);
		// process file before we generate new one
		$tmp2=tempnam('/var/tmp','ExtProcDecoded_');
		echo "<P><FONT COLOR=RED>FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat ".$tmp." | /cluster/operations/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /cluster/operations/software/dp/bin/fgmpos -p ".$stoffile." | /cluster/operations/software/dp/bin/igmvec -o ".$tmp2." ; cat ".$tmp2." >> ".$procfile."</FONT></P>";
		exec("FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat ".$tmp." | /cluster/operations/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /cluster/operations/software/dp/bin/fgmpos -p ".$stoffile." | /cluster/operations/software/dp/bin/igmvec -o ".$tmp2." ; cat ".$tmp2." >> ".$procfile);

		if (!is_dir(EXT.date('Y',$time)))
			mkdir(EXT.date('Y',$time),0750);

		if (!is_dir(EXT.date('Y/m',$time)))
			mkdir(EXT.date('Y/m',$time),0750);

		$outhandle=fopen(EXT.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.EXT','ab');
		if (!$outhandle)
		{
			echo '<FONT COLOR=RED SIZE=+2>Bugger can\'t open it</FONT>';
			exit -1;
		}

		$tmp=tempnam('/var/tmp','ExtProcRaw_');
		$testhandle=fopen($tmp,'wb'); // NB wb not ab
		$sattfile=RAW.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.SATT';
		$stoffile=RAW.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.STOF';
		$outhandle=fopen(EXT.date('Y/m/',$start).'C'.$sc.'_'.date('ymd',$start).'_'.$version.'.EXT','ab');
		$procfile=PROC.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.EXT.GSE';


//		$testhandle=fopen(EXT.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.G','wb'); // NB wb not ab
//
//		$sattfile=RAW.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.SATT';
//		$stoffile=RAW.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.STOF';
//		$procfile=PROC.date('Y/m/',$time).'C'.$sc.'_'.date('ymd',$time).'_'.$version.'.EXT.GSE';
//		$tmp=tempnam('/var/tmp','ExtProc');

//$pipe_h=popen("/raid/cluster/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /raid/cluster/software/dp/bin/fgmpos -p ".$stoffile." | /raid/cluster/software/dp/bin/igmvec -o ".$tmp." ; cat ".$tmp." >> ".$procfile,"wb");

	}
}
fclose($outhandle);
fclose($testhandle);
//echo ">>>>>>>>>>>>>>>Start of output from popen";
//flush;
//while (!feof($pipe_h))
//		{
//			$dummy=fgets($pipe_h,1024);
//			echo $dummy;
//		}
//echo ">>>>>>>>>>>>>>>End of output from popen";

		$tmp2=tempnam('/var/tmp','ExtProcDecoded_');
		echo "FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat ".$tmp." | /cluster/operations/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /cluster/operations/software/dp/bin/fgmpos -p ".$stoffile." | /cluster/operations/software/dp/bin/igmvec -o ".$tmp2." ; cp ".$tmp2." ".$procfile;
		exec("FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat ".$tmp." | /cluster/operations/software/dp/bin/fgmhrt -s gse -a ".$sattfile." | /cluster/operations/software/dp/bin/fgmpos -p ".$stoffile." | /cluster/operations/software/dp/bin/igmvec -o ".$tmp2." ; cp ".$tmp2." ".$procfile);



echo '</PRE>';

foot("cluster");

?>