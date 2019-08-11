COWGOL_DIR = cowgol

TARGET ?= test1

LIBRARIES = \
	src/arch/spectrum/lib/runtime.cow \
	src/arch/z80/lib/runtime.cow \
	src/arch/common/lib/runtime.cow

all: $(TARGET).tap

%.tap: %.bin
	bin/totap.py --start=0x6000 -o $@ $<

%.bin: %.cow
	cd $(COWGOL_DIR) && scripts/cowgol -a spectrum_on_native -o $(abspath $@) \
		$(LIBRARIES) \
		$(abspath $<)

run.tap: $(TARGET).tap
	cat boot.tap $(TARGET).tap >$@

.PHONY: run
run: run.tap
	fuse run.tap

.PHONY: disassemble
disassemble: $(TARGET).bin
	z80dasm -tlag 0x6000 $(TARGET).bin
