<?php

// Name :		ExtMode_stage3_cli_0_1.php
// Author :		Tim Oddy
//				(C) Space Magnetometer Laboratory, Imperial College London
//
// Version :	0.1
// Date :		2016-07-06
//
// Description
// ===========
//
// Does the final processing of the data into spin averaged processed data, using the "normal"
//                igmvec output stage, and other DP pipeline stages, where possible.  The data
//                is inserted into the datastream, by converting to the correct form.  WARNING
//                *** This is highly implementation specific ***.
//                The Calibration data is also modified into something more useful, essentially
//                by ignoring the non-orthogonalities.  The spin axis offsets and gains are just
//                used.  The spin plane offsets are assumed to average out to zero, and the spin
//                plane gains are averaged out.
//                Ranges 6 and 7 are barely handled here, just being set to gains of one and offsets
//                of zero.  This should be modified to correctly handle the extended Calibration
//                files that contain Range 7 data.
// 
// Input Files:  /cluster/data/extended/yyyy/mm/C?_yymmdd_v.META
//               /cluster/data/extended/yyyy/mm/C?_yymmdd_v.En (n=0..) for each Extended Mode Block
// Output Files: /cluster/data/reference/yyyymm/C?_yymmdd_v.EXT.GSE analogous to the processed
//                 data from the more normal DP processing, to one minute and spin average data
//                 files, .1M.GSE and .P.GSE.  Currently all reference data is only created for the
//                 GSE reference frame.
//
// Version History
// ===============
//
//		0.1		2016-07-06		Initial Command Line version, derived from Web version
//
//
// Adapted for use with caa calibration 2016-08-16

#require_once( "meta_file_functions.php" );
require_once '/home/ahk114/Cluster/processing/meta_file_functions.php';

define('CAACAL','/cluster/caa/calibration/'); #caa calibration files directory
define('DAILYCAL','/cluster/operations/calibration/daily/');#dailycalfile dir
define( "RAW", "/cluster/data/raw/" );			#where raw data files reside
define( "EXTMODECOMMAND", "SFGMJ059 SFGMJ064 SFGMSEXT SFGMM002" );
define( "EXT", '/home/ahk114/data/extended/');	#where the output from stage1 and 2 are put
define ("PROC", '/home/ahk114/data/referencecaa/');#where the final output from this stage is put
define( "COORD", 1 );
define( "RESET_PERIOD", 5.152221 );
define( "SPIN_PERIOD", 4 );
define( "RESETPERIOD", 5.152 );
define( "PREREAD", 32768 );
define( "APPENDED",'/home/ahk114/logs/date_range_stage3/');	#log file that shows which files were appended to in this processing.
															#Those files may potentially contain duplicate entries!
$ext_appended = APPENDED.'ext_appended.log';
$ext_gse_appended = APPENDED.'ext_gse_appended.log';
$verbose = FALSE;
require_once 'getcalfile.php';	#needed to put this after constant definitions, otherwise the if loops in 
								#getfile.php complained about the constants being undefined!
// ========== FUNCTIONS ==========

// Take a floating point value, and return an array with four bytes (to be passed into the C
// functions which require data types such as fgmtvec.  See the "FGM Data Processing Handbook".

function float2hex( $float )
{
	if ( $float == 0 )
		return array ( 0, 0, 0, 0);
	$sign      = $float > 0 ? 0 : 1;
	$float     = abs( $float );
	$exp       = floor( log10( $float ) / log10( 2 ) );
	$remainder = 8388608 * ( ( $float / pow( 2, $exp ) ) - 1 );
	$upperexp  = (int) ( ( $exp + 127 ) / 2 );
	$lowerexp  = ( ( $exp + 127 ) & 1 );
	return array ( $remainder & 255, ( $remainder >> 8 ) & 255, ( $lowerexp * 128 ) + ( ( $remainder >> 16 ) & 127 ), ( $sign * 128 ) + $upperexp );
	
}

// Take an integer value, and return an array with four bytes (to be passed into the C functions
// which require data types such as fgmtvec.  See the "FGM Data Processing Handbook".

function integer2hex( $int )
{
	$int = (int) $int;
	//	return array($int>>24,($int>>16)&255,($int>>8)&255,$int&255);
	return array( $int & 255, ( $int >> 8 ) & 255, ( $int >> 16 ) & 255, $int >> 24 );
}

// Extract just the element of a floating point value that is to the right of the decimal point.

function floatbit( $real )
{
	$int = (int) $real;
	return $real - $int;
}

// Output a single byte (very inefficient)

function fputb( $handle, $value )
{
	fputs( $handle, chr( $value ), 1 );
}

// Retrieve a single byte, with some handling of constants that I don't think will work with the
// current installation of PHP, so may be utterly redundant!

function fgetb( $handle )
{
	global $BUFFER, $AVAILABLE, $HANDLE;
	
	if ( !isset( $HANDLE ) )
	{
		$HANDLE == $handle;
		$AVAILABLE == 0;
	}
	
	if ( $handle != $HANDLE )
	{
		return ord( fgetc( $handle ) );
	}
	else
	{
		if ( $AVAILABLE == 0 )
		{
			$BUFFER    = fread( $handle, PREREAD );
			$AVAILABLE = strlen( $BUFFER );
		}
		return ord( substr( $BUFFER, strlen( $BUFFER ) - ( $AVAILABLE-- ), 1 ) );
	}
} // fgetb

// Ignore a number of bytes (probably better done by simply inserting the fseek command directly
// into the code).

function ignore( $handle, $count )
{
	fseek( $handle, $count, SEEK_CUR );
}

function lastextendedmode( $year, $month, $day, $hour, $minute, $second, $sc, $version = "B" )
{
	$from    = mktime( $hour, $minute, 0, $month, $day, $year );
	$fromday = (int) ( $from / 86400 ) * 86400;
	$extmode = 0;
	
	for ( $n = $fromday; $n > ( $fromday - 10 * 86400 ); $n -= 86400 )
	{
		$filename = RAW . sprintf( "%04d", date( "Y", $n ) ) . "/" . sprintf( "%02d", date( "m", $n ) ) . "/C" . $sc . "_" . sprintf( "%6s", date( "ymd", $n ) ) . "_" . $version . ".SCCH";
		if ( file_exists( $filename ) )
		{
			$handle = fopen( $filename, "r" );
			if ( $handle )
			{
				while ( !feof( $handle ) )
				{
					ignore( $handle, 15 );
					$line[ ] = fgets( $handle, 256 );
				}
				fclose( $handle );
				rsort( $line );
				for ( $m = 0; $m < count( $line ); $m++ )
				{
					if ( strstr( EXTMODECOMMAND, substr( $line[ $m ], 61, 8 ) ) )
					{
						$event = mktime( substr( $line[ $m ], 11, 2 ), substr( $line[ $m ], 14, 2 ), substr( $line[ $m ], 17, 2 ), substr( $line[ $m ], 5, 2 ), substr( $line[ $m ], 8, 2 ), substr( $line[ $m ], 0, 4 ) );
						if ( $event < $from )
						{
							$extmode = $event;
							break 2;
						}
					}
				}
			}
		}
	}
	
	return $extmode;
} // lastextendedmode

function getcal($sc,$filepicked)
{
	global $gainx,$gainy,$gainz,$offsetx,$offsety,$offsetz,$verbose;

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
	
	# for non-default calibration files
	# Range 2, 3, 4, 5, 6
	# ----
	# ...
	# ----
	#!Range7
	# Offset X   Offset Y   Offset Z 
	#   M1          M2			M3
	#	M4			M5			M6
	#	M7			M8			M9
	
	#we care about the diagonal elements M1,M5,M9, since these are the gains, + some re-orthogonalisation which
	#is assumed to be negligible for ext mode data processing.
	#thus, effectively  M1 = Gain X
	#					M2 = Gain Y
	#					M3 = Gain Z
	
	/*
	$calfile = "/cluster/operations/calibration/default/C".$sc.".fgmcal";
	$cal=fopen($calfile,"rb"); #1 file like this is only for 1 spacecraft!!	
	*/
	$use_caa = FALSE;
	$use_daily = FALSE;
	$use_default = FALSE;
	/*
	Now hardwired to use caa calibration only!
	*/
	if ($calfile=getcalfile($sc,$filepicked,CAACAL))
	{
		#echo "Using CAA calibration!".PHP_EOL;
		echo "CAL File: ".$calfile.PHP_EOL;
		$use_caa = TRUE;
		$cal=fopen($calfile,"rb");	
	}
	elseif ($calfile=getcalfile($sc,$filepicked,DAILYCAL))
	{
		if (!$use_caa){exit("No caa cal found, exiting!".PHP_EOL);} #caa only
		echo "Using DAILY calibration!".PHP_EOL;
		$use_daily = TRUE;
		$cal=fopen($calfile,"rb");	
	}
	else
	{
		if (!$use_caa){exit("No caa cal found, exiting!".PHP_EOL);} #caa only
		$use_default = TRUE;
		echo "Using default calibration".PHP_EOL;
		$calfile = "/cluster/operations/calibration/default/C".$sc.".fgmcal";
		$cal=fopen($calfile,"rb");
	}
	if (!$use_caa){exit("No caa cal found, exiting!".PHP_EOL);}
	if ($cal)			#if cal file can be opened!
	{
		$dummy=fgets($cal,256); 												#skips first line, containing date/time info
		for($adc=1;$adc<3;$adc++)
		{
			for($sensor=0;$sensor<2;$sensor++)									#goes through 12 lines in total, which cover 1 configuration, eg. OB+ADC1, or IB+ADC2
			{
				fscanf($cal,"%f %f %f %f %f %s",&$offsetx[$adc][$sensor][2],	#only takes into account ranges 2,3,4,5,6 - 6 may be referred to as range 7 in the actual cal file
				                                &$offsetx[$adc][$sensor][3],
				                                &$offsetx[$adc][$sensor][4],
				                                &$offsetx[$adc][$sensor][5],
				                                &$offsetx[$adc][$sensor][6],
												&$dummy2);				#here, identifier string (dummy2) is skipped (eg. S2_32)

				fscanf($cal,"%f %f %f %f %f %s",&$offsety[$adc][$sensor][2],
				                                &$offsety[$adc][$sensor][3],
				                                &$offsety[$adc][$sensor][4],
				                                &$offsety[$adc][$sensor][5],
				                                &$offsety[$adc][$sensor][6],
												&$dummy2);

				fscanf($cal,"%f %f %f %f %f %s",&$offsetz[$adc][$sensor][2],
				                                &$offsetz[$adc][$sensor][3],
				                                &$offsetz[$adc][$sensor][4],
				                                &$offsetz[$adc][$sensor][5],
				                                &$offsetz[$adc][$sensor][6],
												&$dummy2);

				fscanf($cal,"%f %f %f %f %f %s",&$gainx[$adc][$sensor][2],
				                                &$gainx[$adc][$sensor][3],
				                                &$gainx[$adc][$sensor][4],
				                                &$gainx[$adc][$sensor][5],
				                                &$gainx[$adc][$sensor][6],
												&$dummy2);

				$dummy=fgets($cal,256); $dummy=fgets($cal,256); $dummy=fgets($cal,256);	#skips 3 lines

				fscanf($cal,"%f %f %f %f %f %s",&$gainy[$adc][$sensor][2],
				                                &$gainy[$adc][$sensor][3],
				                                &$gainy[$adc][$sensor][4],
				                                &$gainy[$adc][$sensor][5],
				                                &$gainy[$adc][$sensor][6],
												&$dummy2);

				$dummy=fgets($cal,256); $dummy=fgets($cal,256); $dummy=fgets($cal,256);	#skips 3 lines

				fscanf($cal,"%f %f %f %f %f %s",&$gainz[$adc][$sensor][2],
				                                &$gainz[$adc][$sensor][3],
				                                &$gainz[$adc][$sensor][4],
				                                &$gainz[$adc][$sensor][5],
				                                &$gainz[$adc][$sensor][6],
												&$dummy2);
			}
		}
		#fill in values for range7 now
		if ($verbose){echo "trying to extract range7 calibration from:".$calfile.PHP_EOL;}
		while(($line = fgets($cal)) !== false)
		{
			if (strpos(strtolower($line),"#!range7") !== false)
			{
				fscanf($cal,"%f %f %f",&$r7offsetx,&$r7offsety,&$r7offsetz);
				fscanf($cal,"%f %f %f",&$r7gainx,  &$dummy1,   &$dummy2);
				fscanf($cal,"%f %f %f",&$dummy1,   &$r7gainy,  &$dummy2);
				fscanf($cal,"%f %f %f",&$dummy1,   &$dummy2,   &$r7gainz);
				break;
			}
		}
		if ($use_daily)
		{
			$meta_file = substr($filepicked,0,strlen($filepicked)-2).'META';			
			echo "Meta File:".$meta_file.PHP_EOL;
			if (!(file_exists($meta_file))){echo "getcalfile, meta file not found!".PHP_EOL; return 0;}
			if (!(filesize($meta_file))){echo "getcafile, Meta file empty!".PHP_EOL; return 0;}			
			if ($verbose && $extmodeentry_unix)
			{
				echo "Extended mode entry:".$extmodeentry_unix.PHP_EOL;
			}
			if (!($extmodeentry_unix))
			{
				echo "No extended mode data in this dump!".PHP_EOL;
				return 0;
			}
			$daily_range7_dir = '/cluster/operations/calibration/daily/range7/'.date("Y",$extmodeentry_unix).'/'.date("m",$extmodeentry_unix).'/';
			$daily_range7_file = $daily_range7_dir.'C'.$sc.'_range7.fgmcal';
			$cal7 = fopen($daily_range7_file, "rb");
			if ($cal7)
			{
				fscanf($cal7,"%f",&$r7offsetx);
				fscanf($cal7,"%f",&$r7offsety);
				fscanf($cal7,"%f",&$r7offsetz);
				fscanf($cal7,"%f",&$r7gainx);
				$dummy=fgets($cal7,256); $dummy=fgets($cal7,256); $dummy=fgets($cal7,256);	#skips 3 lines
				fscanf($cal7,"%f",&$r7gainy);
				$dummy=fgets($cal7,256); $dummy=fgets($cal7,256); $dummy=fgets($cal7,256);	#skips 3 lines
				fscanf($cal7,"%f",&$r7gainz);
			}
			
		}
		if ((!(isset($r7offsetx))) 
			||	(!(isset($r7offsety))) 
			|| (!(isset($r7offsetz))) 
			|| (!(isset($r7gainx)))
			|| (!(isset($r7gainy)))
			|| (!(isset($r7gainz))))
		{	#if these are not set, then assume that no range7 info was there, and fill it in with unit values
		
			$r7offsetx = 0;
			$r7offsety = 0;
			$r7offsetz = 0;
			$r7gainx = 1;
			$r7gainy = 1;
			$r7gainz = 1;
		}
		for($adc=1;$adc<3;$adc++)			#is it valid to fill this info in for all adcs/sensors?
		{
			for($sensor=0;$sensor<2;$sensor++)
			{
				$offsetx[$adc][$sensor][7]=$r7offsetx;
				$offsety[$adc][$sensor][7]=$r7offsety;
				$offsetz[$adc][$sensor][7]=$r7offsetz;
				$gainx[$adc][$sensor][7]=$r7gainx;
				$gainy[$adc][$sensor][7]=$r7gainy;
				$gainz[$adc][$sensor][7]=$r7gainz;
			}
		}
		
	}
	else
	{
		exit("CAA calibration file not found or can't be opened".PHP_EOL);
		/* #caa only
		for($adc=1;$adc<3;$adc++)
			for($sensor=0;$sensor<2;$sensor++)
				for($range=2;$range<8;$range++)
				{
					$offsetx[$adc][$sensor][$range]=0;
					$offsety[$adc][$sensor][$range]=0;
					$offsetz[$adc][$sensor][$range]=0;
					$gainx[$adc][$sensor][$range]=1;
					$gainy[$adc][$sensor][$range]=1;
					$gainz[$adc][$sensor][$range]=1;
				}
		*/
	}
}

function modifycal( $sc )
{
	global $gainx, $gainy, $gainz, $offsetx, $offsety, $offsetz;
	
	for ( $adc = 1; $adc < 3; $adc++ )
		for ( $sensor = 0; $sensor < 2; $sensor++ )
			for ( $range = 2; $range < 8; $range++ )
			{
				$offsety[ $adc ][ $sensor ][ $range ] = 0;
				$offsetz[ $adc ][ $sensor ][ $range ] = 0;
				
				$n = $gainy[ $adc ][ $sensor ][ $range ];
				$m = $gainz[ $adc ][ $sensor ][ $range ];
				
				$gainy[ $adc ][ $sensor ][ $range ] = ( $n + $m ) / 2;
				$gainz[ $adc ][ $sensor ][ $range ] = ( $n + $m ) / 2;
			}
} // modifycal

function displaycal( $sc )
{
	global $gainx, $gainy, $gainz, $offsetx, $offsety, $offsetz;
	for ( $adc = 1; $adc < 3; $adc++ )
	{
		echo "adc:".$adc.PHP_EOL;
		for ( $sensor = 0; $sensor < 2; $sensor++ )
		{
			echo "sensor:".$sensor.PHP_EOL;
			echo "Range   Gain x  Gain y  Gain z   Offset x   Offset y   Offset z".PHP_EOL;
			for ( $range = 2; $range < 8; $range++ )
			{
				echo $range.'       '
					.sprintf('%05.3f',$gainx[ $adc ][ $sensor ][ $range ]).'   '
					.sprintf('%05.3f',$gainy[ $adc ][ $sensor ][ $range ]).'   '
					.sprintf('%05.3f',$gainz[ $adc ][ $sensor ][ $range ]).'    '
					.sprintf('%08.3f',$offsetx[ $adc ][ $sensor ][ $range ]).'   '
					.sprintf('%08.3f',$offsety[ $adc ][ $sensor ][ $range ]).'   '
					.sprintf('%08.3f',$offsetz[ $adc ][ $sensor ][ $range ])
					.PHP_EOL;
			}
		}
	}
} // displaycal

function spinrate( $year, $month, $day, $sc, $version )
{
	if ( $year >= 2000 )
		$year -= 2000;
	$satt_name = RAW . sprintf( "20%02d/%02d/C%1s_%02d%02d%02d", $year, $month, $sc, $year, $month, $day ) . "_" . $version . '.SATT';
	
	if ( file_exists( $satt_name ) && ( $satt_h = fopen( $satt_name, "rb" ) ) )
	{
		fseek( $satt_h, 15, SEEK_SET );
		$satt_line = fgets( $satt_h, 100 );
		fclose( $satt_h );
		$deltatime = 60 / substr( $satt_line, 61, 9 );
	}
	else
	{
		$deltatime = SPIN_PERIOD;
	}
	
	return $deltatime;
} // spinrate

// ========== END OF FUNCTIONS ==========


// Code to minimally deal with parameter passing

if ( PHP_SAPI != "cli" )
	exit( "THIS SHOULD ONLY BE RUN USING THE PHP CLI\r\n" );

if ( $argc != 6 )
	exit( "NEEDS 5 parameters : stage3_cli.php <sc> <year> <month> <day> <vers>\r\n" );

$year = $argv[ 2 ];
if ( $year < 2000 )
	$year += 2000;
$shortyear = sprintf( "%02d", $year - 2000 );
$month     = $argv[ 3 ];
$day       = $argv[ 4 ];
$sc        = $argv[ 1 ];
$version   = $argv[ 5 ];

if ( ( $year < 2000 or $year > date( "Y" ) ) or ( $year != (int) $year ) )
	exit( "The year (parameter 2) must be an integer between 2000 and " . date( "Y" ) . "\r\n" );
if ( ( $month < 1 or $month > 12 ) or ( $month != (int) $month ) )
	exit( "The month (parameter 3) must be an integer between 1 and 12\r\n" );
if ( ( $day < 1 or $day > 31 ) or ( $day != (int) $day ) )
	exit( "The day (parameter 4) must be an integer between 1 and 31\r\n" );
if ( $sc < 1 or $sc > 4 or $sc != (int) $sc )
	exit( "The spacecraft (parameter 1) must be an integer betwen 1 and 4\r\n" );
if ( $version < 'A' or $version > 'Z' or strlen( $version ) != 1 )
	exit( "The version (parameter 5) must be a single character between A and Z\r\n" );

// Loop around all the Extended Mode blocks in the Meta data file for this date (only loop around
// ten times, which is far more than are likely to occur.  Generally it's unlikely that there will
// be more than two lots of Extended Mode in one day, and each dump may have two sets of date, the
// "good" set, and the partial repetition. ie Four Extended Mode blocks.

for ( $ext = 0; $ext < 10; $ext++ )
{
	// This is probably looking at the version field, so passing this in as well, is probably a
	// mistake.  It will generally work, since Version B files will normally be correct for both
	// both cases.  This needs to be sorted out.
	
	for ( $age = 12; $age >= 0; $age-- )
	{
		$filename = EXT . sprintf( "%04d", $year ) . "/" . sprintf( "%02d", $month ) . "/C" . $sc . "_" . sprintf( "%02d%02d%02d", $year - 2000, $month, $day ) . "_" . chr( ord( "A" ) + $age );

		if ( ( file_exists( $filename . ".E" . $ext ) ) && ( filesize( $filename . ".E" . $ext ) != 0 ) )
		{
			$this_event_date  = read_meta( $filename . ".META", "ExtendedModeEntry_ISO", $ext );
			$this_event_block = $ext;
			$this_source      = mktime( 0, 0, 0, $month, $day, $year );
			
			$entry = 0 + read_meta( $filename . ".META", "ExtendedModeEntry_Unix", $ext );
			
			// If $entry is zero, this probably means that the Entry point could not be found, so don't generate any of the Meta Data,
			// because it will probably just point to Unix date zero, ie 1970 something, which isn't useful.
			
			if ( $entry != 0 )
			{
				$extmodeentrymetafile = EXT . date( "Y", $entry ) . "/" . date( "m", $entry ) . "/C" . $sc . "_" . date( "ymd", $entry ) . "_" . chr( ord( "A" ) + $age ) . ".META";
				$index                = 0;
				do
				{
					$use = read_meta( $extmodeentrymetafile, "Use", chr( ord( "A" ) + $index ) );
					if ( !$use )
						$index++;
				} while ( !$use and $index < 100 );
				
				if ( ( read_meta( $extmodeentrymetafile, "EventTime_ISO", chr( ord( "A" ) + $index ) ) == $this_event_date ) and ( read_meta( $extmodeentrymetafile, "Block", chr( ord( "A" ) + $index ) ) == $this_event_block ) and ( read_meta( $extmodeentrymetafile, "Source_Unix", chr( ord( "A" ) + $index ) ) == $this_source ) )
				{
					$filepicked = $filename . ".E" . $ext;
					
					$extsensor = 0;
					$extadc    = 1;
					
					$year    = substr( basename( $filepicked ), 3, 2 );
					$month   = substr( basename( $filepicked ), 5, 2 );
					$day     = substr( basename( $filepicked ), 7, 2 );
					$sc      = substr( basename( $filepicked ), 1, 1 );
					$version = substr( basename( $filepicked ), 10, 1 );
					
					getcal( $sc ,$filepicked);
					echo "Raw Calibration, before adjustment (just as read from file)".PHP_EOL;
					displaycal( $sc ); #displaying calibration used
					modifycal( $sc );
					echo "Displaying calibration that is actually used! (after modification)".PHP_EOL;
					displaycal( $sc );
					$satt_name = RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_' . $version . '.SATT';
					
					if ( file_exists( $satt_name ) && ( $satt_h = fopen( $satt_name, "rb" ) ) )
					{
						ignore( $satt_h, 15 );
						$satt_line = fgets( $satt_h, 100 );
						fclose( $satt_h );
						$deltatime = 60 / substr( $satt_line, 61, 9 );
					}
					else
					{
						$deltatime = 4;
					}
					
					$section = substr( $filepicked, -1, 1 );
					
					$start = read_meta( EXT . '20' . $year . '/' . $month . '/' . substr( basename( $filepicked ), 0, -3 ) . ".META", "ExtendedModeEntry_Unix", $section );
					
					$current = $start;
					
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
					echo "Reading raw data from:".PHP_EOL.$filepicked.PHP_EOL;			
					$extfile = file( $filepicked );
					
					if ( !is_dir( EXT . date( 'Y', $start ) ) )
						mkdir( EXT . date( 'Y', $start ), 0750 );
					
					if ( !is_dir( EXT . date( 'Y/m', $start ) ) )
						mkdir( EXT . date( 'Y/m', $start ), 0750 );
					
					if (!is_dir(EXT.date('Y/m/',$start)))
					{
						echo "Creating EXT directory".PHP_EOL;
						mkdir(EXT.date('Y/m/',$start),0750,true);
					}
					$dir_path = PROC.date( 'Y/m/', $start );
					if (!is_dir($dir_path))
					{
						mkdir($dir_path,0750,true);
					}
					$outfile = EXT . date( 'Y/m/', $start ) . 'C' . $sc . '_' . date( 'ymd', $start ) . '_' . $version . '.EXT';
					
					if (file_exists($outfile))
					{
						$appended_handle = fopen($ext_appended,'ab');
						if (!$appended_handle)
						{
							exit('Unable to open ext appended log file!'.PHP_EOL);
						}
						fwrite($appended_handle,date("Y-m-d H:i:s").' '.$outfile.PHP_EOL);
						fclose($appended_handle);
					}	
					
					$outhandle = fopen( $outfile , 'ab' );
					if ( !$outhandle )
					{
						exit( "Bugger!" );
					}
					
					$tmp        = tempnam( '/var/tmp', 'ExtProcRaw_' );
					$testhandle = fopen( $tmp, 'wb' ); // NB wb not ab
					if ( !$testhandle )
					{
						exit( "other Bugger!" );
					}

					
					$sattfile = RAW . date( 'Y/m/', $start ) . 'C' . $sc . '_' . date( 'ymd', $start ) . '_' . $version . '.SATT';
					$stoffile = RAW . date( 'Y/m/', $start ) . 'C' . $sc . '_' . date( 'ymd', $start ) . '_' . $version . '.STOF';
					$procfile = PROC . date( 'Y/m/', $start ) . 'C' . $sc . '_' . date( 'ymd', $start ) . '_' . $version . '.EXT.GSE';
					
					$k    = pi() * pi() / 16;
					$k2   = pi() / 4;
					$time = $start;
					
					$lastreset = 999999;
					$loopsize   = count( $extfile );
					$onepercent = (int) ( $loopsize / 100 );
					
					for ( $n = 0; $n < $loopsize; $n++ )
					{
						sscanf( $extfile[ $n ], "%d %d %d %d %d %s", &$instrx, &$instry, &$instrz, &$range, &$reset, &$comment );
						
						if ( !( ( $instrx == 0 && $instry == 0 && $instrz == 0 && $range == 0 ) || $range < 2 || $range > 7 ) )
						{
							$deltareset = ( $reset - $lastreset + 4096 ) % 4096; // allow for -ve values (wraparound)
							
							if ( ( $deltareset ) > 1 and ( $lastreset != 999999 ) )
							{
								// OK, if reset goes up by more than one, then are missing resets for some reason
								
								// Since Reset count only incs every 16 resets (so every 5.152*16), take this and divide by
								// spin to get rough time/reset increment.
								
								$time += $deltatime * ( $deltareset - 1 ) * 16 * RESETPERIOD / $deltatime; // remove 1, since already added deltatime on previous iteration
							}
							
							$lastreset = $reset; // Set lastreset to reset
							
							// The old version worked with ranges 2 to 5 (and 6, by luck), but not with range 7.
							// Using the pow() function generates a floating point result of 0.25 for range 7.
							
							// $scale=(512>>(($range-2)*2))/2;
							$scale = pow( 2, 12 - $range * 2 );
							
							if ( $instrx > 32767 )
								$bx = ( $instrx - 65536 ) / $scale;
							else
								$bx = $instrx / $scale;
							
							if ( $instry > 32767 )
								$by = ( $instry - 65536 ) / $scale;
							else
								$by = $instry / $scale;
							
							if ( $instrz > 32767 )
								$bz = ( $instrz - 65536 ) / $scale;
							else
								$bz = $instrz / $scale;
							
							if ( $range < 2 or $range > 7 )
								exit( "WTf? Range is off the scale?!" );

							$bx = $bx * $gainx[ $extadc ][ $extsensor ][ $range ] - $offsetx[ $extadc ][ $extsensor ][ $range ];
							$by = $by * $k2 * $gainy[ $extadc ][ $extsensor ][ $range ] - $offsety[ $extadc ][ $extsensor ][ $range ];
							$bz = $bz * $k2 * $gainz[ $extadc ][ $extsensor ][ $range ] - $offsetz[ $extadc ][ $extsensor ][ $range ];
							
							$stuff = date( "Y-m-d\TH:i:s", $time ) . '.' . sprintf( "%03d", ( (int) ( 1000 * ( $time - (int) $time ) ) ) ) . 'Z ' . sprintf( "%4.3f %4.3f %4.3f\n", $bx, $by, $bz );
							
							// Hereabouts need to do Reference Frame conversion
							
							$hexbx = float2hex( $bx );
							$hexby = float2hex( $by );
							$hexbz = float2hex( $bz );
							$time1 = integer2hex( $time );
							$time2 = integer2hex( floatbit( $time ) * 1e9 );
							
							
							$teststuff = array(
								( $range << 4 ) + 14,	16,						128 + ( COORD & 7 ),	( ( $sc - 1 ) << 6 ) + 1,
								$time1[ 0 ],			$time1[ 1 ],			$time1[ 2 ],			$time1[ 3 ],
								$time2[ 0 ],			$time2[ 1 ],			$time2[ 2 ],			$time2[ 3 ],
								$hexbx[ 0 ],			$hexbx[ 1 ],			$hexbx[ 2 ],			$hexbx[ 3 ],
								$hexby[ 0 ],			$hexby[ 1 ],			$hexby[ 2 ],			$hexby[ 3 ],
								$hexbz[ 0 ],			$hexbz[ 1 ],			$hexbz[ 2 ],			$hexbz[ 3 ],
								0,						0,						0,						0,
								0,						0,						0,						0 
							);
						}
						else
						{
							$stuff     = date( "Y-m-d\TH:i:s", $time ) . '.' . sprintf( "%03d", ( (int) ( 1000 * ( $time - (int) $time ) ) ) ) . 'Z ' . sprintf( "%4.3f %4.3f %4.3f\n", 0, 0, 0 );
							$teststuff = array(
								14,						128,					128 + 3,				( $sc - 1 ) << 6 + 1,
								integer2hex( $time ),	integer2hex( floatbit( $time ) / 1e9 ),			0,						0,
								0,						0,						0,						0,
								0,						0,						0,						0,
								0,						0,						0,						0,
								0,						0,						0,						0,
								0,						0,						0,						0,
								0,						0,						0,						0
							);
							
						}
						
						fputs( $outhandle, $stuff );
						for ( $i = 0; $i < 32; $i++ )
							fputb( $testhandle, $teststuff[ $i ] );
						
						$time += $deltatime;
						if ( date( "d", $current ) != date( "d", $time ) )
						{
							$current = $time;
							fclose( $outhandle );
							fclose( $testhandle );
							// process file before we generate new one
							$tmp2 = tempnam( '/var/tmp', 'ExtProcDecoded_' );
							
							if (file_exists($procfile))
							{
								$appended_handle = fopen($ext_gse_appended,'ab');
								if (!$appended_handle)
								{
									exit('Unable to open ext.gse appended log file!'.PHP_EOL);
								}
								fwrite($appended_handle,date("Y-m-d H:i:s").' '.$procfile.PHP_EOL);
								fclose($appended_handle);
							}								
							
							exec( "FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat " . $tmp . " | /cluster/operations/software/dp/bin/fgmhrt -s gse -a " . $sattfile . " | /cluster/operations/software/dp/bin/fgmpos -p " . $stoffile . " | /cluster/operations/software/dp/bin/igmvec -o " . $tmp2 . " 2>/dev/null ; cat " . $tmp2 . " >> " . $procfile );
							echo "Output file (appended):".$procfile.PHP_EOL;
							if ( !is_dir( EXT . date( 'Y', $time ) ) )
								mkdir( EXT . date( 'Y', $time ), 0750 );
							
							if ( !is_dir( EXT . date( 'Y/m', $time ) ) )
								mkdir( EXT . date( 'Y/m', $time ), 0750 );
							
							if (!is_dir(EXT.date('Y/m/',$time)))
							{
								echo "Creating EXT directory".PHP_EOL;
								mkdir(EXT.date('Y/m/',$time),0750,true);
							}
							$dir_path = PROC.date( 'Y/m/', $time );
							if (!is_dir($dir_path))
							{
								mkdir($dir_path,0750,true);
							}
							
							$outfile = EXT . date( 'Y/m/', $time ) . 'C' . $sc . '_' . date( 'ymd', $time ) . '_' . $version . '.EXT';

							if (file_exists($outfile))
							{
								$appended_handle = fopen($ext_appended,'ab');
								if (!$appended_handle)
								{
									exit('Unable to open ext appended log file!'.PHP_EOL);
								}
								fwrite($appended_handle,date("Y-m-d H:i:s").' '.$outfile.PHP_EOL);
								fclose($appended_handle);
							}	
							
							$outhandle = fopen( $outfile , 'ab' );							
							if ( !$outhandle )
							{
								exit( "yes another Bugger" );
							}
							
							$tmp        = tempnam( '/var/tmp', 'ExtProcRaw_' );
							$testhandle = fopen( $tmp, 'wb' ); // NB wb not ab
							$sattfile   = RAW . date( 'Y/m/', $time ) . 'C' . $sc . '_' . date( 'ymd', $time ) . '_' . $version . '.SATT';
							$stoffile   = RAW . date( 'Y/m/', $time ) . 'C' . $sc . '_' . date( 'ymd', $time ) . '_' . $version . '.STOF';
							#$outhandle  = fopen( EXT . date( 'Y/m/', $start ) . 'C' . $sc . '_' . date( 'ymd', $start ) . '_' . $version . '.EXT', 'ab' );
							$procfile   = PROC . date( 'Y/m/', $time ) . 'C' . $sc . '_' . date( 'ymd', $time ) . '_' . $version . '.EXT.GSE';
						}
					}
					fclose( $outhandle );
					fclose( $testhandle );
					
					$tmp2 = tempnam( '/var/tmp', 'ExtProcDecoded_' );
					exec( "FGMPATH=/cluster/operations/calibration/default ; export FGMPATH ; cat " . $tmp . " | /cluster/operations/software/dp/bin/fgmhrt -s gse -a " . $sattfile . " | /cluster/operations/software/dp/bin/fgmpos -p " . $stoffile . " | /cluster/operations/software/dp/bin/igmvec -o " . $tmp2 . " 2>/dev/null ; cp " . $tmp2 . " " . $procfile );
					#cp not >> since this is the first time that data *should* be written to this .EXT.GSE file if data is processed chronologically
					#above, content is appended with cat and then >> , since in theory, that *should* be the second time that file is written to
					#it would be problematic, if there were 2 extended modes in one day, then using cp would simply overwrite previously processed data!
					#However, the testhandle (tmp file) is openend in 'wb' mode, overwriting previous changes. 
					#On the current date, the output from the dp software is appended to an output file if already present
					#On the next day, a new file is created and previous output files overwritten!
					
					#When running the same dates through the processing software, some .EXT.GSE files will grow in magnitude, as will all of the 
					#.EXT files, since these files are appended to, rather than overwritten!
					#Log files for appended .EXT and .EXT.GSE files are now being created!
					echo "Output file (copy (overwrite)):".$procfile.PHP_EOL;
				}
			}
		}
	}
}
exit(1);
?>