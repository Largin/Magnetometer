# Magnetometer

Script to convert data from magnetometer.

Data is split into chunks, each chunk consists same nummber of points.
Each point has timestamp and value.

Each chunk is is considered in itself, it's timestamps normalized to first timestamp.
Values are considered normalized to average of first elements of the chunk, and not.

Chunks can be filtered by number of chunk, average of first elements related to average of last elements, and by comparing values of agregate functions to set up limits
All data (normalized and not) are exported as table having chunks as columns and timestamps as rows, with values of functions appended.
Script generates plots with chunks data, averages, and functions.

Input data:
CSV files containg:
	header row:
		chunk;timestamp;value
	Rows with data:
		0;4853816079647;2519.88

Output data:
CSV files containg:
	timestamps\chunk,0,1,...,average
	Rows with data
	Rows with results of aggregate functions
Plots representing data

Script has configurable options:
	headers - is input files hase headers rows
	input_delimiter - delimiter fo input files
	input_directory - path to directory with input files
	output_name - path and name of output files

	averages - options of computing average of chunks
		head_len - number of points at start of chunk to take into average
		tail_len - number of points at end of chunk to take into average
		drop - ignore chunk if diff between head average and tail average is greater than limit
		tail_head_diff - limit to compare to when dropping chunks

	filter - options to filter chunks
		chunk_min - ignore chunks before this number
		chunk_max - ignore chunks after this number
		drop - is filter active

	functions - options of functions to apply
		label - name of function for csv output and plot
		callback - callback function
		filter - ignore chunk if absolute value of callback is greater than this
		filter_min - ignore chunk if value of callback is lower than this
		filter_max - ignore chunk if value of callback is greater than this
		drop - ignore chunk taking values before normalizing
		drop_corrected - ignore chunk taking values after normalizing

	plot_title - title of plots
