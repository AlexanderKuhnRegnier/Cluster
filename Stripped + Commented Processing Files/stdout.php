<?php
/*
Delete the following 3 lines, AND LAST LINE for deployment, or figure out why permission to normal session folder are denied
*/
session_destroy();
ini_set('session.save_path','/home/ahk114'. '/testing/'. 'session/'); 
session_start();

// Program start

set_time_limit(600);									#Sets maximum execution time limit

// define("EXT",'/cluster/data/extended/');
define("EXT",'/home/ahk114/extended/'); 				#writing the meta files to my own home directory on the server
define("RAW",'/cluster/data/raw/');

//Acquiring the selection info from the command line input now, not from the URL!

$day = 1;
$month = 1;
$year = 2016;
$sc = 1;
$version = 'B';

$jdcount = gregoriantojd($month, $day, $year);
$month_name = jdmonthname($jdcount,0);

$shortyear=sprintf("%02d",$year-2000);			
$month=sprintf("%02d",$month);
$day=sprintf("%02d",$day);

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

session_destroy();
?>
