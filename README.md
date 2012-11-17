slack_pytsk
===========

A Sleuthkit tool to check the slack space at the end of each file in a filesystem.

The project is based on pytsk.

##How to use

The tool works in "list mode" or "extraction mode". In list mode it lists each file reporting for each of them the amount of slack space available, and the number of non-null bytes in the slack. In extraction mode it creates a directory tree containing the files that have an non-empty slack and exports a file that contains the content of the slack.

##Sleuthkit

Sleuthkit and Autopsy Browser are open source digital investigation tools (a.k.a. digital forensic tools) that run on Windows, Linux, OS X, and other Unix systems. They can be used to analyze disk images and perform in-depth analysis of file systems (such as NTFS, FAT, HFS+, Ext3, and UFS) and several volume system types. For more information: http://www.sleuthkit.org

###Pytsk
A python binding for the sleuthkit. For more information: http://code.google.com/p/pytsk/