<?php
#, /* */AKR comments

/*
Delete the following line for deployment or figure out why permission to normal session folder are denied
*/
session_destroy();
require 'meta_file_functions.php';

define("RAW","/cluster/data/raw/");
define("EXT",'/home/ahk114/extended/');

#filepicked in my case, /home/ahk114/extended/2016/01/C1_160101_B.E0
function getcalfile($filepicked)
{
	$block = substr($filepicked,strlen($filepicked)-1,1);
	$sc=substr(basename($filepicked),1,1);
	$meta_file = substr($filepicked,0,strlen($filepicked)-2).'META';
	echo "Meta File:".$meta_file.PHP_EOL;
	if (!(file_exists($meta_file))){exit("getcalfile, meta file not found!");}
	if (!(filesize($meta_file))){exit("getcafile, Meta file empty!");}
	$extmodeentry_unix = read_meta($meta_file,"ExtendedModeEntry_Unix",$block);
	$version_list = array('B','K','A');
	$found = FALSE;
	foreach ($version_list as $ver)
	{
		$steffile = RAW.date('Y',$extmodeentry_unix).'/'.date('m',$extmodeentry_unix).'/'.'C'.$sc.'_'.date('ymd',$extmodeentry_unix).'_'.$ver.'.STEF';	
		if (file_exists($steffile) && filesize($steffile))
		{
			$found = TRUE;
			break;
		}
		else
		{
			echo "getcalfile, empty stef file version ".$ver.PHP_EOL;
		}
	}
	if (!($found))
	{
		#do something here - look for other file or abort?
		#maybe ask Peter about this from a scientific standpoint
	}
	echo "getcalfile, using:".$steffile.PHP_EOL;
	$steffilecontents = file_get_contents($steffile);
	$searchstringpos = strpos($steffilecontents, "START REVOLUTION");
	echo "Position:".$searchstringpos.PHP_EOL;
	if (!$searchstringpos)
	{
		echo "No match found, trying earlier file".PHP_EOL;
		#need to implement this!!!
	}
	$sample_output = substr($steffilecontents,$searchstringpos-100,400);
	echo "Sample".PHP_EOL;
	echo $sample_output.PHP_EOL;
	echo "123456789012345678901234567890123456789012345678901234567890".PHP_EOL;
}
/* Testing */
$filepicked = "/home/ahk114/extended/2016/01/C1_160106_B.E0";
getcalfile($filepicked);

?>