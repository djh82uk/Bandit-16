.org 0x03E8
; Find all Fibonacci number upto the number put in line 5.  Line 5 must be a valid fibonacci number

; preload registers
LDI A, 0          
LDI B, 1
; specify a valid fibonacci number to finish at
LDI X, 6765         

; main loop
Loop:
;Output to Hex display
IOO A, [0x0002]
; Add A + B, output to Y   
ADD A, B, Y     
; Move A to B  
MOV B, A
; Move Y to A          
MOV A, Y  
; Compare with X to see if limit has been reached        
CMP A, X 
; Loop again if limit not reached   
JNZ Loop
; Jump to finish routine if limit is reached
JMP Finish

Finish:
; Output final number
IOO A, [0x0002]  
; Halt
HLT
