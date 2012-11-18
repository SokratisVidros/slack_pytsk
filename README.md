slack_pytsk
===========

A Sleuthkit tool to check the slack space at the end of each file in a filesystem.

The smaller allocation unit in a file system is a block, and blocks normally contain multiple disk sectors. As a result, when a user is creating a file with a size that is not a perfect multiple of a block size, some free space remains in the last block, called block slack space. Some operating systems fill this space with 0s (null bytes) but others apparently let the other disk sectors unchanged, therefore possibly containing previous data.

The project is based on pytsk.

##Installation

+ Clone and install the required libraries of pytsk. More information found at https://code.google.com/p/pytsk/.

```
su root
cd ~ && hg clone https://code.google.com/p/pytsk/ pytsk
cd pytsk
./setup.py build
./setup.py install
```

##How to use

The tool works in "list mode" or "extraction mode". In list mode it lists each file reporting for each of them the amount of slack space available, and the number of non-null bytes in the slack. In extraction mode it creates a directory tree containing the files that have an non-empty slack and exports a file that contains the content of the slack.

To get help on how to use the script type

```
./slack.py -h
```

##Sleuthkit

Sleuthkit and Autopsy Browser are open source digital investigation tools (a.k.a. digital forensic tools) that run on Windows, Linux, OS X, and other Unix systems. They can be used to analyze disk images and perform in-depth analysis of file systems (such as NTFS, FAT, HFS+, Ext3, and UFS) and several volume system types. For more information: http://www.sleuthkit.org

###Pytsk
A python binding for the sleuthkit. For more information: http://code.google.com/p/pytsk/==============================
