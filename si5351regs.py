'''
20220915 ajbw converted from https://rfzero.net/tutorials/si5351a/
'''
import time
try:
    from machine import I2C
    micropython = True
except ImportError:
    micropython = False

def write8(reg,value):
    if micropython:
        i2c.writeto_mem(0x60, reg, bytes([value]))
    else:
        print('reg ',reg,'%02X' % (value,))
           
def enableOutputs(chan,enabled):
    ''' Enabled  output (see Register 3). Currently only one channel at a time '''
    if chan == 0:
        val = 0xFE if enabled else 0xFF
    else:
        val = 0xFD if enabled else 0xFF
    write8(3, val)

def calcRegisters(fout,fref=25000000,chan=0):   
    ''' 
    chan 0 is PLLA MS0 (CLK0).  chan 1 is PLLB MS1
    https://rfzero.net/tutorials/si5351a/
    https://rfzero.net/documentation/tools/si5351a-frequency-tool/
    '''
#    fref = 25000000                  # The reference frequency
#    fref = 25008130                  # The reference frequency
    # Calc Output Multisynth Divider and R with e = 0 and f = 1 => msx_p2 = 0 and msx_p3 = 1
    d = 4
    msx_p1 = 0                         # If fout > 150 MHz then MSx_P1 = 0 and MSx_DIVBY4 = 0xC0, 
                #see datasheet 4.1.3
    msx_divby4 = 0
    rx_div = 0
    r = 1
 
    if (fout > 150000000):
        msx_divby4 = 0x0C                       # MSx_DIVBY4[1:0]  = 0b11, see datasheet 4.1.3
    elif (fout < 292969):                    # If fout < 500 kHz then use R divider, 
                            #see datasheet 4.2.2. In reality this means > 292 968,75 Hz when d = 2048   
        rd = 0
        while ((r < 128) and (r * fout < 292969)):        
            r <<= 1
            rd += 1       
        rx_div = rd << 4		
        d = 600000000 // (r * fout)            # Use lowest VCO frequency but handle d minimum
        if (d % 2):                               # Make d even to reduce spurious and phase noise/jitter, 
                                                #see datasheet 4.1.2.1.
            d += 1
        if (d * r * fout < 600000000):          # VCO frequency to low check and maintain an even d value
            d += 2   	
    else:                                         # 292968 Hz <= fout <= 150 MHz   
        d = 600000000 // fout                  # Use lowest VCO frequency but handle d minimum
        if (d < 6):
            d = 6
        elif (d % 2):                          # Make d even to reduce phase noise/jitter, see datasheet 4.1.2.1.
           d += 1
			
        if (d * fout < 600000000):              # VCO frequency to low check and maintain an even d value
            d += 2    
    msx_p1 = 128 * d - 512 
    fvco = d * r * fout
    # Calc Feedback Multisynth Divider
    fmd = fvco / fref            # The FMD value has been found
    a = int(fmd)                                 # a is the integer part of the FMD value 
    b_c = float(fmd - a)                # Get b/c
    c = 1048575
    b = int(b_c * c)
    if (b > 0):    
        c = int(b / b_c + 0.5)               # Improves frequency precision in some cases
        if (c > 1048575):
            c = 1048575    
    msnx_p1 = 128 * a + int(128.0 * b / c) - 512   # See datasheet 3.2
    msnx_p2 = 128 * b - c * int(128.0 * b / c)
    msnx_p3 = c
    if not micropython:
        print(a,b/c,b,c,msnx_p1,msnx_p2,msnx_p3)
    # Feedback Multisynth Divider register values
    
    baseaddr = 26 if chan == 0 else 34
    write8(baseaddr + 0,(msnx_p3 >> 8) & 0xFF)
    write8(baseaddr + 1,msnx_p3 & 0xFF)
    write8(baseaddr + 2,(msnx_p1 >> 16) & 0x03)
   
    write8(baseaddr + 3,(msnx_p1 >> 8) & 0xFF)
    write8(baseaddr + 4,msnx_p1 & 0xFF)
    write8(baseaddr + 5,((msnx_p3 >> 12) & 0xF0) + ((msnx_p2 >> 16) & 0x0F)  )
    write8(baseaddr + 6,(msnx_p2 >> 8) & 0xFF)
    write8(baseaddr + 7,msnx_p2 & 0xFF)
 
    # Output Multisynth Divider and R register values
    baseaddr = 34 if chan == 0 else 42
    # set in init write8(baseaddr + 8,0 )                                 # 42 (msx_p3 >> 8) & 0xFF
    # set in init write8(baseaddr + 9,1 )                                 # 43 msx_p3 & 0xFF
    write8(baseaddr + 10,rx_div + msx_divby4 + ((msx_p1 >> 16) & 0x03) )
    write8(baseaddr + 11,(msx_p1 >> 8) & 0xFF )
    write8(baseaddr + 12,msx_p1 & 0xFF )
    # set in init write8(baseaddr + 13,0 )                                # 47 ((msx_p3 >> 12) & 0xF0) + (msx_p2 >> 16) & 0x0F
    # set in init write8(baseaddr + 14,0 )                                # 48 (msx_p2 >> 8) & 0xFF
    # set in init write8(baseaddr + 15,0 )                                # 49 msx_p2 & 0xFF
    time.sleep(.001)                            # Allow registers to settle before resetting the PLL
    if chan == 0:
        write8(177,0x20)
    else:
        write8(177,0x80)
    if not micropython:
        print(d,r,msx_p1)
    return

#def initialize(i2c,chan=0):
def initialize(): #chan=0):
    # Initialize Si5351A
    #while (ReadRegister(0) & 0x80)    # Wait for Si5351A to initialize
    write8(3, 0xFF)            # Output Enable Control, disable all    	
    for i in range(16,24):
        write8 (i, 0x80)       # CLKi Control, power down CLKi 
    write8(15, 0x00)           # PLL Input Source, select the XTAL input as the reference clock for PLLA and PLLB
    write8(24, 0x00)           # CLK3–0 Disable State, unused are low and never disable CLK0    
    # Output Multisynth0, e = 0, f = 1, MS0_P2 and MSO_P3
    write8(42, 0x00)
    write8(43, 0x01)
    write8(47, 0x00)
    write8(48, 0x00)
    write8(49, 0x00)
    # Output Multisynth1, e = 0, f = 1, MS1_P2 and MS1_P3
    write8(50, 0x00)
    write8(51, 0x01)
    write8(55, 0x00)
    write8(56, 0x00)
    write8(57, 0x00)
 
    
    write8(16, 0x4F)           # Power up CLK0, PLLA, MS0 operates in integer mode,
            # Output Clock 0 is not inverted, Select MultiSynth 0 as the source for CLK0 and 8 mA 
    write8(17, 0x6F)           # Power up CLK1, PLLB, MS1 operates in integer mode,
            # Output Clock 1 is not inverted, Select MultiSynth 1 as the source for CLK1 and 8 mA 
    # Reference load configuration
    write8(183, 0x12)          # Set reference load C: 6 pF = 0x12, 8 pF = 0x92, 10 pF = 0xD2
    '''
    # Turn CLK0 output on
    write8(3, 0xFE)            # Output Enable Control. Active low
    # Turn CLK1 output on
    write8(3, 0xFD)            # Output Enable Control. Active low
    '''
    # Turn CLK0 and CLK1 outputs on
    write8(3, 0xFC)            # Output Enable Control. Active low    
