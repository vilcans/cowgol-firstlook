COWGOL_DIR = cowgol

TARGET ?= test1

LIBRARIES = \
	src/arch/spectrum/lib/runtime.cow \
	src/arch/z80/lib/runtime.cow \
	src/arch/common/lib/runtime.cow

all: $(TARGET).tap

# Build binary from Cowgol source
%.bin: %.cow
	cd $(COWGOL_DIR) && scripts/cowgol -a spectrum_on_native -o $(abspath $@) \
		$(LIBRARIES) \
		$(abspath $<)

# Create tape image containing the binary code
%.tap: %.bin
	bin/totap.py -n $(TARGET) --start=0x6000 --prepend boot.tap -o $@ $<

.PHONY: run
run: $(TARGET).tap
	fuse $(TARGET).tap

.PHONY: disassemble
disassemble: $(TARGET).bin
	z80dasm -tlag 0x6000 $(TARGET).bin
