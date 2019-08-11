#!/usr/bin/env python3

from array import array
import argparse

# TAP file format:
# http://www.zxshed.co.uk/sinclairfaq/index.php5?title=TAP_format

# How to inject binary data into basic program:
# Add a line with the following code (only):
#   REM INJECT HERE
# Run this script with --inject=somefile.bin.
# Then the content of the REM statement will be replaced
# by the content of somefile.bin.

REM = '\xea'
inject_marker = REM + 'INJECT HERE\x0d'

def to_block(flag, data):
    """Creates a TAP block from raw bytes"""
    block = array('B')
    total = len(data) + 2  # including flag and checksum
    block.append(total & 0xff)
    block.append(total >> 8)
    block.append(flag)
    block += data

    checksum = flag
    for d in data:
        checksum ^= d
    block.append(checksum & 0xff)

    return block


def get_header(data_length, param1, param2, type, filename='HELLO'):
    """Creates a Spectrum tape header (17 bytes)

    param1 =
        * autostart line number for basic or >= 32768 if no autostart
        * start of code block for binary

    param2 =
        * start of variable area relative to start of program for basic
        * 32768 for code
    """
    header = array('B')
    # type: 0=program, 3=code
    header.append(type)
    for c in filename.ljust(10)[:10]:
        header.append(ord(c))
    header += array('B', [
        # length of data
        data_length & 0xff, data_length >> 8,
        # autostart line number for basic or >= 32768 if no autostart
        # start of code block for binary
        param1 & 0xff, param1 >> 8,
        # start of variable area relative to start of program
        # 32768 for code
        param2 & 0xff, param2 >> 8,
    ])
    return header


def make_tap(
    binary_data,
    output_tap_file,
    file_type,  # 0=basic program, 3=bytes
    spectrum_filename,
    start,
):
    binary_data = array('B', binary_data)

    header_block = get_header(
        len(binary_data),
        param1=start if start is not None else 32768,
        param2=len(binary_data) if file_type == 0 else 32768,
        type=file_type,
        filename=spectrum_filename
    )

    output_tap_file.write(to_block(0x00, header_block))
    output_tap_file.write(to_block(0xff, binary_data))


def main():
    parser = argparse.ArgumentParser(
        description='Create a TAP file, optionally injecting additional data'
    )
    parser.add_argument(
        '-n', '--name', metavar='FILENAME', default='DEMO',
        help='Spectrum file name'
    )
    parser.add_argument(
        '--inject', metavar='FILE', type=argparse.FileType('rb'),
        help='Binary data to inject into BASIC program'
    )
    parser.add_argument(
        '-o', metavar='TAP', required=True,
        type=argparse.FileType('wb'),
        help='tap file to write'
    )
    parser.add_argument('--start', type=lambda x: int(x, 0),
        help='Autostart line number for BASIC or load address for binary'
    )
    parser.add_argument('--basic', action='store_true',
        help='Store as a BASIC file instead of binary (Bytes)'
    )
    parser.add_argument(
        'file', metavar='FILE', type=argparse.FileType('rb'),
        help='Data to insert. For BASIC file, created using e.g. zmakebas.'
    )

    args = parser.parse_args()

    data = args.file.read()
    if args.inject:
        inject_data = args.inject.read()
        basic_line = REM + inject_data + '\x0d'
        # Replace marker with actual code
        pos = data.index(inject_marker)
        line_length = len(basic_line)
        data = ''.join((
            data[:pos - 2],
            chr(line_length & 0xff),
            chr(line_length >> 8),
            basic_line,
            data[pos + len(inject_marker):]
        ))

    make_tap(data, args.o, 0 if args.basic else 3, args.name, args.start)


if __name__ == '__main__':
    main()

# 00000000  13 00 00 00 41 00 00 00 00 00 00 00 00 00 08 00  |....A...........|
# 00000010  0a 00 08 00 4b 0a 00 ff 00 0a 04 00 f1 61 3d 61  |....K........a=a|

# 00000000  13 00 00 00 44 45 4d 4f 20 20 20 20 20 20 a3 00  |....DEMO      ..|
#           ^^ ^^ TAP block size
#                 ^^ flag byte (A reg, 00 for headers, ff for data blocks)
#                    ^^ first byte of header (type)
#                       ^^ ^^ ^^ ^^ ^^ ^^ ^^ ^^ ^^ ^^ file name
#                                                     ^^ ^^ length of data block
# 00000010  00 80 a3 00 83 a5 00 ff 00 0a 27 00 f1 61 3d be  |..........'..a=.|
#           ^^ ^^ ^^ ^^ param1, param2
#                       ^^ checksum
#                          ^^ ^^ TAP block size
#                                ^^ flag, ff = data block
#                                   ^^ ^^ line number
#                                         ^^ ^^ line length
# 00000020  32 33 36 33 35 0e 00 00 53 5c 00 2b 32 35 36 0e  |23635...S\.+256.|
# 00000030  00 00 00 01 00 2a be 32 33 36 33 36 0e 00 00 54  |.....*.23636...T|
# 00000040  5c 00 0d 00 14 1d 00 f1 6c 3d be 28 61 2b 31 0e  |\.......l=.(a+1.|
# 00000050  00 00 01 00 00 29 2b 32 35 36 0e 00 00 00 01 00  |.....)+256......|
# 00000060  2a be 61 0d 00 1e 1b 00 fa 6c 3d 32 35 35 0e 00  |*.a......l=255..|
# 00000070  00 ff 00 00 cb f9 c0 61 2b 35 0e 00 00 05 00 00  |.......a+5......|
# 00000080  3a e2 0d 00 28 23 00 f1 61 3d 61 2b be 28 61 2b  |:...(#..a=a+.(a+|
# 00000090  32 0e 00 00 02 00 00 29 2b 34 0e 00 00 04 00 00  |2......)+4......|
# 000000a0  3a ec 32 0e 00 00 02 00 00 0d 00 ff 0d 00 ea 30  |:.2............0|
# 000000b0  31 32 33 34 35 36 37 38 39 30 0d 0b              |1234567890..|
# 000000bc

