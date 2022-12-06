#!/usr/bin/env python3

from migen import *
from migen.genlib.io import CRG
from migen.genlib.cdc import MultiReg

## debe dejar solo una tarjeta
import tarjetas.nexys4ddr as tarjeta # si usa tarjeta nexy 4 
# import tarjetas.nexys4ddr as tarjeta # si usa tarjeta nexy 4 4DRR
#import tarjetas.digilent_zybo_z7 as tarjeta # si usa tarjeta zybo z7
# import tarjetas.c4e6e10 as tarjeta

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect.csr import *

from litex.soc.cores import gpio
from module import rgbled
from module import vgacontroller
from module.display import SevenSegmentDisplay
from module import camara

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
	def __init__(self):
		sys_clk_freq = int(100e6)
		platform = tarjeta.Platform()
		# SoC with CPU
		platform.add_source("module/verilog/camara/camara.v")
		platform.add_source("module/verilog/camara/buffer_ram_dp.v")
		platform.add_source("module/verilog/camara/cam_read.v")
		platform.add_source("module/verilog/camara/VGA_driver.v")
		platform.add_source("module/verilog/camara/PLL/clk24_25_nexys4.v")
		platform.add_source("module/verilog/camara/PLL/clk24_25_nexys4_0.v")
		platform.add_source("module/verilog/camara/PLL/clk24_25_nexys4_clk_wiz.v")
		SoCCore.__init__(self, platform,
# 			cpu_type="picorv32",
			cpu_type="vexriscv",
			clk_freq=100e6,
			integrated_rom_size=0x8000,
			integrated_sram_size=0x1000,
			integrated_main_ram_size=20*1024)

		# Clock Reset Generation
		self.submodules.crg = CRG(platform.request("clk"), ~platform.request("cpu_reset"))

		# Leds
		SoCCore.add_csr(self,"leds")
		user_leds = Cat(*[platform.request("led", i) for i in range(10)])
		self.submodules.leds = gpio.GPIOOut(user_leds)
		
		# Switchs
		SoCCore.add_csr(self,"switchs")
		user_switchs = Cat(*[platform.request("sw", i) for i in range(7)])
		self.submodules.switchs = gpio.GPIOIn(user_switchs)
		
		# Buttons  ("btnl", 0, Pins("P17"), IOStandard("LVCMOS33")),

		SoCCore.add_csr(self,"buttons")
		user_buttons = Cat(*[platform.request("btn%c" %c) for c in ['c','r','l']])
		self.submodules.buttons = gpio.GPIOIn(user_buttons)
		

		# RGB leds
		#SoCCore.add_csr(self,"ledRGB_1")
		#self.submodules.ledRGB_1 = rgbled.RGBLed(platform.request("ledRGB",1))
		
#		SoCCore.add_csr(self,"ledRGB_2")
#		self.submodules.ledRGB_2 = rgbled.RGBLed(platform.request("ledRGB",2))
		
		#7segments Display para zybo z7 comentar 
  
		#self.submodules.display = SevenSegmentDisplay(sys_clk_freq)
		#self.add_csr("display")
		#self.comb += [
          #platform.request("display_cs_n").eq(~self.display.cs),
#           platform.request("display_abcdefg").eq(~self.display.abcdefg)
#   	]				
		# VGA
		#SoCCore.add_csr(self,"vga_cntrl")
		vga_red = Cat(*[platform.request("vga_red", i) for i in range(4)])
		vga_green = Cat(*[platform.request("vga_green", i) for i in range(4)])
		vga_blue = Cat(*[platform.request("vga_blue", i) for i in range(4)]) # Se concatena
		vsync=platform.request("vsync")
		hsync=platform.request("hsync")
		#self.submodules.vga_cntrl = vgacontroller.VGAcontroller(hsync,vsync, vga_red, vga_green, vga_blue)
		
		#Camara
		SoCCore.add_csr(self,"camara_cntrl") # Incluir mapa de memoria
		SoCCore.add_interrupt(self,"camara_cntrl")
		cam_data_in = Cat(*[platform.request("cam_data_in", i) for i in range(8)])		
		self.submodules.camara_cntrl = camara.Camara(vsync,hsync,vga_red,vga_green,vga_blue,platform.request("cam_xclk"),platform.request("cam_pwdn"),platform.request("cam_pclk"),cam_data_in,platform.request("cam_vsync"),platform.request("cam_href"))

# Build --------------------------------------------------------------------------------------------
if __name__ == "__main__":
	builder = Builder(BaseSoC(),output_dir="build", csr_csv="csr.csv")
	builder.build(build_name="top")

