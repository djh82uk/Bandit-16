.org 0x03E8
; count to 280 in 304 Bytes

; Initialise count as zero 
LDI A, 0 
; Count to 280
LDI B, 280 

Loop:
; Increment A
INCA 
; Output A
IOO A, [0x0002] 
; Load Flags
FI 
; Compare A and B
CMP A, B 
; Jump if A does not match B
JNZ Loop 
; Jump to end
JMP Finish

; Display completion message and Halt
Finish: 
DISPTXT X, <<EOB, [0x0004]
Program Complete
EOB