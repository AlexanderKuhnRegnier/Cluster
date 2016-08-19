<?php

// Name :		ExtMode_stage1_cli_0_1.php
// Author :		Tim Oddy
//				(C) Space Magnetometer Laboratory, Imperial College London
//
// Version :	0.1
// Date :		2016-07-06
//
// Description
// ===========
//
// Does the initial analysis of Extended Mode data using a couple of states machines.  The first
// looks at the internals of a packet, to decide whether it's plausibly Extended Mode or not, and
// whether it's Even or Odd.  Since there are 444.5 vectors within each packet of Extended Mode
// data, alternate packets have the half vector at the end or start.  The second state machine
// inspects the sequence of packets, to decide which one make up a "block" of data, and then
// extracts this to a data file, and updates a Meta data file, with information about the block.
//
// Input files: /cluster/data/raw/yyyy/mm/C?_yymmdd_v.BS
// Output files: /cluster/data/extended/yyyy/mm/C?_yymmdd_v.META
//               /cluster/data/extended/yyyy/mm/C?_yymmdd_v.En (n=0..) for each Extended Mode Block
//
// Version History
// ===============
//
//		0.1		2016-07-06		Initial Command Line version, derived from Web version

require_once( "meta_file_functions.php" );

define( "EXT", '/home/ahk114/data/extended/');
define( "RAW", '/cluster/data/raw/' );

// Packet State Machine - States

define( "P_INIT", 0 );
define( "P_ODD", 1 );
define( "P_EVEN", 3 );
define( "P_ODD_BADEND", 2 );
define( "P_EVEN_BADEND", 4 );
define( "P_BAD", 5 );
define( "P_ODD_BADSRT", 6 );
define( "P_EVEN_BADSRT", 7 );
define( "P_ERR", 8 );

// Packet State Machine - Inputs

define( "ODD", 0 );
define( "EVEN", 1 );
define( "BOTH", 2 );
define( "NONE", 3 );

// Sequence State Machine - Outputs

define( "NUL", 0x00 );
define( "O_USE", 0x01 );
define( "O_START", 0x02 );
define( "O_ODD", 0x04 );
define( "O_EVEN", 0x08 );
define( "O_MISSING", 0x10 );
define( "O_PARTIAL", 0x20 );
define( "O_EARLYWRITE", 0x40 );
define( "O_LATEWRITE", 0x80 );

// Sequence State Machine - States

//      NUL  ,0
define( "BAD", 2 );
define( "DBLE", 1 );

define( "S_IDLE", 0 );
define( "S_ODD", 1 );
define( "S_EVEN", 2 );

// ========== FUNCTIONS ==========

function convert( $b0, $b1, $b2, $b3, $b4, $b5, $b6, $b7, $comment )
{
	// Takes 8 bytes of data, and converts them into engineering values
	// a range values, and a reset count (as well as adds a comment)
	// This is then output.
	
	$rawx = $b0 * 256 + $b1;
	$rawy = $b2 * 256 + $b3;
	$rawz = $b4 * 256 + $b5;
	
	$range = $b6 >> 4; // <<-- Not correct, we have to also extract the sensor
	
	$reset = ( $b6 & 15 ) * 256 + $b7;
	
	output( $rawx, $rawy, $rawz, $range, sprintf( "%04d ", $reset ) . $comment );
} // convert

function output( $x, $y, $z, $range, $comment )
{
	// Generic output routine, adds the output to a string
	// called outputdata.
	
	// 0         1         2         3         4         5         6         7         8
	// 012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	//
	// 012345678901234567890123 01234567 01234567 01234567 012345678 012345678 021345678
	//
	// 2001-11-02T17:13:30.000Z   51.129   30.099 -140.797   13510.1    9451.1  -42561.3
	
	global $outputdata;
	
	$n             = sprintf( "%6d %6d %6d %1d", $x, $y, $z, $range ) . ' ' . $comment;
	$outputdata[ ] = $n;
} // output

function fgetb( $handle )
{
	// slight mod to create a get byte command
	
	return ord( fgetc( $handle ) );
}

function WriteEntireBlock( )
{
	global $outputdata, $extblockcount, $extdtc, $startsection, $lastgoodendreset, $month, $base, $year, $dir, $filename, $partialstart, $metafilename, $e;
	
	if ( count( $outputdata ) != 0 )
	{
		//		echo "  <B>Extended Block Count     ".$extblockcount."<BR></FONT>";
		//		echo '  Reset Range              '.$startsection.'-'.$lastgoodendreset.'<BR>';
		//		printf('  Aproximate Duration      %8.3f seconds / %2.1f hours</B> <FONT COLOR="C0C0C0"><I>(assumes 5.152s reset period)</I></FONT><B><BR>',($lastgoodendreset-$startsection+4096)%4096*16*5.152,($lastgoodendreset-$startsection+4096)%4096*16*5.152/3600);
		//		echo '  Total number of vectors  '.count($outputdata)."<BR>";
		//		printf('  Aproximate Duration      %8.3f seconds / %2.1f hours</B> <FONT COLOR="C0C0C0"><I>(assumes 4s spin)</I></FONT><BR>',count($outputdata)*4,count($outputdata)*4/3600);
		//		printf("\n");
		
		
		//		echo "<form>";
		//		echo "<input type=\"checkbox\" name=\"click".$extblockcount."\" onclick=\"showMe(".$extblockcount.")\">Show Vectors";
		//		echo "</form>";
		
		//		echo "<DIV ID=\"vectors".$extblockcount."\" style=\"display:none\">";
		
		write_meta( $metafilename, "DumpStartTime_Unix", $extdtc, $extblockcount );
		write_meta( $metafilename, "DumpStartTime_ISO", date( 'Y-m-d\TH:i:s\Z', $extdtc ), $extblockcount );
		write_meta( $metafilename, "ResetCountStart", $startsection, $extblockcount );
		write_meta( $metafilename, "ResetCountEnd", $lastgoodendreset, $extblockcount );
		
		if ( $partialstart )
		{
			write_meta( $metafilename, "PartialStart", "TRUE", $extblockcount );
		}
		
		$block = fopen( EXT . $year . "/" . $month . "/" . $base . ".E" . $extblockcount, "wb" );
		write_meta( $metafilename, "NumberOfVectors", count( $outputdata ), $extblockcount );
		if ( $block )
		{
			//			echo "Vector [Eng Units]         Range\n";
			//			echo "Count  Bx     By     Bz      Reset\n";
			//			echo "=====  =====  =====  ===== = ====\n";
			$extblockcount++;
			
			for ( $n = 0; $n < count( $outputdata ); $n++ )
			{
				//				printf("<FONT COLOR=GRAY>%5d %s</FONT>\n",$n,$outputdata[$n]);
				fputs( $block, $outputdata[ $n ] . "\n" );
			}
			fclose( $block );
		}
		else
		{
			//			printf('<FONT COLOR=RED SIZE=+2>Cannot Open File for writing ('.dir.$filename.'.E'.$extblockcount.')');
			exit - 1;
		}
	}
	$outputdata = array( );

} // WriteEntireBlock

// Arrays used for state machines

$new[ S_IDLE ][ NUL ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_IDLE ][ DBLE ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_IDLE ][ BAD ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_ODD ][ NUL ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_ODD ][ DBLE ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_IDLE,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_ODD ][ BAD ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_EVEN ][ NUL ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_EVEN ][ DBLE ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_IDLE,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);

$new[ S_EVEN ][ BAD ] = array(
	P_INIT => S_IDLE,
	P_BAD => S_IDLE,
	P_ERR => S_IDLE,
	P_ODD => S_ODD,
	P_ODD_BADEND => S_IDLE,
	P_ODD_BADSRT => S_ODD,
	P_EVEN => S_EVEN,
	P_EVEN_BADEND => S_IDLE,
	P_EVEN_BADSRT => S_EVEN 
);


// Sequence - Output table

$out[ S_IDLE ][ 0 ] = array(
	P_INIT => NUL,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE,
	P_ODD_BADEND => NUL,
	P_EVEN => O_EVEN | O_START | O_USE,
	P_EVEN_BADEND => NUL,
	P_BAD => NUL,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE,
	P_ERR => NUL 
);

$out[ S_IDLE ][ DBLE ] = array(
	P_INIT => NUL,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE,
	P_ODD_BADEND => NUL,
	P_EVEN => O_EVEN | O_START | O_USE,
	P_EVEN_BADEND => NUL,
	P_BAD => NUL,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE,
	P_ERR => NUL 
);

$out[ S_IDLE ][ BAD ] = array(
	P_INIT => NUL,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE,
	P_ODD_BADEND => NUL,
	P_EVEN => O_EVEN | O_START | O_USE,
	P_EVEN_BADEND => NUL,
	P_BAD => NUL,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE,
	P_ERR => NUL 
);

$out[ S_ODD ][ 0 ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE | O_EARLYWRITE,
	P_ODD_BADEND => O_EARLYWRITE,
	P_EVEN => O_EVEN | O_USE,
	P_EVEN_BADEND => O_EVEN | O_PARTIAL | O_USE | O_LATEWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

$out[ S_ODD ][ DBLE ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_ODD | O_MISSING | O_USE,
	P_ODD_BADEND => O_ODD | O_MISSING | O_PARTIAL | O_USE | O_LATEWRITE,
	P_EVEN => O_EARLYWRITE,
	P_EVEN_BADEND => O_EARLYWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

$out[ S_ODD ][ BAD ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE | O_EARLYWRITE,
	P_ODD_BADEND => O_EARLYWRITE,
	P_EVEN => O_EVEN | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADEND => O_EARLYWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

$out[ S_EVEN ][ 0 ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_ODD | O_USE,
	P_ODD_BADEND => O_ODD | O_PARTIAL | O_USE | O_LATEWRITE,
	P_EVEN => O_EVEN | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADEND => O_EARLYWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

$out[ S_EVEN ][ DBLE ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_EARLYWRITE,
	P_ODD_BADEND => O_EARLYWRITE,
	P_EVEN => O_EVEN | O_MISSING | O_USE,
	P_EVEN_BADEND => O_EVEN | O_MISSING | O_PARTIAL | O_USE | O_LATEWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

$out[ S_EVEN ][ BAD ] = array(
	P_INIT => O_EARLYWRITE,
	P_ODD => O_ODD | O_MISSING | O_START | O_USE | O_EARLYWRITE,
	P_ODD_BADEND => O_EARLYWRITE,
	P_EVEN => O_EVEN | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADEND => O_EARLYWRITE,
	P_BAD => O_EARLYWRITE,
	P_ODD_BADSRT => O_ODD | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_EVEN_BADSRT => O_EVEN | O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
	P_ERR => O_EARLYWRITE 
);

function packet_analyse( $bytes, &$state, &$startreset, &$stopreset )
{
	// A function which analyses the data in array $bytes.
	// $bytes = payload alone, neither the DDS or Instrument Headers are present.
	// This array contains a total of 3562 bytes, Up to 444½ vectors can be present
	// within this, an 'even' packet has the ½ vector at the end, an 'odd' packet has
	// the ½ vector at the start.
	
	// Byte		0		1		2		3		4		5		6MSN	6LSN	7
	// 															Range	Reset	Reset
	//																	MSB		LSB
	
	// The state machine transition $table within this function, ie for analysing the internals
	// of the packet alone.
	
	//                            OE #########
	//                          /----#       # R
	//                          |    #   0   #----------------------------------------------\
	//                          \--->#       #                                              |
	//                               #########                                              V
	//                               O |   | E                                          ######### R/OE
	//                          /------/   \------\                                     #       #----\
	//                          |                 |                                     #   5   #    |
	//                          V                 V                                     #       #----/
	//                 O/OE #########         ######### E/OE                            #########
	//                 /----#       #         #       #----\                            O |   | E
	//                 |    #   1   #         #   3   #    |                       /------/   \------\
	//                 \--->#       #         #       #<---/                       |                 |
	//                      #########         #########                            V                 V
	//                      R |   | E         O |   | R                   O/OE #########         ######### E/OE
	//           /------------/   |             |   \------------\        /----#       #         #       #----\
	//           |                \----\   /----/                |        |    #   6   #         #   7   #    |
	//           |                     |   |                     |        \--->#       #         #       #<---/
	//           V                     |   |                     V             #########         #########
	//    R  #########                 |   |                 #########  R      E/R |             O/R |
	//  /----#       #                 |   |                 #       #----\        |                 |
	//  |    #   2   #                 |   |                 #   4   #    |        |                 |
	//  \--->#       #                 |   |                 #       #<---/        |                 |
	//       #########                 V   V                 #########             |                 |
	//           | E/O/OE            #########            E/O/OE |                 |                 |
	//           \------------------>#       #<------------------/                 |                 |
	//                               #   8   #<------------------------------------/                 |
	//                               #       #<------------------------------------------------------/
	//                               #########
	//                                    
	//   1   = All Odd                          P_ODD
	//   3   = All Even                         P_EVEN
	// 
	//   2,6 = Partially Odd                    P_ODD_BADEND P_ODD_BADSRT
	//   4,7 = Partially Even                   P_EVEN_BADEND P_ODD_BADSRT
	//   5   = All Bad (ie not Extended Mode)   P_BAD
	//   8   = Erroneous                        P_ERR
	// 
	//   2,4 = Bad at End                       P_ODD_BADEND P_EVEN_BADEND
	//   6,7 = Bad at Start                     P_ODD_BADSRT P_EVEN_BADSRT
	//
	//   0   P_INIT                                           NOT_USEFUL
	//   1                   ODD
	//   2                   ODD   PARTIAL  END_BAD
	//   3                   EVEN
	//   4                   EVEN  PARTIAL  END_BAD
	//   5                                                    NOT_USEFUL
	//   6                   ODD   PARTIAL  START_BAD
	//   7                   EVEN  PARTIAL  START_BAD
	//   8                                             ERROR  NOT_USEFUL
	
	
	// State Transition Table for Packet to Packet
	
	$table[ P_INIT ][ ODD ]         = P_ODD;
	$table[ P_INIT ][ EVEN ]        = P_EVEN;
	$table[ P_INIT ][ BOTH ]        = P_INIT;
	$table[ P_INIT ][ NONE ]        = P_BAD;
	$table[ P_ODD ][ ODD ]          = P_ODD;
	$table[ P_ODD ][ EVEN ]         = P_ERR;
	$table[ P_ODD ][ BOTH ]         = P_ODD;
	$table[ P_ODD ][ NONE ]         = P_ODD_BADEND;
	$table[ P_ODD_BADEND ][ ODD ]   = P_ERR;
	$table[ P_ODD_BADEND ][ EVEN ]  = P_ERR;
	$table[ P_ODD_BADEND ][ BOTH ]  = P_ERR;
	$table[ P_ODD_BADEND ][ NONE ]  = P_ODD_BADEND;
	$table[ P_EVEN ][ ODD ]         = P_ERR;
	$table[ P_EVEN ][ EVEN ]        = P_EVEN;
	$table[ P_EVEN ][ BOTH ]        = P_EVEN;
	$table[ P_EVEN ][ NONE ]        = P_EVEN_BADEND;
	$table[ P_EVEN_BADEND ][ ODD ]  = P_ERR;
	$table[ P_EVEN_BADEND ][ EVEN ] = P_ERR;
	$table[ P_EVEN_BADEND ][ BOTH ] = P_ERR;
	$table[ P_EVEN_BADEND ][ NONE ] = P_EVEN_BADEND;
	$table[ P_BAD ][ ODD ]          = P_ODD_BADSRT;
	$table[ P_BAD ][ EVEN ]         = P_EVEN_BADSRT;
	$table[ P_BAD ][ BOTH ]         = P_BAD;
	$table[ P_BAD ][ NONE ]         = P_BAD;
	$table[ P_ODD_BADSRT ][ ODD ]   = P_ODD_BADSRT;
	$table[ P_ODD_BADSRT ][ EVEN ]  = P_ERR;
	$table[ P_ODD_BADSRT ][ BOTH ]  = P_ODD_BADSRT;
	$table[ P_ODD_BADSRT ][ NONE ]  = P_ERR;
	$table[ P_EVEN_BADSRT ][ ODD ]  = P_ERR;
	$table[ P_EVEN_BADSRT ][ EVEN ] = P_EVEN_BADSRT;
	$table[ P_EVEN_BADSRT ][ BOTH ] = P_EVEN_BADSRT;
	$table[ P_EVEN_BADSRT ][ NONE ] = P_ERR;
	$table[ P_ERR ][ ODD ]          = P_ERR;
	$table[ P_ERR ][ EVEN ]         = P_ERR;
	$table[ P_ERR ][ BOTH ]         = P_ERR;
	$table[ P_ERR ][ NONE ]         = P_ERR;
	
	
	$counteven = 0; // Number of even vectors
	$countodd  = 0; // Number of odd vectors
	$state     = P_INIT; // Initial State of State Machine
	
	// Set these reset values on the various first possible even and odd vectors
	// Even vectors are at 0+n*8, Odd vectors are at 4+n*8
	// +0,+1 are Bx  +2,+3 are By  +4,+5 are By
	// +6 is SNNN RRRR    S = Sensor, 0 for OB, 1 for IB   NNN = Range
	// +7 is RRRR RRRR    RRRR RRRR RRRR = Reset Count, 12 MSB
	
	// Reset Count will increment by 0 or 1 (Modulo 4096) where there is valid data.
	// The Sensor value will not change with a period of Extended Mode operation.
	// The Range must be two or higher (zero and one are invalid).  For early data the range will also be five
	// or below. but with later data, due to lowering of the spacecraft orbits, the supposedly non-operational
	// ranges 6 or 7 can bs used.
	
	// Set the previous values for the reset counts to the values for vector zero (this will change, at the loop end).
	// Set the first value for the sensors (this will not change)
	
	$prevreseteven   = ( $bytes[ 6 ] & 15 ) * 256 + $bytes[ 7 ];
	$prevresetodd    = ( $bytes[ 10 ] & 15 ) * 256 + $bytes[ 11 ];
	$firstsensoreven = $bytes[ 6 ] >> 7;
	$firstsensorodd  = $bytes[ 10 ] >> 7;
	
	// Loop around the 444 entire vectors (there are 444.5, but we'll ignore the half vector here)
	
	for ( $n = 1; $n < 444; $n++ )
	{
		$rangeeven  = ( $bytes[ $n * 8 + 6 ] >> 4 ) & 0x07; // This is the Range, if the packet is even
		$reseteven  = ( $bytes[ $n * 8 + 6 ] & 15 ) * 256 + $bytes[ $n * 8 + 7 ]; // Thie is the Reset Count, if the packet is even
		$sensoreven = $bytes[ $n * 8 + 6 ] >> 7;
		$rangeodd   = ( $bytes[ $n * 8 + 10 ] >> 4 ) & 0x07; // This is the Range, if the packet is odd
		$resetodd   = ( $bytes[ $n * 8 + 10 ] & 15 ) * 256 + $bytes[ $n * 8 + 11 ]; // This is the Reset Count, if the packet is odd
		$sensorodd  = $bytes[ $n * 8 + 10 ] >> 7;
		
		// Unused vector areas can be set to AAAA5555AAAA5555 or 5555AAAA5555AAAA, which should be ignored
		
		$invalid = ( ( $bytes[ $n + 8 ] == 0x55 ) && ( $bytes[ $n * 8 + 1 ] == 0x55 ) && ( $bytes[ $n * 8 + 2 ] == 0xAA ) && ( $bytes[ $n * 8 + 3 ] == 0xAA ) && ( $bytes[ $n * 8 + 4 ] == 0x55 ) && ( $bytes[ $n * 8 + 5 ] == 0x55 ) && ( $bytes[ $n * 8 + 6 ] == 0xAA ) && ( $bytes[ $n * 8 + 7 ] == 0xAA ) ) || ( ( $bytes[ $n + 8 ] == 0xAA ) && ( $bytes[ $n * 8 + 1 ] == 0xAA ) && ( $bytes[ $n * 8 + 2 ] == 0x55 ) && ( $bytes[ $n * 8 + 3 ] == 0x55 ) && ( $bytes[ $n * 8 + 4 ] == 0xAA ) && ( $bytes[ $n * 8 + 5 ] == 0xAA ) && ( $bytes[ $n * 8 + 6 ] == 0x55 ) && ( $bytes[ $n * 8 + 7 ] == 0x55 ) );
		
		if ( ( $rangeeven >= 2 ) && ( ( ( $reseteven - $prevreseteven + 4096 ) % 4096 ) <= 1 ) && $sensoreven == $firstsensoreven && !$invalid )
		{
			$counteven++;
			$iseven = 1;
			if ( !isset( $startreseteven ) )
				$startreseteven = $reseteven;
			$stopreseteven = $reseteven;
		}
		else
			$iseven = 0;
		
		if ( ( $rangeodd >= 2 ) && ( ( ( $resetodd - $prevresetodd + 4096 ) % 4096 ) <= 1 ) && $sensorodd == $firstsensorodd && !$invalid )
		{
			$countodd++;
			$isodd = 1;
			if ( !isset( $startresetodd ) )
				$startresetodd = $resetodd;
			$stopresetodd = $resetodd;
		}
		else
			$isodd = 0;
		
		if ( $isodd && !$iseven )
			$state = $table[ $state ][ ODD ];
		elseif ( $iseven && !$isodd )
			$state = $table[ $state ][ EVEN ];
		elseif ( $iseven && $isodd )
			$state = $table[ $state ][ BOTH ];
		else
			$state = $table[ $state ][ NONE ];
		
		$prevreseteven = $reseteven;
		$prevresetodd  = $resetodd;
	}
	
	// Set and return values, depending on whether this is (apparently) an Odd or Even packet
	
	if ( ( $state == P_EVEN ) || ( $state == P_EVEN_BADSRT ) || ( $state == P_EVEN_BADEND ) )
	{
		$startreset = $startreseteven;
		$stopreset  = $stopreseteven;
		return $counteven;
	}
	if ( ( $state == P_ODD ) || ( $state == P_ODD_BADSRT ) || ( $state == P_ODD_BADEND ) )
	{
		$startreset = $startresetodd;
		$stopreset  = $stopresetodd;
		return $countodd;
	}
	else
	{
		$startreset = -1;
		$stopreset  = -1;
		return 0;
	}
} // packet_analyse

// ========== END OF FUNCTIONS ==========


// State Table information for overall MSA Extended mode 'set'.
// $new[<PREV STATE>,<PACKET GOODNESS>,<PACKET STATE MACHINE>)
//$new[$state][$in][$retstate];
//$in=$double+2*$badpacket;
//$double two packets jumped (ie reset 123->125)
//$badpacket is a bad packet (not sure if external or internal or either!)

// Bits 0 (1)   Use (This packet has good data, use it)
//      1 (2)   Start (ie start recording data from this point)
//      2 (4)   Odd (If True, Even is False)
//      3 (8)   Even (If True, Odd is False) (If Even False != Odd True, both can be False)
//      4 (16)  Missing (Previous Packet, ie Parity = Not Current Parity)
//      5 (32)  Partial (If Start, then start of packet mising, if Write, then end of packet missing)
//      6 (64)  Early Write (Write the existing data, don't use any data in the current packet)
//      7 (128) Late Write (Write the existing data, DO use any data in the current packet)



$outputdata = array( );

set_time_limit( 600 );  // Catches out infinte loops

if ( PHP_SAPI != "cli" )
	exit( "THIS SHOULD ONLY BE RUN USING THE PHP CLI\r\n" );

if ( $argc != 6 )
	exit( "NEEDS 5 parameters : stage1_cli.php <sc> <year> <month> <day> <vers>\r\n" );

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

$month = sprintf( "%02d", $month );
$day   = sprintf( "%02d", $day );

$base         = "C" . $sc . "_" . $shortyear . $month . $day . "_" . $version;
$datafilename = RAW . $year . "/" . $month . "/" . $base . ".BS";

if ( !file_exists( $datafilename ) )
	exit(1);#return code for invalid file!

$metafilename = EXT . $year . '/' . $month . '/' . $base . ".META";

if ( !is_dir( EXT . $year ) )
	mkdir( EXT . $year, 0750 );

if ( !is_dir( EXT . $year . '/' . $month ) )
	mkdir( EXT . $year . '/' . $month, 0750 );

write_meta( $metafilename, "SourceFile", $datafilename );
write_meta( $metafilename, "ProcessingTime_ISO", date( "Y-m-d\TH:i:s\Z" ) );

$handle = fopen( $datafilename, "r" );

$fsize = filesize( $datafilename );

$extblockcount = 0;
$etime         = 0;

$previousreset    = 999999;
$previousextreset = 999999;
$packetcount      = 0;
$lastextreset     = 999999;
$firstreset       = 999999;
$lastzero         = 999999;
$state            = 0;

// Packet Header (DDS, added by ESOC)
//
// Bytes 0 - 7           SCET Time
// Byte 8                ID (Not Needed)
// Bytes 9 - 11          Length
// Byte 12 Lower Nibble  Groundstation (Not Needed)
// Byte 12 Upper Nibble  Spacecraft
// Byte 13               Datastream (Not Needed)
// Byte 14 Lower Nibble  TASI (Not Needed)
// Byte 14 Upper Nibble  Time Quality (Not Needed)
//
// Science Telemetry Header (Added by FGM on S/C)
//
// Bytes 15

// Packet Date & Time            Reset Mode  State   Resets
//                                              Size Sta End
//
// 0000 | 16 Jan 2004 00:04:05 | 7457   C    0     0 000 000  000  | 0 |  State 0  Out   0  In 2            0
// 0001 | 16 Jan 2004 00:04:10 | 7458  EXT   5     0 FFFFFFFF FFFFFFFF  000  | 0 |  State 0  Out   0  In 0            0
// 0002 | 16 Jan 2004 00:04:15 | 7459  EXT   5     0 FFFFFFFF FFFFFFFF  000  | 0 |  State 0  Out   0  In 0            0
// 0003 | 16 Jan 2004 00:04:20 | 745A  EXT   8     1 172 172  000  | 0 |  State 0  Out   0  In 2            0
// 0004 | 16 Jan 2004 00:04:25 | 745B  EXT   8     1 81E 81E  000  | 0 |  State 0  Out   0  In 2            0
//
// Mode = 0->E or EXT for "F" (0xF / 15)
// State = State returned from Packet Analysis
// Resets Sta & End are the Starting and Ending Resets of the data within the Extended Mode packet.

// Bodge to get rid of error messages about variables being undefined

$s    = NULL;
$e    = NULL;
$size = NULL;

//echo "<DIV STYLE=\"position: fixed; top: 0px; background-color: #F0F0F0;\">";
//printf("Pack  Pack                      Pack  TM      E    E              Ext         Flags<BR>");
//printf("#     Date and Time             Rst   Mode P  Size Reset                      USOMPEW Vectors in<BR>");   
//printf("                                                   Srt  End  Dif  S  Out B D    E  LW Packet<BR>");
//printf("====  ========================  ====  ===  =  ===  ===  ===  ===  =  ==  ===  =<B>=</B>=<B>=</B>=<B>==</B> ====<BR>");
//echo "</DIV>";

while ( ftell( $handle ) < $fsize )
{
	// Get the SCET data from the DDS header
	for ( $n = 0; $n < 15; $n++ )
		$header[ $n ] = fgetb( $handle );
	
	$headlen = $header[ 9 ] * 65536 + $header[ 10 ] * 256 + $header[ 11 ];
	$headsc  = $header[ 12 ] >> 4;
	
	// Information: The packet count
	
	//	printf("%04d  ",$packetcount);
	
	// Packet Header
	
	$packetcount++;
	
	// SCET is Bytes 0-1 : Days from 1st Jan 1958
	//         Bytes 2-5 : Milliseconds in Day
	//         Bytes 6-7 : Microseconds in Milliseconds
	
	$scetday = $header[ 0 ] * 256 + $header[ 1 ];
	$scetms  = $header[ 2 ] * 16777216 + $header[ 3 ] * 65536 + $header[ 4 ] * 256 + $header[ 5 ];
	$scetus  = $header[ 6 ] * 256 + $header[ 7 ];
	
	$dtc = mktime( 0, 0, $scetms / 1000, 1, 1 + $scetday, 1958 ); // Convert SCET days into Unix Seconds from 1st Jan 1970
	
	$date = date( "Y-m-d\TH:i:s", $dtc ); // Convert that value into ISO date and time (without the decimal bit or 'Z')
	
	// Information: The date and time, in ISO format, including microseconds
	
	//	printf("%s.%03dZ  ",$date,$scetms%1000);
	
	$telemstatus    = fgetb( $handle ) * 256 + fgetb( $handle ); // Used to determine whether we're in Extended Mode
	$telemhfreset   = fgetb( $handle ) * 256 + fgetb( $handle ); // Not currently used
	$telemhflastsun = fgetb( $handle ) * 256 + fgetb( $handle ); // Used to determin deltahfsun (which is then not used)
	$telemhfthissun = fgetb( $handle ) * 256 + fgetb( $handle ); // Used to determin deltahfsun (which is then not used)
	$telemhf1ry     = fgetb( $handle ) * 256 + fgetb( $handle ); // Not currently used
	$telemhf2ry     = fgetb( $handle ) * 256 + fgetb( $handle ); // Not currently used
	$telemreset     = fgetb( $handle ) * 256 + fgetb( $handle ); // The reset counter value of the *packet*
	$telemmode      = fgetb( $handle ); // The Telemetry Mode
	
	// Ignore Varianace
	fseek( $handle, 19, SEEK_CUR );
	
	$deltahfsun = $telemhfthissun - $telemhflastsun;
	if ( $deltahfsun < 0 )
		$deltahfsun += 65536;
	
	// Information: The packet reset count (ie at the time of data downlink)
	
	//	printf("%04X  ",$telemreset);
	
	if ( ( $telemstatus & 0x0F ) == 15 )
	{
		$msa = array_slice( unpack( "C*", fread( $handle, 3562 ) ), 0 );
		
		$size = packet_analyse( $msa, $retstate, $s, $e );
		
		// Information: IN EXTENDED MODE - TM Mode (EXT), the value returned by the packet analysis
		// State Machine, the number of vectors in the packet (not including the first vector, or the
		// half vector ie a maximum of 443), the first and last extended mode reset counts (ie those
		// recorded into the MSA when the data was collected), but *only* the top 12 most significant
		// bits.
		// (The "& 0xFFF" clips -1 values to 0xFFF).
		
		//		printf("EXT  %1d  %3d  %03X  %03X  ",$retstate,$size,$s & 0xFFF,($e & 0xFFF));
		
		// WORKS !!!! If Missing packet, ie Pack Reset +2, then DONT check Vector Reset,
		// because it *WILL* be wrong as well (doh!)
		
		if ( ( $previousreset == 999999 ) || // If this is the first time or the packet has gone up by one
			( ( $telemreset - $previousreset ) == 1 ) || // or a rollover.
			( ( $previousreset - $telemreset ) == 65535 ) )
		{
			if ( ( $previousextreset == 999999 ) || // ... and this is the first extended mode or extended mode
				( ( ( $s - $previousextreset ) == 0 ) || // has gone up by zero or one, or a rollover
				( ( $s - $previousextreset ) == 1 ) ) || ( ( $previousextreset - $e ) == 4095 ) )
			{
				$badpacket = 0; // So, this isn't a bad or a double bad, the reset count
				$double    = 0; // went up by one, and the ext mode reset count by 1 or 0.
			}
			else
			{
				$badpacket = 1; // Uhoh, the ext mode reset count changed by some odd number,
				$double    = 0; // so mark things as bad.
			}
		}
		elseif ( ( ( $telemreset - $previousreset ) == 2 ) || // OK, did the packet reset count go up by two?
			( ( $previousreset - $telemreset ) == 65534 ) )
		{
			$badpacket = 0; // Yes, so we have a single missing packet, not 'bad' as such.
			$double    = 1;
		}
		else
		{
			$badpacket = 1; // No, so stuff is just messed up, mark as bad.
			$double    = 0;
		}
		
		$previousextreset = $e; // Now set these previous values, so next time around, we
		$previousreset    = $telemreset; // have something to check against
	}
	else // This isn't an extended mode packet, so it's clearly
		
	// bad
	{
		// Information: just display some blank bits
		//		printf(" <FONT COLOR=RED>%01X</FONT>   -   -    -    -   ",$telemstatus&0x0F);
		// Jump over the reaminder of the packet, we don't care what is in it.
		fseek( $handle, $headlen - 34, SEEK_CUR );
		$badpacket = 1; // This is a bad packet
		$double    = 0; // We didn't simply miss a packet
		$retstate  = 0; // Lets set the state (used as input to the next stage) token_name
	} // zero, the initial state, which is where it sits if the system is unsure
	
	$in = $double + 2 * $badpacket; // Form Double and Bad into one convenient value
	
	$output = $out[ $state ][ $in ][ $retstate ]; // $output is what we do at this point
	$state  = $new[ $state ][ $in ][ $retstate ]; // $state is the new state (basically either Bad, Odd or Even)
	
	//	$disp_stuff=disp($output); // Need to do this here (rather than in the printf) so $ispartial gets set for the next bit
	
	$use        = ( $output & 1 ) != 0;
	$isstart    = ( $output & 2 ) != 0;
	$isodd      = ( $output & 4 ) != 0;
	$iseven     = ( $output & 8 ) != 0;
	$ismissing  = ( $output & 16 ) != 0;
	$ispartial  = ( $output & 32 ) != 0;
	$writeearly = ( $output & 64 ) != 0;
	$writelate  = ( $output & 128 ) != 0;
	
	// Generate a string based upon some status variables, and sets various globals
	//
	//  U S O M P EW LW          (nine characters long, displayed spaces not present)
	//      E  
	//  U (Black)    = Use this packet or " "
	//  S (Green)    = Start " "
	//  O (Blue)     = Odd packet or
	//    E (Blue)   = Even packet or " "
	//  M (Red)      = Missing or " "
	//  P (Black)    = Partial or " "
	//  EW (Green)   = Early Write or
	//    LW (Green) = Late Write or "  "
	
	$disp_stuff = "<B>";
	$disp_stuff .= $use ? "<FONT COLOR=BLACK>U</FONT>" : " ";
	$disp_stuff .= $isstart ? "<FONT COLOR=GREEN>S</FONT>" : " ";
	$disp_stuff .= $isodd ? "<FONT COLOR=BLUE>O</FONT>" : ( $iseven ? "<FONT COLOR=BLUE>E</FONT>" : " " );
	$disp_stuff .= $ismissing ? "<FONT COLOR=RED>M</FONT>" : " ";
	$disp_stuff .= $ispartial ? "<FONT COLOR=BLACK>P</FONT>" : " ";
	$disp_stuff .= $writeearly ? "<FONT COLOR=GREEN>EW</FONT>" : ( $writelate ? "<FONT COLOR=GREEN>LW</FONT>" : "  " );
	$disp_stuff .= "</B>";
	
	// Spin is roughly between 3.9 and 4.4 seconds, so 444 spins will take between 1731 seconds and
	// 1954 seconds.  With resets at around 5.152 seconds, it will increment betweem 336 and 379 times,
	// but we only see the top 12 bits, so divide this by 16 to get a range or 21 to 24.
	// (That's all a bit rough and ready, but you get the idea).
	// If we're outside that range (and ignoring the zero values), display this hexadecimal difference
	// value in Red.
	
	if ( ( $s != -1 ) && ( $e != -1 ) )
	{
		$delta = ( ( $e - $s ) + 0xFFF ) % 0xFFF;
	}
	else
	{
		$delta = -1;
	}
	
	// Information: If the delta value is sensible, then display it.  If it's outside of 
	// a reasonable range (as above) then put it in red.
	
	if ( $ispartial )
	{
		//		printf("%03X  ",$delta);
	}
	else
	{
		if ( $delta == -1 )
		{
			//			printf(" -   ");
		}
		else if ( $delta != 0 )
		{
			if ( ( $delta > 24 ) || ( $delta < 21 ) )
			{
				//				printf("<FONT COLOR=\"RED\">%03X</FONT>  ",$delta);
				
				// Also record that this has occured.  I'm not sure that this is a sensible
				// descriptor BadSpinCount ?
				inc_meta( $metafilename, "BadSunPacketCount", $extblockcount );
			}
			else
			{
				//				printf("%03X  ",$delta);
			}
		}
		else
		{
			//			printf(" -   ");
		}
	}
	
	// Information: Display the current state, what response has come from the state machine
	// Whether it B (Bad) or D (Double) and the flags.
	
	//	printf("%d  %02X  %3s  %s",$state,$output,($in==1)?"  D":(($in==2)?"B  ":"   "),$disp_stuff);
	
	// If we have some output data, then display how many values there are
	
	//	if (count($outputdata)!=0)
	//		echo " ".count($outputdata)." ";
	
	//	echo"<BR>";
	
	// Time to act upon flags
	// order is
	//
	// $writeearly
	// $isstart
	// $ismissing($isodd,$iseven)
	// $use($isodd,$iseven,$ispartial,$isstart)    (effect if $partial depending on whether $isstart or not)
	// $writelate
	
	// First do Early Write
	// If there's some data, write it out.
	
	
	if ( $writeearly )
	{
		//		echo "<BR><B>Early Write</B><BR>";
		WriteEntireBlock();
	}
	
	if ( $isstart ) // OK, this is the start of an Extended Mode block
	{
		$missing      = 0; // Set the number of missing blocks to zero
		$startsection = $s; // Set the start of this section, in ext reset counter terms
		$extdtc       = $dtc; // Record the packet SCET (in Unix terms)
		if ( $ispartial ) // If this is a partial packet, tag it
			$partialstart = TRUE;
		else
			unset( $partialstart );
		
		// Reset the BadSunPacketCount nad MissingPacket values
		write_meta( $metafilename, "BadSunPacketCount", 0, $extblockcount );
		write_meta( $metafilename, 'MissingPacket', 0, $extblockcount );
	}
	
	if ( $ismissing ) // If the packet is missing, we write out some blank vectors, to fill the gap.
		
	// We increment the record of how many packets are missing.
	{
		//		debug("Missing");
		write_meta( $metafilename, 'MissingPacket' . $missing++ . "_FollowingResetCount", $s, $extblockcount );
		if ( $isodd )
		{
			//				debug("Odd");
			// OK, this packet is odd, so missing packet was even, and we don't have the half a vector
			for ( $n = 0; $n < 445; $n++ ) // <<-- Is this correct?
			{
				output( 0, 0, 0, 0, "0000 MISSING EVEN " . $n );
				//					debug($n);
			}
			//				debug("Before IncMeta");
			//				debug($metafilename);
			//				debug($extblockcount);
			//				$q=read_meta($metafilename,'MissingPacket',$extblockcount);
			//				$q+=1;
			//				write_meta($metafilename,'MissingPacket',$q,$extblockcount);
			inc_meta( $metafilename, 'MissingPacket', $extblockcount );
			//				debug("After IncMeta");
			
		}
		elseif ( $iseven )
		{
			//				debug("Even");
			// OK, this packet is even, so missing packet was odd, throw away the half a vector.
			for ( $n = 0; $n < 446; $n++ ) // <<-- Is this correct?
				output( 0, 0, 0, 0, "0000 MISSING ODD " . $n );
			inc_meta( $metafilename, 'MissingPacket', $extblockcount );
		}
		//		debug("MissingEnd");
	}
	
	//	debug("X");
	
	if ( $use ) // We should use this packet, it's good.
	{
		//		debug("Use");
		if ( $ispartial ) // We've only got part of a packet
		{
			if ( $isstart ) // Partial at Start, so data is at the end of the packet
			{
				if ( $isodd )
				{
					for ( $n = 0; $n < ( $size + 1 ); $n++ )
					{
						$pos = 8 * ( 443 - $size + $n ) + 4;
						convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "PARTIAL START ODD " . $n );
					}
				}
				elseif ( $iseven )
				{
					for ( $n = 0; $n < ( $size + 1 ); $n++ )
					{
						$pos = 8 * ( 443 - $size + $n );
						convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "PARTIAL START EVEN " . $n );
						
					}
					for ( $n = 0; $n < 4; $n++ )
						$halfvector[ $n ] = $msa[ 8 * 444 + $n ];
				}
			}
			else // Must be at the end, so data is at the start of the packet
			{
				if ( $isodd )
				{
					if ( $ismissing )
						output( 0, 0, 0, 0, "0000 PARTIAL END ODD, FILL MISSING HALF VECTOR" );
					else
						convert( $halfvector[ 0 ], $halfvector[ 1 ], $halfvector[ 2 ], $halfvector[ 3 ], $msa[ 0 ], $msa[ 1 ], $msa[ 2 ], $msa[ 3 ], "PARTIAL END ODD, COMPLETE HALF VECTOR" );
					
					for ( $n = 0; $n < ( $size + 1 ); $n++ ) // NB Max Size from proc is 443 vectors
					{
						$pos = 8 * $n + 4;
						convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "PARTIAL END ODD " . ( $n + 1 ) );
					}
				}
				elseif ( $iseven )
				{
					for ( $n = 0; $n < ( $size + 1 ); $n++ )
					{
						$pos = 8 * $n;
						convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "PARTIAL END EVEN " . $n );
					}
				}
			}
		}
		else // Must be a whole packet
		{
			if ( $isodd )
			{
				// If the previous vector was missing, then we have to "invent" a blank
				// vector, since the remainder isn't useful.
				// Otherwise, just use the half vector from the last even packet, and combine
				// it to generate the entire vector from two halves.
				// Then output the remaining 444 vectors.
				
				if ( $ismissing )
					output( 0, 0, 0, 0, "0000 WHOLE ODD, FILL MISSING HALF VECTOR" );
				else
					convert( $halfvector[ 0 ], $halfvector[ 1 ], $halfvector[ 2 ], $halfvector[ 3 ], $msa[ 0 ], $msa[ 1 ], $msa[ 2 ], $msa[ 3 ], "WHOLE ODD, COMPLETE HALF VECTOR" );
				for ( $n = 0; $n < 444; $n++ )
				{
					$pos = 8 * $n + 4;
					convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "WHOLE ODD " . ( $n + 1 ) );
				}
			}
			elseif ( $iseven ) // For an Even vector, write out the 444 vectors, and then
				
			// record the details of the half of a vector.
			{
				for ( $n = 0; $n < 444; $n++ )
				{
					$pos = 8 * $n;
					convert( $msa[ $pos ], $msa[ $pos + 1 ], $msa[ $pos + 2 ], $msa[ $pos + 3 ], $msa[ $pos + 4 ], $msa[ $pos + 5 ], $msa[ $pos + 6 ], $msa[ $pos + 7 ], "WHOLE EVEN " . $n );
				}
				for ( $n = 0; $n < 4; $n++ )
					$halfvector[ $n ] = $msa[ 8 * 444 + $n ];
			}
		}
		$lastgoodendreset = $e;
	} // End of ($use)
	
	if ( $writelate )
	{
		//		echo "<BR><B>Late Write</B><BR>";
		WriteEntireBlock();
	}
}

// If we get to the end, and we *still* have some data in $output data, we need to write this
// out, otherwise we lose it.  This code should be identical to the EarlyWrite code.

if ( count( $outputdata ) != 0 )
{
	//	echo "<BR><B>Terminal Write</B><BR>";
	WriteEntireBlock();
}

write_meta( $metafilename, "NumberOfBlocks", $extblockcount );
exit(0);
?>