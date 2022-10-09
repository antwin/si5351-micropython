Micropython code for the Si5351 synthesiser. It currently sets up two channels of the Si5351 as  signal generators with a frequency range of 2kHz to 290MHz, depending on the actual silicon. This is a python version derived from the very informative code in https://rfzero.net/tutorials/si5351a/
It is used on a raspberry pi Pico 2040, but the routine si.calcRegisters will also run on python3. This is useful for checking against the register values created in the on-line tool at https://rfzero.net/documentation/tools/si5351a-frequency-tool/

This is a work-in-progress. Expect errors and changes!
