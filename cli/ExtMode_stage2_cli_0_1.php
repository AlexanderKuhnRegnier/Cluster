<?php

// Name :		ExtMode_stage2_cli_0_1.php
// Author :		Tim Oddy
//				(C) Space Magnetometer Laboratory, Imperial College London
//
// Version :	0.2
// Date :		2016-07-06
//
// Description
// ===========
// Mostly this code just determines when the instrument switched into Extended Mode, for a set of
// data on a given day, which is just the day when the data was dowbloaded from the instrument,
// and which is typically a day or maybe two, before that.
// Here it's done *very* simply using the SCCH (Spacecraft Command History) file, but would be
// better done using the Reset and Sunpulse information in both the Extended Mode data and the
// Science and Housekeeping telemetry adjacent to it.
// Similarly the spin period would be better chosen using the same technique, rather than simply
// extracting it from the SATT file.
//
// Version History
// ===============
//
//		0.1		2016-07-06		Initial Command Line version, derived from Web version

require_once( "iso.php" );
require_once( "meta_file_functions.php" );

define( "EXTMODECOMMAND_INITIATE", "SFGMJ059 SFGMJ064 SFGMSEXT" );
define( "EXTMODECOMMAND_TERMINATE", "SFGMJ065 SFGMJ050" );
define( "INITIATE", 1 );
define( "TERMINATE", 2 );
define( "RAW", "/cluster/data/raw/" );
define( "EXT", '/home/ahk114/data/extended/' );

// ========== FUNCTIONS ==========

function fgetb( $handle )

{
	return ord( fgetc( $handle ) );
}

function ignore( $handle, $count )
{
	for ( $n = 0; $n < $count; $n++ )
		fgetc( $handle );
}

// Input time of Extended Mode Block *Dump* (as unix time in seconds)
// Output time of Extended Mode Entry (as Unix time in seconds)

function lastextendedmode( $unixtime, $sc, $type )
{
	if ( $type == INITIATE )
		$searchstring = EXTMODECOMMAND_INITIATE;
	elseif ( $type == TERMINATE )
		$searchstring = EXTMODECOMMAND_TERMINATE;
	else
		$searchstring = "";
	
	$fromday = (int) ( $unixtime / 86400 ) * 86400;
	$extmode = 0;
	
	$commanding_found = FALSE;
	
	for ( $n = $fromday; $n > ( $fromday - 10 * 86400 ); $n -= 86400 )
	{
		$scch_filename = RAW . sprintf( "%04d", date( "Y", $n ) ) . "/" . sprintf( "%02d", date( "m", $n ) ) . "/C" . $sc . "_" . sprintf( "%6s", date( "ymd", $n ) ) . "_B.SCCH";
		
		if ( file_exists( $scch_filename ) )
		{
			$handle = fopen( $scch_filename, "r" );
			if ( $handle )
			{
				while ( !feof( $handle ) )
				{
					for ( $dummy = 0; $dummy < 15; $dummy++ )
						fgetc( $handle );
					$line[ ] = fgets( $handle, 256 );
				}
				fclose( $handle );
				rsort( $line );
				for ( $m = 0; $m < count( $line ); $m++ )
				{
					if ( strstr( $searchstring, substr( $line[ $m ], 61, 8 ) ) )
					{
						$evnt = mktime( substr( $line[ $m ], 11, 2 ), substr( $line[ $m ], 14, 2 ), substr( $line[ $m ], 17, 2 ), substr( $line[ $m ], 5, 2 ), substr( $line[ $m ], 8, 2 ), substr( $line[ $m ], 0, 4 ) );
						if ( $evnt < $unixtime )
						{
							$extmode = $evnt;
							break 2;
						}
					}
				}
			}
		}
	}
	
	return $extmode;
} // lastextendedmode

function spin( $unixtime, $sc )
{
	$year  = date( "y", $unixtime );
	$month = date( "m", $unixtime );
	$day   = date( "d", $unixtime );
	if ( file_exists( RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_K.SATT' ) )
		$satt_name = RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_K.SATT';
	elseif ( file_exists( RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_B.SATT' ) )
		$satt_name = RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_B.SATT';
	elseif ( file_exists( RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_A.SATT' ) )
		$satt_name = RAW . '20' . $year . '/' . $month . '/C' . $sc . '_' . $year . $month . $day . '_A.SATT';
	else
		return 4;
	
	if ( $satt_h = fopen( $satt_name, "rb" ) )
	{
		ignore( $satt_h, 15 );
		$satt_line = fgets( $satt_h, 100 );
		fclose( $satt_h );
		return 60 / substr( $satt_line, 61, 9 );
	}
	else
		return 4;
} // spin

function spaceship( $a, $b )
{
	if ( $a == $b )
		return 0;
	else if ( $a < $b )
		return -1;
	else
		return 1;
}

function sorter( $a, $b )
{
	$first = spaceship( $a[ 'source_unix' ], $b[ 'source_unix' ] );
	if ( $first != 0 )
	{
		return $first;
	}
	else
	{
		$second = spaceship( $a[ 'block' ], $b[ 'block' ] );
		if ( $second != 0 )
		{
			return $second;
		}
		else
		{
			return spaceship( $a[ 'unix' ], $b[ 'unix' ] );
		}
	}
} // sorter

function debug( $message )
{
	//	print $message."\r\n";
}

// ========== END OF FUNCTIONS ==========


if ( PHP_SAPI != "cli" )
	exit( "THIS SHOULD ONLY BE RUN USING THE PHP CLI\r\n" );

if ( $argc != 6 )
	exit( "NEEDS 5 parameters : stage2_cli.php <sc> <year> <month> <day> <vers>\r\n" );

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

debug( "Year " . $year . " Month " . $month . " Day " . $day . " SC " . $sc . " Version " . $version );

$filename = EXT . sprintf( "%4d/%02d/C%d_%02d%02d%02d_%s", $year, $month, $sc, $year - 2000, $month, $day, $version );

debug( $filename );

if ( !file_exists( $filename . ".META" ) )
	exit(-1);
echo "Reading from (and writing to) META file:".$filename.PHP_EOL;
$numberofblocks = 0 + read_meta( $filename . ".META", "NumberOfBlocks" );

debug( "Number of blocks : " . $numberofblocks );

$bits = explode( "/", $filename );

// 01234567890
// C1_020304_B

//$sc       = substr( $bits[count( $bits )-1], 1, 1 );
//$vers     = substr( $bits[count( $bits )-1], -1, 1 );
//$src_date = mktime( 0, 0, 0, substr( $bits[count( $bits )-1], 5, 2 ), substr( $bits[count( $bits )-1], 7, 2 ), substr( $bits[count( $bits )-1], 3, 2 ) );

$src_date = mktime( 0, 0, 0, $month, $day, $year );

for ( $n = 0; $n < $numberofblocks; $n++ )
{
	
	debug( "n " . $n );
	
	// The $filename.".META" metafile is at the location of the source data file, and contains the date of where the
	// Extended Mode starts in the $start variable.
	
	// The $where_filename metafile is at the location where Extended Mode starts from the $start variable and contains
	// the location of the source data file and block.
	
	$start = lastextendedmode( read_meta( $filename . ".META", "DumpStartTime_Unix", $n ), $sc, INITIATE );
	$end   = lastextendedmode( read_meta( $filename . ".META", "DumpStartTime_Unix", $n ), $sc, TERMINATE );
	
	// Only process this data, if $start has been set to something useful.  If it's zero, that probably
	// means that there's no useful data, so further processing would probably jusr produce rubbish.
	
	if ( $start != 0 )
	{
		$part = read_meta( $filename . ".META", "PartialStart", $n );
		
		debug( "Start " . $start . " End " . $end . " Part " . $part );
		
		$where_filename = EXT . date( "Y/m/", $start ) . "C" . $sc . "_" . date( "ymd", $start ) . "_" . $version . ".META";
		
		debug( "Where Filename " . $where_filename );
		
		$event        = array( );
		$unused_event = array( );
		
		if ( !file_exists( $where_filename ) )
		{
			if ( !file_exists( EXT . date( "Y", $start ) ) )
				mkdir( EXT . date( "Y", $start ) );
			if ( !file_exists( EXT . date( "Y/m", $start ) ) )
				mkdir( EXT . date( "Y/m", $start ) );
			touch( $where_filename );
			
			$where_count                 = 1;
			$event[ 0 ][ 'filename' ]    = read_meta( $filename . ".META", "SourceFile" );
			$event[ 0 ][ 'unix' ]        = $start;
			$event[ 0 ][ 'block' ]       = 0;
			$event[ 0 ][ 'use' ]         = 1;
			$event[ 0 ][ 'source_unix' ] = $src_date;
		}
		else
		{
			$where_count = 0 + read_meta( $where_filename, "NumberOfExtendedEvents" );
			
			debug( "Where Count : " . $where_count );
			
			for ( $i = 0; $i < $where_count; $i++ )
			{
				
				$use_it = 0 + read_meta( $where_filename, "Use", chr( ord( "A" ) + $i ) );
				if ( $use_it )
				{
					$event[ $i ][ 'filename' ]    = read_meta( $where_filename, "FileName", chr( ord( "A" ) + $i ) );
					$event[ $i ][ 'unix' ]        = 0 + read_meta( $where_filename, "EventTime_Unix", chr( ord( "A" ) + $i ) );
					$event[ $i ][ 'block' ]       = 0 + read_meta( $where_filename, "Block", chr( ord( "A" ) + $i ) );
					$event[ $i ][ 'use' ]         = $use_it;
					$event[ $i ][ 'source_unix' ] = 0 + read_meta( $where_filename, "Source_Unix", chr( ord( "A" ) + $i ) );
				}
				else
				{
					$unused_event[ $i ][ 'filename' ]    = read_meta( $where_filename, "FileName", chr( ord( "A" ) + $i ) );
					$unused_event[ $i ][ 'unix' ]        = 0 + read_meta( $where_filename, "EventTime_Unix", chr( ord( "A" ) + $i ) );
					$unused_event[ $i ][ 'block' ]       = 0 + read_meta( $where_filename, "Block", chr( ord( "A" ) + $i ) );
					$unused_event[ $i ][ 'use' ]         = $use_it;
					$unused_event[ $i ][ 'source_unix' ] = read_meta( $where_filename, "Source_Unix", chr( ord( "A" ) + $i ) );
				}
			}
		}
		
		if ( !file_exists( EXT . date( "Y", $start ) ) )
			mkdir( EXT . date( "Y", $start ) );
		if ( !file_exists( EXT . date( "Y/m", $start ) ) )
			mkdir( EXT . date( "Y/m", $start ) );
		if ( !file_exists( $where_filename ) )
			touch( $where_filename );
		
		if ( isset( $event[ 0 ][ 'unix' ] ) )
			$found_date = $event[ 0 ][ 'unix' ];
		else
			$found_date = mktime( 0, 0, 0, 1, 1, 2999 );
		
		if ( isset( $event[ 0 ][ 'block' ] ) )
			$found_block = $event[ 0 ][ 'block' ];
		else
			$found_block = 9999;
		
		$event[ $where_count ][ 'filename' ]    = read_meta( $filename . ".META", "SourceFile" );
		$event[ $where_count ][ 'unix' ]        = $start;
		$event[ $where_count ][ 'block' ]       = $n;
		$event[ $where_count ][ 'use' ]         = 1;
		$event[ $where_count ][ 'source_unix' ] = $src_date;
		
		if ( $found_date != "" )
		{
			if ( $src_date < $found_date )
			{
				$good_to_do_stage3 = TRUE;
			}
			elseif ( $src_date == $found_date )
			{
				if ( $n < $found_block )
				{
					// This block is Better
					$good_to_do_stage3 = TRUE;
				}
				elseif ( $n == $found_block )
				{
					// This is the Existing (Date same then block same)
					$good_to_do_stage3 = TRUE;
				}
				else
				{
					// Existing is better (Date same then block greater)
					$good_to_do_stage3 = FALSE;
				}
			}
			else
			{
				// Existing is better (Date newer)
				$good_to_do_stage3 = FALSE;
			}
		}
		else
		{
			// This is New
			$good_to_do_stage3 = TRUE;
			write_meta( $where_filename, "FoundDate_Unix", $src_date );
			write_meta( $where_filename, "FoundDate_ISO", unix2iso( $src_date ) );
			write_meta( $where_filename, "FoundBlock", $n );
			write_meta( $where_filename, "Source_Unix", $src_date );
			write_meta( $where_filename, "FileName", $filename );
		}
		if ( $good_to_do_stage3 )
		{
			// This Block should be processed further
		}
		
		if ( $part == "TRUE" )
		{
			// Probable repeat copy
		}
		$spin        = spin( $start, $sc );
		$calcvec     = (int) ( ( $end - $start ) / $spin );
		$actualvec   = 0 + read_meta( $filename . ".META", "NumberOfVectors", $n );
		// Derived Number of vectors  $calcvec
		// Number of vectors in block $actualvec
		$miss        = read_meta( $filename . ".META", "MissingPacket", $n );
		$reset_start = read_meta( $filename . ".META", "ResetCountStart", $n );
		$reset_stop  = read_meta( $filename . ".META", "ResetCountEnd", $n );
		write_meta( $filename . ".META", "ExtendedModeEntry_ISO", date( "Y-m-d\TH:i:s\Z", $start ), $n );
		write_meta( $filename . ".META", "ExtendedModeEntry_Unix", $start, $n );
		write_meta( $filename . ".META", "ExtendedModeExit_ISO", date( "Y-m-d\TH:i:s\Z", $end ), $n );
		write_meta( $filename . ".META", "ExtendedModeExit_Unix", $end, $n );
		write_meta( $filename . ".META", "SpinPeriod", round( $spin, 6 ) );
		
		$event = array_unique( $event, SORT_REGULAR ); // Remove any identical cases (need SORT_REGULAR so it doesn't do a string comparison)
		$event = array_merge( $event, $unused_event ); // Now combine in the unused events (ie those with 'use' marked as 0
		usort( $event, "sorter" ); // Sort according to the 'unix' field and then the 'block' field
		$event = array_combine( range( 0, count( $event ) - 1 ), $event ); // Re-index the array, from 0 to size-1
		
		do
		{
			$removed = FALSE;
			for ( $i = 0; $i < ( count( $event ) - 1 ); $i++ ) // We need to make sure that the cases with 'use' marked zero, supersede those with it marked as one.
				
			// Loop one less range, because we're checking pairs.
			{
				if ( ( $event[ $i ][ 'unix' ] == $event[ $i + 1 ][ 'unix' ] ) and ( $event[ $i ][ 'block' ] == $event[ $i + 1 ][ 'block' ] ) and ( $event[ $i ][ 'source_unix' ] == $event[ $i + 1 ][ 'source_unix' ] ) ) // OK, only do this, if the time and block in this pair are the same
				{
					if ( $event[ $i ][ 'use' ] and !$event[ $i + 1 ][ 'use' ] ) // the second one is marked "bad", so throw away the one marked "use" (the first)
					{
						unset( $event[ $i ] );
						$removed = TRUE;
					}
					else if ( !$event[ $i ][ 'use' ] and $event[ $i + 1 ][ 'use' ] ) // the first one is marked "bad", so throw away the one marked "use" (the second)
					{
						unset( $event[ $i + 1 ] );
						$i++; // We have to increment the counter, otherwise the next loop will fail, because this event has been deleted
						$removed = TRUE;
					}
					else
					// only need to check the cases where the two cases differ, if they're the same, we should never get here.
					{
						exit( "OK, this should **never** happen.  Awooga awooga" );
					}
				}
			}
			if ( $removed )
				$event = array_combine( range( 0, count( $event ) - 1 ), $event ); // Re-index the array, from 0 to size-1, to allow for any which were removed.
		} while ( $removed );
		
		write_meta( $where_filename, "NumberOfExtendedEvents", count( $event ) );
		
		for ( $i = 0; $i < count( $event ); $i++ )
		{
			write_meta( $where_filename, "Use", $event[ $i ][ 'use' ], chr( ord( "A" ) + $i ) );
			write_meta( $where_filename, "FileName", $event[ $i ][ 'filename' ], chr( ord( "A" ) + $i ) );
			write_meta( $where_filename, "EventTime_Unix", $event[ $i ][ 'unix' ], chr( ord( "A" ) + $i ) );
			write_meta( $where_filename, "EventTime_ISO", unix2iso( $event[ $i ][ 'unix' ] ), chr( ord( "A" ) + $i ) );
			write_meta( $where_filename, "Block", $event[ $i ][ 'block' ], chr( ord( "A" ) + $i ) );
			write_meta( $where_filename, "Source_Unix", $event[ $i ][ 'source_unix' ], chr( ord( "A" ) + $i ) );
		}
	}
}
exit(1); #all is well
?>