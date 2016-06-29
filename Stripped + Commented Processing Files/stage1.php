<?php
/*
Delete the following 3 lines, AND LAST LINE for deployment, or figure out why permission to normal session folder are denied
*/
session_destroy();
ini_set('session.save_path','/home/ahk114'. '/testing/'. 'session/'); 
session_start();

/**AKR Comments*/
#AKR Comments
#previous comments by Cary Colgan used where available, but overwritten where wrong / NA

//The Meta functions, here we only use write_meta and inc_meta
#created META files go into the EXT directory

require("meta_file_functions.php");

function convert($b0,$b1,$b2,$b3,$b4,$b5,$b6,$b7,$comment)
{
	// Takes 8 bytes of data, and converts them into engineering values
	// a range values, and a reset count (as well as adds a comment)
	// This is then output.
	#doesn't  convert units, just shifts bits to correct position and stores the true value in $rawx, etc..
	$rawx=$b0*256+$b1;
	$rawy=$b2*256+$b3;
	$rawz=$b4*256+$b5;

	$range=$b6>>4;   // <<-- Not correct, we have to also extract the sensor
	#need to extract sensor ID - ie IB(1) or OB(0) - from +6 is SNNN RRRR, S = Sensor, 0 for OB, 1 for IB   NNN = Range -measuring range, ie. 2-5 (or 6,7)
	#should be? -neglected because sensor ID is *always* 0 (OB)
	#$range=($b6&112)>>4;
	
	$reset=($b6&15)*256+$b7; #15=0b00001111 so isolates the LS nibble only, as this is the range. $b7*256 effectively shifts is to the left by 8 bits <<8

	output($rawx,$rawy,$rawz,$range,sprintf("%04d ",$reset).$comment);
}

function output($x,$y,$z,$range,$comment)
{
	// Generic output routine, adds the output to a string
	// called outputdata.
	
	#this string is written out in the WriteEntireBlock function
	
	// 0         1         2         3         4         5         6         7         8
	// 012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	//
	// 012345678901234567890123 01234567 01234567 01234567 012345678 012345678 021345678
	//
	// 2001-11-02T17:13:30.000Z   51.129   30.099 -140.797   13510.1    9451.1  -42561.3
	#data here is related to xyz components, measurement range and comments, note dates!
	global $outputdata;

	$n=sprintf("%6d %6d %6d %1d",$x,$y,$z,$range).' '.$comment;
	$outputdata[]=$n;#shown when "show vectors" is ticked
}

function fgetb($handle)
{
	// slight mod to create a get byte command

	return ord(fgetc($handle));							#Returns ASCII value of current position in data file
}
/*
$base="C".$sc."_".$shortyear.$month.$day."_".$version;
*/
#outputdata: string appended to by output function, contains xyz components in engineering units, measurement range and comment
#extblockcount: number of extended mode data blocks
#$extdtc: if($isstart) -> =$dtc, SCET Time, Bytes 0-7 in DDS Packet Header
	// SCET is Bytes 0-1 : Days from 1st Jan 1958
	//         Bytes 2-5 : Milliseconds in Day
	//         Bytes 6-7 : Microseconds in Milliseconds
	#$dtc is SCET days converted into Unix seconds from 1st Jan 1970 (seconds from Unix epoch)
	
#$month: month - from selection
#$base:see above
#$year: year - from selection

#$filename: name or BS dump file
#$partialstart: Boolean - whether partial start or not
#$metafilename: name of metafile

#"RAW" - constant, directory of raw BS files  
#$datafilename=RAW.$year."/".$month."/".$base.".BS";
#"EXT" - constant, describes directory of extended data files - metafiles are output here .META as well as .E[$extblockcount] files
#containing the data from the convert function

#$startsection: again, if($isstart), $startsection=$s; // Set the start of this section, in ext reset counter terms 
#$s=NULL, redefined in packet_analyse by reference!!!
#$e: also redefined in packet_analyse by reference!!!
#$lastgoodendreset:=$e

/**PROBLEM*/
#$dir:? - supposed to be BS file directory?


function WriteEntireBlock()
{
	#Writes data to webpage
	#Writes data to metafile
	
	global $outputdata,$extblockcount,$extdtc,$startsection,$lastgoodendreset,$month,$base,$year,$dir,$filename,$partialstart,$metafilename,$e;
	#access global variables modified elsewhere
	if (count($outputdata)!=0)
	{
		/*
		See original code for the 2 measures of approximate duration!
		*/

		#write metadata to META file in EXT directory
		write_meta($metafilename,"DumpStartTime_Unix",$extdtc,$extblockcount);
		write_meta($metafilename,"DumpStartTime_ISO",date('Y-m-d\TH:i:s\Z',$extdtc),$extblockcount);
		write_meta($metafilename,"ResetCountStart",$startsection,$extblockcount);
		write_meta($metafilename,"ResetCountEnd",$lastgoodendreset,$extblockcount);
		
		if ($partialstart)
		{
			write_meta($metafilename,"PartialStart","TRUE",$extblockcount);
		}

		$block=fopen(EXT.$year."/".$month."/".$base.".E".$extblockcount,"wb"); #opens(creates) the processed data file 
		#(for data from convert, output) corresponding to the specified extblock
		write_meta($metafilename,"NumberOfVectors",count($outputdata),$extblockcount);
		if ($block)#if file can be opened
		{
			$extblockcount++;

			for($n=0;$n<count($outputdata);$n++)
			{
				fputs($block,$outputdata[$n]."\n");#writes to the file 
			}
			fclose($block);#closes file
		}
		else
		{
			exit -1;
		}
	}
	$outputdata=array();#assigns empty array to outputdata, as all data should have been output and written to file
}

// Packet State Machine - States

define("P_INIT",0);
define("P_ODD",1);
define("P_EVEN",3);
define("P_ODD_BADEND",2);
define("P_EVEN_BADEND",4);
define("P_BAD",5);
define("P_ODD_BADSRT",6);
define("P_EVEN_BADSRT",7);
define("P_ERR",8);

// Packet State Machine - Inputs

define("ODD", 0);
define("EVEN",1);
define("BOTH",2);
define("NONE",3);

// Sequence State Machine - Outputs

define(  "NUL",       0x00);#0b00000000
define("O_USE",       0x01);#0b00000001
define("O_START",     0x02);#0b00000010
define("O_ODD",       0x04);#0b00000100
define("O_EVEN",      0x08);#0b00001000
define("O_MISSING",   0x10);#0b00010000
define("O_PARTIAL",   0x20);#0b00100000
define("O_EARLYWRITE",0x40);#0b01000000
define("O_LATEWRITE", 0x80);#0b10000000

// Sequence State Machine - States

//      NUL  ,0					#'normal'
define("DBLE",1); 				#single missing packet (not 'bad' as such)
define("BAD" ,2);				#ext mode rest count changed by weird number, or something else odd occurred

define("S_IDLE",0);
define("S_ODD",1);
define("S_EVEN",2);

#$new[$state from previous run][$in (0,1,2, missing/bad packet)][$retstate - output from packet_analyse, 9 options]
#ie. takes previous state, quality of packet and packet_analyse output as inputs, and outputs the new state.

$new[S_IDLE][NUL]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_IDLE][DBLE]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE, #can DBLE and P_ODD (or P_EVEN, etc...) occur simultaneously?
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_IDLE][BAD]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_ODD][NUL]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_ODD][DBLE]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_IDLE,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);
							#same difference as for S_EVEN DBLE, just for ODD
							
$new[S_ODD][BAD]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_EVEN][NUL]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);

$new[S_EVEN][DBLE]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_IDLE,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);
							#why the distinction here, and what makes P_ODD different from P_EVEN - becaues previous $state was S_EVEN!!
							#so after skipping a packet, the packet should also be even. If it is odd, then something has gone wrong -> IDLE

$new[S_EVEN][BAD]=	array(	P_INIT=>	S_IDLE,	P_BAD=>			S_IDLE,	P_ERR=>			S_IDLE,
							P_ODD=>		S_ODD,	P_ODD_BADEND=>	S_IDLE,	P_ODD_BADSRT=>	S_ODD,
							P_EVEN=>	S_EVEN,	P_EVEN_BADEND=>	S_IDLE,	P_EVEN_BADSRT=>	S_EVEN);


	// Sequence - Output table
	#IDLE - INIT
	#$out[previous state][in - 0/1/2][$retstate -  - output from packet_analyse, 9 options]
	$out[S_IDLE][0]=	array(	P_INIT=>			NUL,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE,
								P_ODD_BADEND=>		NUL,
								P_EVEN=>				O_EVEN |                         O_START | O_USE,
								P_EVEN_BADEND=>		NUL,
								P_BAD=>				NUL,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE,
								P_ERR=>				NUL);
								
	$out[S_IDLE][DBLE]=	array(	P_INIT=>			NUL,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE,
								P_ODD_BADEND=>		NUL,
								P_EVEN=>				O_EVEN |                         O_START | O_USE,
								P_EVEN_BADEND=>		NUL,
								P_BAD=>				NUL,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE,
								P_ERR=>				NUL);
								
	$out[S_IDLE][BAD]=	array(	P_INIT=>			NUL,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE,
								P_ODD_BADEND=>		NUL,
								P_EVEN=>				O_EVEN |                         O_START | O_USE,
								P_EVEN_BADEND=>		NUL,
								P_BAD=>				NUL,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE,
								P_ERR=>				NUL);

	$out[S_ODD][0]=		array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE | O_EARLYWRITE,
								P_ODD_BADEND=>		                                                       O_EARLYWRITE,
								P_EVEN=>				O_EVEN |                                   O_USE,
								P_EVEN_BADEND=>			O_EVEN |             O_PARTIAL |           O_USE |                O_LATEWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);
								
	$out[S_ODD][DBLE]=	array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>					O_ODD  | O_MISSING |                       O_USE,
								P_ODD_BADEND=>			O_ODD  | O_MISSING | O_PARTIAL |           O_USE |                O_LATEWRITE,
								P_EVEN=>			                                                       O_EARLYWRITE,
								P_EVEN_BADEND=>		                                                       O_EARLYWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);
								
	$out[S_ODD][BAD]=	array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE | O_EARLYWRITE,
								P_ODD_BADEND=>		                                                       O_EARLYWRITE,
								P_EVEN=>				O_EVEN |                         O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADEND=>		                                                       O_EARLYWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);

	$out[S_EVEN][0]=	array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>				    O_ODD  |                                   O_USE,
								P_ODD_BADEND=>			O_ODD  |             O_PARTIAL |           O_USE |                O_LATEWRITE,
								P_EVEN=>				O_EVEN |                         O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADEND=>		                                                       O_EARLYWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);
								
	$out[S_EVEN][DBLE]=	array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>				                                                       O_EARLYWRITE,
								P_ODD_BADEND=>		                                                       O_EARLYWRITE,
								P_EVEN=>				O_EVEN | O_MISSING |                       O_USE,
								P_EVEN_BADEND=>			O_EVEN | O_MISSING | O_PARTIAL |           O_USE |                O_LATEWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);
								
	$out[S_EVEN][BAD]=	array(	P_INIT=>			                                                       O_EARLYWRITE,
								P_ODD=>					O_ODD  | O_MISSING |             O_START | O_USE | O_EARLYWRITE,
								P_ODD_BADEND=>		                                                       O_EARLYWRITE,
								P_EVEN=>				O_EVEN |                         O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADEND=>		                                                       O_EARLYWRITE,
								P_BAD=>				                                                       O_EARLYWRITE,
								P_ODD_BADSRT=>			O_ODD  |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_EVEN_BADSRT=>			O_EVEN |             O_PARTIAL | O_START | O_USE | O_EARLYWRITE,
								P_ERR=>				                                                       O_EARLYWRITE);

function packet_analyse($bytes,&$state,&$startreset,&$stopreset)
{
	// A function which analyses the data in array $bytes.
	// $bytes = payload alone, neither the DDS or Instrument Headers are present.
	// This array contains a total of 3562 bytes, Up to 444½ vectors can be present
	// within this, an 'even' packet has the ½ vector at the end, an 'odd' packet has
	// the ½ vector at the start.
	
	// Byte		0		1		2		3		4		5		6MSN	6LSN	7       #every vector is 8 bytes long - 1/2 vector is thus 4 bytes long
	// 															Range	Reset	Reset
	//																	MSB		LSB

	// The state machine transition $table within this function, ie for analysing the internals
	// of the packet alone.
    /** R represents an error - NONE (3), OE is both ODD and EVEN - BOTH (2)*/
	
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
	#related to the diagram
	
	$table[P_INIT       ][ODD]=P_ODD;        $table[P_INIT       ][EVEN]=P_EVEN;        $table[P_INIT       ][BOTH]=P_INIT;        $table[P_INIT       ][NONE]=P_BAD;
	$table[P_ODD        ][ODD]=P_ODD;        $table[P_ODD        ][EVEN]=P_ERR;         $table[P_ODD        ][BOTH]=P_ODD;         $table[P_ODD        ][NONE]=P_ODD_BADEND;
	$table[P_ODD_BADEND ][ODD]=P_ERR;        $table[P_ODD_BADEND ][EVEN]=P_ERR;         $table[P_ODD_BADEND ][BOTH]=P_ERR;         $table[P_ODD_BADEND ][NONE]=P_ODD_BADEND;
	$table[P_EVEN       ][ODD]=P_ERR;        $table[P_EVEN       ][EVEN]=P_EVEN;        $table[P_EVEN       ][BOTH]=P_EVEN;        $table[P_EVEN       ][NONE]=P_EVEN_BADEND;
	$table[P_EVEN_BADEND][ODD]=P_ERR;        $table[P_EVEN_BADEND][EVEN]=P_ERR;         $table[P_EVEN_BADEND][BOTH]=P_ERR;         $table[P_EVEN_BADEND][NONE]=P_EVEN_BADEND;
	$table[P_BAD        ][ODD]=P_ODD_BADSRT; $table[P_BAD        ][EVEN]=P_EVEN_BADSRT; $table[P_BAD        ][BOTH]=P_BAD;         $table[P_BAD        ][NONE]=P_BAD;
	$table[P_ODD_BADSRT ][ODD]=P_ODD_BADSRT; $table[P_ODD_BADSRT ][EVEN]=P_ERR;         $table[P_ODD_BADSRT ][BOTH]=P_ODD_BADSRT;  $table[P_ODD_BADSRT ][NONE]=P_ERR;
	$table[P_EVEN_BADSRT][ODD]=P_ERR;        $table[P_EVEN_BADSRT][EVEN]=P_EVEN_BADSRT; $table[P_EVEN_BADSRT][BOTH]=P_EVEN_BADSRT; $table[P_EVEN_BADSRT][NONE]=P_ERR;
	$table[P_ERR        ][ODD]=P_ERR;        $table[P_ERR        ][EVEN]=P_ERR;         $table[P_ERR        ][BOTH]=P_ERR;         $table[P_ERR        ][NONE]=P_ERR;


	$counteven=0;    // Number of even vectors
	$countodd=0;     // Number of odd vectors
	$state=P_INIT;   // Initial State of State Machine

	// Set these reset values on the various first possible even and odd vectors
	// Even vectors are at 0+n*8, Odd vectors are at 4+n*8 #since odd packet has 1/2 vector at start, thus offset by 4
	#1/2 vector is skipped in this code section
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
	#ie values at $n=0, loop below starts at $n=1 and compares n=1 values with the following n=0 values for validity
	$prevreseteven=($bytes[6]&15)*256+$bytes[7];#extracts lower nibble of 6th byte, combines with 7th byte to form reset count 
												#(nibble in 6th byte is MSB, thus *256)
	$prevresetodd=($bytes[10]&15)*256+$bytes[11];#same as above, but offset by 4 due to 1/2 vector at start
	#extracts sensor ID (0/1) from first vecotr (ignoring 1/2 vector)
	$firstsensoreven=$bytes[6]>>7;
	$firstsensorodd=$bytes[10]>>7;
	
	// Loop around the 444 entire vectors (there are 444.5, but we'll ignore the half vector here)
	
	for($n=1;$n<444;$n++)
	{
		$rangeeven= ($bytes[$n*8+ 6]>>4)&0x07;                 // This is the Range, if the packet is even #0x07 = 7 = 0b0111 - only extracts the 3 range bits
		$reseteven= ($bytes[$n*8+ 6]&15)*256+$bytes[$n*8+ 7];  // This is the Reset Count, if the packet is even #15 = 0b1111
		$sensoreven= $bytes[$n*8+ 6]>>7;
		
		$rangeodd=  ($bytes[$n*8+10]>>4)&0x07;                 // This is the Range, if the packet is odd
		$resetodd=  ($bytes[$n*8+10]&15)*256+$bytes[$n*8+11];  // This is the Reset Count, if the packet is odd
		$sensorodd=  $bytes[$n*8+10]>>7;

		// Unused vector areas can be set to AAAA5555AAAA5555 or 5555AAAA5555AAAA, which should be ignored
		#used to identify unused vector areas ie. if(!$invalid) then data is good 
		$invalid=(($bytes[$n+8  ]==0x55) && ($bytes[$n*8+1]==0x55) && ($bytes[$n*8+2]==0xAA) && ($bytes[$n*8+3]==0xAA)
		       && ($bytes[$n*8+4]==0x55) && ($bytes[$n*8+5]==0x55) && ($bytes[$n*8+6]==0xAA) && ($bytes[$n*8+7]==0xAA)) ||
		         (($bytes[$n+8  ]==0xAA) && ($bytes[$n*8+1]==0xAA) && ($bytes[$n*8+2]==0x55) && ($bytes[$n*8+3]==0x55)
		       && ($bytes[$n*8+4]==0xAA) && ($bytes[$n*8+5]==0xAA) && ($bytes[$n*8+6]==0x55) && ($bytes[$n*8+7]==0x55));
		
		#checks if range is valid, if reset count advanced by 4096 OR 4097, sensor value stayed constant and if data is not invalid
		if (($rangeeven>=2) && ((($reseteven-$prevreseteven+4096)%4096)<=1) && $sensoreven==$firstsensoreven && !$invalid)
		{
			$counteven++;
			$iseven=1;
			if (!isset($startreseteven))#first time $startreseteven is defined, but only if not set before
										#ie. it remains the same throughout, but $stopreseteven changes, 
										#$startreseteven set to n=1 vector, not n=0 vector!
				$startreseteven=$reseteven;
			$stopreseteven=$reseteven;
		}
		else
			$iseven=0;

		if (($rangeodd>=2) && ((($resetodd-$prevresetodd+4096)%4096)<=1) && $sensorodd==$firstsensorodd && !$invalid)
		{
			$countodd++;
			$isodd=1;
			if (!isset($startresetodd))
				$startresetodd=$resetodd;
			$stopresetodd=$resetodd;
		}
		else
			$isodd=0;

		if ($isodd && !$iseven)#if vector is odd
			$state=$table[$state][ODD];#advance to next state given state transition table (initial state P_INIT)
		elseif ($iseven && !$isodd)
			$state=$table[$state][EVEN];
		elseif ($iseven && $isodd)
			$state=$table[$state][BOTH];
		else		#eg. if vector is invalid
			$state=$table[$state][NONE];

		#vectors could be both, but how do these assignments make subsequent detection of opposite state possible? - 
		#ie. how is line (511) possible? (elseif ($iseven && $isodd))
		#eg. even -> odd, or odd -> even, since condition ((($resetodd-$prevresetodd+4096)%4096)<=1) has to be fulfilled 
		#assignments are of course necessary to continually detect 1 state, eg. even, even, even, etc...
		$prevreseteven=$reseteven;
		$prevresetodd=$resetodd;
	}

	// Set and return values, depending on whether this is (apparently) an Odd or Even packet
	
	if (($state==P_EVEN) || ($state==P_EVEN_BADSRT) || ($state==P_EVEN_BADEND))
	{
		$startreset=$startreseteven;
		$stopreset =$stopreseteven;
		return $counteven;
	}
	if (($state==P_ODD) || ($state==P_ODD_BADSRT) || ($state==P_ODD_BADEND))
	{
		$startreset=$startresetodd;
		$stopreset =$stopresetodd;
		return $countodd;
	}
	else
	{
		$startreset=-1;
		$stopreset=-1;
		return 0;
	}
}


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


// Program start

$outputdata=array();

set_time_limit(600);									#Sets maximum execution time limit

// define("EXT",'/cluster/data/extended/');
define("EXT",'/home/ahk114/extended/'); 				#writing the meta files to my own home directory on the server
define("RAW",'/cluster/data/raw/');

//Acquiring the selection info from the command line input now, not from the URL!

$day = null;
$month = null;
$year = null;
$sc = null;
$version = null;

$shortopts  = "d:";
$shortopts .= "m:";
$shortopts .= "y:";
$shortopts .= "sc:";
#$shortopts .= "ver:"; #select version automatically

$options = getopt($shortopts);
#var_dump($options);

if (array_key_exists("y",$options)){$year  = $options["y"];}
else {exit("Please select a Year!".PHP_EOL);}
if (array_key_exists("m",$options)){$month = $options["m"];}
else {exit("Please select a Month!".PHP_EOL);}
if (array_key_exists("d",$options)){$day   = $options["d"];}
else {exit("Please select a Day!".PHP_EOL);}

#verification of input parameters, php automatically converts between string and int
if (array_key_exists("sc",$options))
{
	if ($sc > 4 || $sc < 1)
	{
		exit("Invalid Spacecraft!".PHP_EOL);
	}
	else {$sc = sprintf('%1d',$options["sc"]);}
}
else
{
	echo "Setting default value for Spacecraft: Rumba (1)".PHP_EOL;
	$sc = 1;
}
/*
if (array_key_exists("ver",$options))
{
	if (strtoupper($version) != 'A' || strtoupper($version) != 'B' || strtoupper($version) != 'K')
	{
		exit("Invalid Version!".PHP_EOL);
	}
	else {$version = $option["ver"];}
}
else
{
	echo "Setting default value for Version: B".PHP_EOL;
	$version = 'B';
}
*/
if ($month > 12 || $month < 1)
{
	exit("Invalid Month!".PHP_EOL);
}
#possible issue with date()
if ($year < 2000)
{
	$year += 2000;
}
if ($year > date("Y") || $year < 2000)
{
	exit("Invalid Year!".PHP_EOL);
}
#beware of lacking support for calendars, but seems to be working (24/06/2016)
if ($options["d"] > cal_days_in_month(CAL_GREGORIAN,$month,$year) || $options["d"] < 1)
{
	exit("Number of days is invalid!".PHP_EOL);
}

$jdcount = gregoriantojd($month, $day, $year);
$month_name = jdmonthname($jdcount,0);

$shortyear=sprintf("%02d",$year-2000);			
$month=sprintf("%02d",$month);
$day=sprintf("%02d",$day);

/*Selecting version based on selected date and the available burst science data */
$target_dir = RAW.$year.'/'.sprintf('%02d',$month).'/';
$files = scandir($target_dir);
$needle_base = 'C'.$sc.'_'.$shortyear.$month.$day.'_';	#eg. 'C1_160101_A.BS'

$versions = array('K','B','A');							#due to break statement - give precendence in this order, ie. K is most important
foreach ($versions as $version)
{
	$needle_tip = $version.'.BS';
	if (array_search($needle_base.$needle_tip,$files))
	{
		break;
	}
	else
	{
		if ($version == 'A')
		{
			exit("No valid Version (A,B or K) for Burst Science Data found!");
		}
	}
} 

echo "Year:       ".$year.PHP_EOL;
echo "Month:      ".$month_name.PHP_EOL;
echo "Day:        ".$day.PHP_EOL;
echo "Spacecraft: ".$sc.PHP_EOL;
echo "Version:    ".$version.PHP_EOL;

$base="C".$sc."_".$shortyear.$month.$day."_".$version;
$datafilename=RAW.$year."/".$month."/".$base.".BS";		#burst science (BS) raw data file

$metafilename=EXT.$year.'/'.$month.'/'.$base.".META";								

echo "Reading Data from: ".$datafilename.PHP_EOL;
echo "Meta-filename:     ".$metafilename.PHP_EOL;
echo "Writing to:        ".EXT.$year."/".$month."/".$base.'.E'.'n'.'    (n is the block number)'.PHP_EOL;

fwrite(STDOUT,"target".EXT.$year."/".$month."/".$base);			#write filename base to stdout, for input into stage2 processing!

if (!is_dir(EXT.$year))									#make directory named with date if non-existent. (Failing here 24-06-15)
	mkdir(EXT.$year,0750);

if (!is_dir(EXT.$year.'/'.$month))
	mkdir(EXT.$year.'/'.$month,0750);					#(again failing here 24-06-15)

write_meta($metafilename,"SourceFile",$datafilename);					#since 4th field is missing, written to "GLOBAL" section 
write_meta($metafilename,"ProcessingTime_ISO",date("Y-m-d\TH:i:s\Z"));  #at top of META file

$handle=fopen($datafilename,"r");						#open file for reading data ONLY, starting from the beginning

$fsize=filesize($datafilename);							#size of file in bytes

$extblockcount=0;
$etime=0;

$previousreset=999999;
$previousextreset=999999;
$packetcount=0;
$lastextreset=999999;									#WHAT ARE THESE RESET COUNTS?
$firstreset=999999;
$lastzero=999999;
$state=0;

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
// Bytes 15 (15 Bytes)

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
$s=NULL;
$e=NULL;
$size=NULL;

while (ftell($handle)!=$fsize)						#ftell is the current position in open data file. while command iterates through (until EOF)
{
	// Get the SCET data from the DDS header
	for($n=0;$n<15;$n++)
		$header[$n]=fgetb($handle);

	$headlen=$header[9]*65536+$header[10]*256+$header[11];  #extracts length (2^16=65536)
	$headsc=$header[12]>>4;								    #spacecraft

	// Packet Header

	$packetcount++;

	// SCET is Bytes 0-1 : Days from 1st Jan 1958
	//         Bytes 2-5 : Milliseconds in Day
	//         Bytes 6-7 : Microseconds in Milliseconds

	$scetday=$header[0]*256+$header[1];
	$scetms=$header[2]*16777216+$header[3]*65536+$header[4]*256+$header[5];
	$scetus=$header[6]*256+$header[7];

	$dtc=mktime(0,0,$scetms/1000,1,1+$scetday,1958);  // Convert SCET days into Unix Seconds from 1st Jan 1970

	$date=date("Y-m-d\TH:i:s",$dtc);  // Convert that value into ISO date and time (without the decimal bit or 'Z')

	#extracts 15 bytes from the Science Telemetry Header (every fgetb advances by 1 byte)
	$telemstatus=fgetb($handle)*256+fgetb($handle);     // Used to determine whether we're in Extended Mode
	$telemhfreset=fgetb($handle)*256+fgetb($handle);	// Not currently used
	$telemhflastsun=fgetb($handle)*256+fgetb($handle);	// Used to determin deltahfsun (which is then not used)
	$telemhfthissun=fgetb($handle)*256+fgetb($handle);	// Used to determin deltahfsun (which is then not used)
	$telemhf1ry=fgetb($handle)*256+fgetb($handle);		// Not currently used
	$telemhf2ry=fgetb($handle)*256+fgetb($handle);		// Not currently used
	$telemreset=fgetb($handle)*256+fgetb($handle);		// The reset counter value of the *packet*
	$telemmode=fgetb($handle);							// The Telemetry Mode

	// Ignore Varianace
	fseek($handle,19,SEEK_CUR);									#ignore bytes 16-33 of the science header
																#skips straight to first byte of primary science data

	$deltahfsun=$telemhfthissun-$telemhflastsun;
	if ($deltahfsun<0)
		$deltahfsun+=65536;										#overflow of 16 bit counter

	if (($telemstatus&0x0F)==15)#get last 4 bits!
	{
		$msa=array_slice(unpack("C*",fread($handle,3562)),0);	#C-unsigned char, * is repeater argument, repeat to end of data

		$size=packet_analyse($msa,$retstate,$s,$e);				#EVEN/ODD count returned by packet_analyse function or 0 upon error
																#$retstate,$s(startreset),$e(stopreset) changed within packet_analyse
																
		// Information: IN EXTENDED MODE - TM Mode (EXT), the value returned by the packet analysis
		// State Machine, the number of vectors in the packet (not including the first vector, or the
		// half vector ie a maximum of 443), the first and last extended mode reset counts (ie those
		// recorded into the MSA when the data was collected), but *only* the top 12 most significant
		// bits.
		// (The "& 0xFFF" clips -1 values to 0xFFF). 	#what does this mean??? 0xFFF = 4095 = 0b00000011 1111111111 -shouldn't this be the other way around?
		
// WORKS !!!! If Missing packet, ie Pack Reset +2, then DONT check Vector Reset,
// becase it *WILL* be wrong as well (doh!)

		if ( ($previousreset==999999) ||				// If this is the first time 
		     (($telemreset-$previousreset)==1) ||		// or the packet has gone up by one
		     (($previousreset-$telemreset)==65535) )	// or a rollover.
			{											#reset count of ext mode vectors ($s, $e, $previousextreset) will go up by 0/1 (%4096)
			if ( ($previousextreset==999999) ||			// ... and this is the first extended mode 
			     ((($s-$previousextreset)==0) ||		// or extended mode has gone up by zero #$s is new startreset
			     (($s-$previousextreset)==1)) ||		// or one
			     (($previousextreset-$e)==4095) )		// or a rollover
				{
					$badpacket=0;							// So, this isn't a bad or a double bad, the reset count
					$double=0;								// went up by one, and the ext mode reset count by 1 or 0.
				}
			else
				{
					$badpacket=1;							// Uhoh, the ext mode reset count changed by some odd number,
					$double=0;								// so mark things as bad.
				}
			}
		elseif ( (($telemreset-$previousreset)==2) ||	// OK, did the packet reset count go up by two?
		         (($previousreset-$telemreset)==65534) )// rollover, also up by 2
		{
			$badpacket=0;								// Yes, so we have a single missing packet, not 'bad' as such.
			$double=1;
		}
		else
		{
			$badpacket=1;								// No, so stuff is just messed up, mark as bad.
			$double=0;
		}

		$previousextreset=$e;	#$e is stop reset		// Now set these previous values, so next time around, we
		$previousreset=$telemreset;						// have something to check against
	}
	else												// This isn't an extended mode packet, so it's clearly
	{													// bad
		// Jump over the remainder of the packet, we don't care what is in it.
		fseek($handle,$headlen-34,SEEK_CUR);
		$badpacket=1;									// This is a bad packet #triggers EW if previous state NOT S_IDLE (ie. previous packet is 'known')
		$double=0;										// We didn't simply miss a packet
		$retstate=0;									// Lets set the state (used as input to the next stage) token_name
	}													// zero, the initial state, which is where it sits if the system is unsure

	$in=$double+2*$badpacket;							// Form Double and Bad into one convenient value

	$output=$out[$state][$in][$retstate];				// $output is what we do at this point
	/*$retstate could be 
	P_INIT
	P_ERR  
	*P_ODD
	*P_ODD_BADEND 
	*P_ODD_BADSRT
	*P_EVEN
	*P_EVEN_BADEND 
	*P_EVEN_BADSRT
	*P_BAD 
	without * -> $startreset($s), $stopreset($e) set to -1
	$in could be 0,1,2 depending on missing packet, bad packet, etc...
	$state is defined below, and remains as such until redefined the next time around. -> ie. $state is from the previous packet!
	*/
	$state=$new[$state][$in][$retstate];				// $state is the new state (basically either Bad, Odd or Even)

//	$disp_stuff=disp($output); // Need to do this here (rather than in the printf) so $ispartial gets set for the next bit

	$use=       ($output & 1)!=0;
	$isstart=   ($output & 2)!=0;
	$isodd=     ($output & 4)!=0;
	$iseven=    ($output & 8)!=0;
	$ismissing= ($output & 16)!=0;
	$ispartial= ($output & 32)!=0;
	$writeearly=($output & 64)!=0;
	$writelate= ($output & 128)!=0;
	
	// Spin is roughly between 3.9 and 4.4 seconds, so 444 spins will take between 1731 seconds and
	// 1954 seconds.  With resets at around 5.152 seconds, it will increment betweem 336 and 379 times,
	// but we only see the top 12 bits, so divide this by 16 to get a range or 21 to 24.
	// (That's all a bit rough and ready, but you get the idea).
	// If we're outside that range (and ignoring the zero values), display this hexadecimal difference
	// value in Red.
	
	if (($s!=-1) && ($e!=-1))
	{
		$delta=(($e-$s)+0xFFF)%0xFFF;
	}
	else
	{
		$delta=-1;
	}

	// Information: If the delta value is sensible, then display it.  If it's outside of 
	// a reasonable range (as above) then put it in red.
	
	if ($ispartial)
	{
	}
	else
	{
		if ($delta==-1)
		{
		}
		else if ($delta!=0)
		{
			if (($delta>24) || ($delta<21))
			{
				// Also record that this has occured.  I'm not sure that this is a sensible
				// descriptor BadSpinCount ?
				inc_meta($metafilename,"BadSunPacketCount",$extblockcount);
			}
			else
			{
			}
		}
		else
		{
		}
	}

	// If we have some output data, then display how many values there are
	
	if (count($outputdata)!=0)
	{
	}
		
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


	if ($writeearly)
	{
		WriteEntireBlock();
	}

	if ($isstart)  // OK, this is the start of an Extended Mode block
	{
		$missing=0;							// Set the number of missing blocks to zero
		$startsection=$s;					// Set the start of this section, in ext reset counter terms
		$extdtc=$dtc;						// Record the packet SCET (in Unix terms)
		if ($ispartial)						// If this is a partial packet, tag it
			$partialstart=TRUE;
		else
			unset($partialstart);
			
		// Reset the BadSunPacketCount and MissingPacket values
		write_meta($metafilename,"BadSunPacketCount",0,$extblockcount);
		write_meta($metafilename,'MissingPacket',0,$extblockcount);
	}

	if ($ismissing)		// If the packet is missing, we write out some blank vectors, to fill the gap.
						// We increment the record of how many packets are missing.
	{
	write_meta($metafilename,'MissingPacket'.$missing++."_FollowingResetCount",$s,$extblockcount);
		if ($isodd)
			{
				// OK, this packet is odd, so missing packet was even, and we don't have the half a vector
				for($n=0;$n<445;$n++) // <<-- Is this correct?
					output(0,0,0,0,"0000 MISSING EVEN ".$n);
				inc_meta($metafilename,'MissingPacket',$extblockcount);

			}
		elseif ($iseven)
			{
				// OK, this packet is even, so missing packet was odd, throw away the half a vector.
				for($n=0;$n<446;$n++) // <<-- Is this correct?
					output(0,0,0,0,"0000 MISSING ODD ".$n);
				inc_meta($metafilename,'MissingPacket',$extblockcount);
			}
	}

	if ($use)				// We should use this packet, it's good.
	{
		if ($ispartial)		// We've only got part of a packet
		{
			if ($isstart)	// Partial at Start, so data is at the end of the packet
			{
				if ($isodd)
				{
					for($n=0;$n<($size+1);$n++)
					{
						$pos=8*(443-$size+$n)+4;
						convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
						        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
						        "PARTIAL START ODD ".$n);
					}
				}
				elseif ($iseven)
				{
					for($n=0;$n<($size+1);$n++)
					{
						$pos=8*(443-$size+$n);
						convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
						        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
						        "PARTIAL START EVEN ".$n);

					}
					for($n=0;$n<4;$n++)
						$halfvector[$n]=$msa[8*444+$n];
				}
			}
			else // Must be at the end, so data is at the start of the packet
			{
				if ($isodd)
				{
					if ($ismissing)
						output(0,0,0,0,"0000 PARTIAL END ODD, FILL MISSING HALF VECTOR");
					else
						convert($halfvector[0],$halfvector[1],$halfvector[2],$halfvector[3],
						        $msa[0],$msa[1],$msa[2],$msa[3],
						        "PARTIAL END ODD, COMPLETE HALF VECTOR");

					for($n=0;$n<($size+1);$n++) // NB Max Size from proc is 443 vectors
					{
						$pos=8*$n+4;
						convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
						        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
						        "PARTIAL END ODD ".($n+1));
					}
				}
				elseif ($iseven)
				{
					for($n=0;$n<($size+1);$n++)
					{
						$pos=8*$n;
						convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
						        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
						        "PARTIAL END EVEN ".$n);
					}
				}
			}
		}
		else // Must be a whole packet
		{
			if ($isodd)
			{
				// If the previous vector was missing, then we have to "invent" a blank
				// vector, since the remainder isn't useful.
				// Otherwise, just use the half vector from the last even packet, and combine
				// it to generate the entire vector from two halves.
				// Then output the remaining 444 vectors.
			
				if ($ismissing)
					output(0,0,0,0,"0000 WHOLE ODD, FILL MISSING HALF VECTOR");
				else
					convert($halfvector[0],$halfvector[1],$halfvector[2],$halfvector[3],
					        $msa[0],$msa[1],$msa[2],$msa[3],
					        "WHOLE ODD, COMPLETE HALF VECTOR");
				for($n=0;$n<444;$n++)
				{
					$pos=8*$n+4;
					convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
					        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
					        "WHOLE ODD ".($n+1));
				}
			}
			elseif ($iseven)		// For an Even vector, write out the 444 vectors, and then
									// record the details of the half of a vector.
			{
				for($n=0;$n<444;$n++)
				{
					$pos=8*$n;
					convert($msa[$pos],$msa[$pos+1],$msa[$pos+2],$msa[$pos+3],
					        $msa[$pos+4],$msa[$pos+5],$msa[$pos+6],$msa[$pos+7],
					        "WHOLE EVEN ".$n);
				}
				for($n=0;$n<4;$n++)
					$halfvector[$n]=$msa[8*444+$n];
			}
		}
		$lastgoodendreset=$e;
	}  // End of ($use)

	if ($writelate)
	{
		WriteEntireBlock();
	}
}

// If we get to the end, and we *still* have some data in $output data, we need to write this
// out, otherwise we lose it.  This code should be identical to the EarlyWrite code.

if (count($outputdata)!=0)
{
	WriteEntireBlock();
}

write_meta($metafilename,"NumberOfBlocks",$extblockcount);


session_destroy();
?>
