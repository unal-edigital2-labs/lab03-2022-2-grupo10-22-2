#!/usr/bin/env python3

import os

from litex.build.xilinx import VivadoProgrammer

bitstream_file="./build/gateware/top.bit"
prog=VivadoProgrammer().load_bitstream( bitstream_file, target="", device=1)
