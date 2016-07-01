<?php

// function read_meta($filename,$variablename,$section="")
// function write_meta($filename,$variablename,$variablevalue,$section="")
// function inc_meta($filename,$variablename,$section="",$amount=1)
// function import_meta($filename)
// function export_meta($filename)
// function exists_meta_section($filename,$section)

function _sort($a,$b)
{
	if ((gettype($a)!="integer") and (gettype($b)=="integer"))
		return -1;
	else if ((gettype($a)=="integer") and (gettype($b)!="integer"))
		return +1;
	else
	{
		if ($a>$b)
			return +1;
		else if ($a<$b)
			return -1;
		else
		return 0;
	}
}

function exists_meta_section($filename,$section)
{
	global $meta_file_contents,$meta_file_changed,$meta_file_name;

	if (isset($meta_file_contents) and isset($meta_file_name) and $meta_file_name==$filename)
	{
		if (is_array($meta_file_contents[$section]))
			return TRUE;
		else
			return FALSE;
	}
	else
	{
		if (file_exists($filename))
		{
			if ($file_h=fopen($filename,"rb"))
			{
				$currentsection="";
				while (!feof($file_h))
				{
					$line=trim(fgets($file_h,255));
					if ($line!="")
					{
						if ((substr($line,0,1)=="[") && (substr($line,-1)=="]"))
						{
							$currentsection=trim(substr($line,1,-1));
						}
						else
						{
							$elements=explode("=",$line);
							$contents[$currentsection][trim($elements[0])]=trim($elements[1]);
						}
					}
				}
				if (is_array($contents[$section]))
					return TRUE;
				else
					return FALSE;
			}
			else
			{
				exit("Can't open file ".$filename." in read_meta.");
			}
		}
		else
		{
			exit("File ".$filename." in read_meta doesn't exist.");
		}
	}
}

// ================================================================================

function read_meta($filename,$variablename,$section="Global")
{
	global $meta_file_contents,$meta_file_changed,$meta_file_name;
	
	if (isset($meta_file_contents) and isset($meta_file_name) and $meta_file_name==$filename)
	{
		if (isset($meta_file_contents[$section][$variablename]))
				return $meta_file_contents[$section][$variablename];
			else
				return "";
	}
	else
	{

		if (file_exists($filename))
		{
			if ($file_h=fopen($filename,"rb"))
			{
				$currentsection="";
				while (!feof($file_h))
				{
					$line=trim(fgets($file_h,255));
					if ($line!="")
					{
						if ((substr($line,0,1)=="[") && (substr($line,-1)=="]"))
						{
							$currentsection=trim(substr($line,1,-1));
						}
						else
						{
							$elements=explode("=",$line);
							$contents[$currentsection][trim($elements[0])]=trim($elements[1]);
						}
					}
				}
				if (isset($contents[$section][$variablename]))
					return $contents[$section][$variablename];
				else
					return "";
			}
			else
			{
				exit("Can't open file ".$filename." in read_meta.");
			}
		}
		else
		{
			exit("File ".$filename." in read_meta doesn't exist.");
		}
	}
	return "";
}

// ================================================================================

function write_meta($filename,$variablename,$variablevalue,$section="Global")
{
	global $meta_file_contents,$meta_file_changed,$meta_file_name;
	
	if (isset($meta_file_contents) and isset($meta_file_name) and $meta_file_name==$filename)
	{
		$meta_file_contents[$section][$variablename]=$variablevalue;
		$meta_file_changed=TRUE;
	}
	else
	{
		if (file_exists($filename))
		{
			if ($file_h=fopen($filename,"rb"))
			{
				$currentsection="";
				while (!feof($file_h))
				{
					$line=trim(fgets($file_h,255));
					if ($line!="")
					{
						if ((substr($line,0,1)=="[") && (substr($line,-1)=="]"))
						{
							$currentsection=trim(substr($line,1,-1));
						}
						else
						{
							$elements=explode("=",$line);
							$contents[$currentsection][trim($elements[0])]=trim($elements[1]);
						}
					}
				}
				$contents[$section][$variablename]=$variablevalue;

				uksort($contents,'_sort');
				if ($file_h=fopen($filename,"wb"))
				{
					foreach($contents as $scansection => $scanvariable)
					{
						uksort($contents[$scansection],'_sort');
						if ($scansection!=="")
							fputs($file_h,"[".$scansection."]\n");
						foreach($contents[$scansection] as $scanname => $scanvalue)
						{
							fputs($file_h,$scanname."=".$scanvalue."\n");
						}
					}
					fclose($file_h);
				}
				else
				{
					exit("Can't open file ".$filename." for writing in write_meta.");
				}
			}
			else
			{
				exit("Can't open file ".$filename." for reading in write_meta.");
			}
		}
		else
		{
			if ($file_h=fopen($filename,"wb"))
			{
				if ($section!=="")
					fputs($file_h,"[".$section."]\n");
				fputs($file_h,$variablename."=".$variablevalue."\n");
				fclose($file_h);
			}
			else
			{
				exit("Can't open file ".$filename." for writing in write_meta.");
			}
		}
	}
}

// ================================================================================

function inc_meta($filename,$variablename,$section="Global",$amount=1)
{
	if (file_exists($filename))
	{
		if ($file_h=fopen($filename,"rb"))
		{
			$currentsection="";
			while (!feof($file_h))
			{
				$line=trim(fgets($file_h,255));
				if ($line!="")
				{
					if ((substr($line,0,1)=="[") && (substr($line,-1)=="]"))
					{
						$currentsection=trim(substr($line,1,-1));
					}
					else
					{
						$elements=explode("=",$line);
						$contents[$currentsection][trim($elements[0])]=trim($elements[1]);
					}
				}
			}
			fclose($file_h);

			if (isset($contents[$section][$variablename]))
			{
				$contents[$section][$variablename]=$contents[$section][$variablename]+$amount;
			}
			else
			{
				$contents[$section][$variablename]=$amount;
			}
			
			uksort($contents,'_sort');
			if ($file_h=fopen($filename,"wb"))
			{
				foreach($contents as $scansection => $scanvariable)
				{
					uksort($contents[$scansection],'_sort');
					if ($scansection!=="")
						fputs($file_h,"[".$scansection."]\n");
					foreach($contents[$scansection] as $scanname => $scanvalue)
					{
						fputs($file_h,$scanname."=".$scanvalue."\n");
					}
				}
				fclose($file_h);
			}
			else
			{
				exit("Can't open file ".$filename." for writing in inc_meta.");
			}
		}
		else
		{
			exit("Can't open file ".$filename." for reading in inc_meta.");
		}
	}
	else
	{
		exit("File ".$filename." doesn't exist in inc_meta.");
	}
}

// ================================================================================

function import_meta($filename)
{
	global $meta_file_contents,$meta_file_changed,$meta_file_name;

	if (isset($meta_file_contents) and isset($meta_file_name) and $meta_file_name!=$filename)
		export_meta($meta_file_name); // If we have stuff open alrady, then make sure it's written out before it gets overwritten by the new file

	if (isset($meta_file_contents) and isset($meta_file_name) and $meta_file_name==$filename)
		return; // If the meta file is already open, then we don't need to do it again.

	if (file_exists($filename))
	{
		if ($file_h=fopen($filename,"rb"))
		{
			$currentsection="";
			while (!feof($file_h))
			{
				$line=trim(fgets($file_h,255));
				if ($line!="")
				{
					if ((substr($line,0,1)=="[") && (substr($line,-1)=="]"))
					{
						$currentsection=trim(substr($line,1,-1));
					}
					else
					{
						$elements=explode("=",$line);
						$meta_file_contents[$currentsection][trim($elements[0])]=trim($elements[1]);
					}
				}
			}
			$meta_file_name=$filename;
			$meta_file_changed=FALSE;
		}
		else
		{
			exit("Can't open file ".$filename." in import_meta.");
		}
	}
	else
	{
		exit("File ".$filename." in import_meta doesn't exist.");
	}
}

// ================================================================================

function export_meta($filename)
{
	global $meta_file_contents,$meta_file_changed,$meta_file_name;

	if ($meta_file_changed)
	{
		uksort($meta_file_contents,'_sort');
		if ($file_h=fopen($filename,"wb"))
		{
			foreach($meta_file_contents as $scansection => $scanvariable)
			{
				uksort($meta_file_contents[$scansection],'_sort');
				if ($scansection!=="")
					fputs($file_h,"[".$scansection."]\n");
				foreach($meta_file_contents[$scansection] as $scanname => $scanvalue)
				{
					fputs($file_h,$scanname."=".$scanvalue."\n");
				}
			}
			fclose($file_h);
		}
		else
		{
			exit("Can't open file ".$filename." for writing in export_meta.");
		}
	}

	unset($meta_file_contents);
	unset($meta_file_changed);
	unset($meta_file_name);
}

?>