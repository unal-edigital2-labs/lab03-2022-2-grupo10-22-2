PACKAGES=libc libcompiler_rt libbase libfatfs liblitespi liblitedram libliteeth liblitesdcard liblitesata bios
PACKAGE_DIRS=/tools/PLitex/litex/litex/soc/software/libc /tools/PLitex/litex/litex/soc/software/libcompiler_rt /tools/PLitex/litex/litex/soc/software/libbase /tools/PLitex/litex/litex/soc/software/libfatfs /tools/PLitex/litex/litex/soc/software/liblitespi /tools/PLitex/litex/litex/soc/software/liblitedram /tools/PLitex/litex/litex/soc/software/libliteeth /tools/PLitex/litex/litex/soc/software/liblitesdcard /tools/PLitex/litex/litex/soc/software/liblitesata /tools/PLitex/litex/litex/soc/software/bios
LIBS=libc libcompiler_rt libbase libfatfs liblitespi liblitedram libliteeth liblitesdcard liblitesata
TRIPLE=riscv64-unknown-elf
CPU=vexriscv
CPUFAMILY=riscv
CPUFLAGS=-march=rv32i2p0_m     -mabi=ilp32 -D__vexriscv__
CPUENDIANNESS=little
CLANG=0
CPU_DIRECTORY=/tools/PLitex/litex/litex/soc/cores/cpu/vexriscv
SOC_DIRECTORY=/tools/PLitex/litex/litex/soc
PICOLIBC_DIRECTORY=/tools/PLitex/pythondata-software-picolibc/pythondata_software_picolibc/data
COMPILER_RT_DIRECTORY=/tools/PLitex/pythondata-software-compiler_rt/pythondata_software_compiler_rt/data
export BUILDINC_DIRECTORY
BUILDINC_DIRECTORY=/LabsDigital2/lab03-2022-2-grupo10-22-2-main/SoC_project/build/software/include
LIBC_DIRECTORY=/tools/PLitex/litex/litex/soc/software/libc
LIBCOMPILER_RT_DIRECTORY=/tools/PLitex/litex/litex/soc/software/libcompiler_rt
LIBBASE_DIRECTORY=/tools/PLitex/litex/litex/soc/software/libbase
LIBFATFS_DIRECTORY=/tools/PLitex/litex/litex/soc/software/libfatfs
LIBLITESPI_DIRECTORY=/tools/PLitex/litex/litex/soc/software/liblitespi
LIBLITEDRAM_DIRECTORY=/tools/PLitex/litex/litex/soc/software/liblitedram
LIBLITEETH_DIRECTORY=/tools/PLitex/litex/litex/soc/software/libliteeth
LIBLITESDCARD_DIRECTORY=/tools/PLitex/litex/litex/soc/software/liblitesdcard
LIBLITESATA_DIRECTORY=/tools/PLitex/litex/litex/soc/software/liblitesata
BIOS_DIRECTORY=/tools/PLitex/litex/litex/soc/software/bios
LTO=0
BIOS_CONSOLE_FULL=1