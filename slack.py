#!/usr/bin/python
# ******************************************************
# Sokratis Vidros <sokratis.vidros@gmail.com>
#
# ******************************************************
#  Version: 1.0 Date: 13/06/2012
# ******************************************************
#
# * This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License
# * as published by the Free Software Foundation; either version 2
# * of the License, or (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# ******************************************************

import images
import pytsk3
import re
import string
import sys
from optparse import OptionParser
from pytsk3 import *

parser = OptionParser()

parser.add_option('-o', '--offset', default=0, type='int',
                  help='Offset in the image (in bytes)')

parser.add_option("-l", "--long", action='store_true', default=False,
                  help="Display long version (like ls -l)")

parser.add_option("-r", "--recursive", action='store_true', default=False,
                  help="Display a recursive file listing.")

parser.add_option("-e", "--encoding", default="ascii",
                  help="Display slack space in ASCII or Hex. Supported options 'ascii', 'hex")

parser.add_option("-m", "--mode", default="list",
                  help="Select mode. Supported options 'list', 'extract")

parser.add_option("-t", "--type", default="raw",
                  help="Type of image. Currently supported options 'raw (dd)', "
                  "'ewf'")

parser.add_option("-i", "--inode", default=None, type="int",
                  help="The inode to list")

parser.add_option("-p", "--path", default="/",
                  help="Path to list (Default /)")

(options, args) = parser.parse_args()


FILE_TYPE_LOOKUP = {
    TSK_FS_NAME_TYPE_UNDEF : '-',
    TSK_FS_NAME_TYPE_FIFO : 'p',
    TSK_FS_NAME_TYPE_CHR : 'c',
    TSK_FS_NAME_TYPE_DIR : 'd',
    TSK_FS_NAME_TYPE_BLK : 'b',
    TSK_FS_NAME_TYPE_REG : 'r',
    TSK_FS_NAME_TYPE_LNK : 'l',
    TSK_FS_NAME_TYPE_SOCK : 'h',
    TSK_FS_NAME_TYPE_SHAD : 's',
    TSK_FS_NAME_TYPE_WHT : 'w',
    TSK_FS_NAME_TYPE_VIRT : 'v'
}

META_TYPE_LOOKUP = {
    TSK_FS_META_TYPE_REG : 'r',
    TSK_FS_META_TYPE_DIR : 'd',
    TSK_FS_META_TYPE_FIFO : 'p',
    TSK_FS_META_TYPE_CHR : 'c',
    TSK_FS_META_TYPE_BLK : 'b',
    TSK_FS_META_TYPE_LNK : 'h',
    TSK_FS_META_TYPE_SHAD : 's',
    TSK_FS_META_TYPE_SOCK :'s',
    TSK_FS_META_TYPE_WHT : 'w',
    TSK_FS_META_TYPE_VIRT : 'v'
}

NTFS_TYPES_TO_PRINT = [
    TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
    TSK_FS_ATTR_TYPE_NTFS_DATA,
    TSK_FS_ATTR_TYPE_DEFAULT,
]

FILTER = ''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def hex_pp(src, length=8):
    """ Hex pretty printer. """
    
    N=0; result=''
    while src:
       s,src = src[:length],src[length:]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
       N+=length
    return result


def get_slack(inode):
    """ Returns the slack space of the block. """
    
    f = fs.open_meta(inode = inode)

    # Walk all blocks allocated by this file as in some filesystems 
    # each file has several attributes which can allocate multiple 
    # blocks.
    l_offset = 0

    for attr in f:
        for run in attr:
            l_offset = run.offset

    # Last block of the file
    l_block = (l_offset - 1) * blocksize

    if l_block < 0:
        l_block = 0

    # File size
    size = f.info.meta.size

    # Actual file data in the last block
    l_d_size = size % blocksize

    # Slack space size
    s_size = blocksize - l_d_size

    slack_bytes = []

    while l_block < size:
        # Force reading the slack of the file providing the FLAG_SLACK
        data = f.read_random(l_block + l_d_size, s_size, TSK_FS_ATTR_TYPE_DEFAULT, 0, TSK_FS_FILE_READ_FLAG_SLACK )
        if not data:
            break

        l_block += len(data)

        if options.encoding == "ascii":
            slack_bytes.extend(["%02x" % ord(c) for c in data if ord(c) != 00])
             
        elif options.encoding == "hex":
            # TODO print in hex
            print hex_pp(data)
    
    if ( options.mode == 'list' ):
        # Returns slack size, valid slack content size 
        return s_size, len(slack_bytes)
    else:
        # Returns slack ascii content, valid slack content size
        return ("".join([chr(int(b,16)) for b in slack_bytes]) , len(slack_bytes))


def is_fs_directory(f):
    """ Checks if an inode is a filesystem directory. """
    
    return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_DIR]


def is_fs_regfile(f):
    """Checks if an inode is a regular file."""
    
    return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_REG]


def scan_inode(f, ident = 1, prefix = ''):
    """ Fetches meta data (type, filename, slack) of an inode (file or directory).
        
        Note that inodes work on FAT filesystems as well.
    """
    
    meta = f.info.meta
    name = f.info.name
    inode = f.info.meta.addr

    name_type = '-'
    if name:
        name_type = FILE_TYPE_LOOKUP.get(int(name.type), '-')

    meta_type = '-'
    if meta:
        meta_type = META_TYPE_LOOKUP.get(int(meta.type), '-')

    type = "%s/%s" % (name_type, meta_type)

    slack_data = ''
    slack_size = ''
 
    # Fetch slack information only for files
    if (is_fs_regfile(f)):
        slack_data, slack_size = get_slack(inode);

    # Get all file attributes
    for attr in f:
        inode_type = int(attr.info.type)
        if inode_type in NTFS_TYPES_TO_PRINT:
            attribute_name = attr.info.name
            # For NTFS filesystems
            if attribute_name and attribute_name != "$Data" and attribute_name != "$I30":
                filename = "%s:%s" % (name.name, attr.info.name)
            else:
                filename = name.name
            
            # Skip current and previous folder
            if filename == '.' or filename=='..': continue

            if meta and name:
                if ( options.mode == 'list' ):
                    print "{0:<32} {1:^30} {2:>16}".format(type + "- " + filename, slack_data, slack_size)
                elif ((options.mode == 'extract' and slack_size > 0) or is_fs_directory(f)):
                    print "%s%s" % (prefix, type) + "    |" * ident + "- {0} : {1}".format(filename, slack_data)


def list_directory(directory, stack = None, indent = 0):
    """ Iterate over all files in a directory and print the related meta data.
        In each iteration a proxy object is returned for the TSK_FS_FILE
        struct - you can further dereference this struct into a TSK_FS_NAME
        and TSK_FS_META structs.
    """
    stack.append(directory.info.fs_file.meta.addr)

    for f in directory:

        prefix = '';
        scan_inode(f, indent, prefix)

        if (is_fs_directory(f)) and options.recursive:
            try:
                d = f.as_directory()
                inode = f.info.meta.addr
            
                # This ensures that we dont recurse into a directory
                # above the current level to avoid circular loops:
                if inode not in stack:
                    list_directory(d, stack, indent + 1)
            except RuntimeError, IOError:
                print 'Error!'

    stack.pop(-1)


# Open img file
img = images.SelectImage(options.type, args)

# Open the filesystem
fs = pytsk3.FS_Info(img, offset = (options.offset * 512 ))

# Open the directory node
if options.inode is not None:
    directory = fs.open_dir(inode=options.inode)
else:
    directory = fs.open_dir(path=options.path)

# Get the blocksize
blocksize = fs.info.block_size

# Get listing the
if options.mode == 'list':
   print "{0:40} {1:20} {2:16}".format("File", "Slack size", "Filled slack space")
   print "-" * 80

list_directory(directory, [], 0)
