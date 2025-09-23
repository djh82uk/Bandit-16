; count to 280 in 298 Bytes

; Initialise count as zero in 298 Bytes
LDI A, 0 
; Count to 280
LDI B, 280 

LDI X, 1

Loop:
; Increment A via ALU
ADD A, X, A
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

HLT