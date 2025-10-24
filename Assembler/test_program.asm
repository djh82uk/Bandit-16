
.org 0x03E8

Test1:

DISPTXT A, <<EOB, [0x0004]

Test 1: Addition (5 + 6)
Result should be 0x000b
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 5
LDI B, 6
ADD A, B, X
IOO  X, [0x0002] 
Wait1:
FI
JNI INPUT1
JMP Wait1

Test2:

DISPTXT A, <<EOB, [0x0004]

Test 2: Subtraction (10-6)
Result should be 0x0004
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 10
LDI B, 6
SUB A, B, X
IOO  X, [0x0002] 
Wait2:
FI
JNI INPUT2 
JMP Wait2

Test3:

DISPTXT A, <<EOB, [0x0004]

Test 3: Shift Left (10)
Result should be 0x0014
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 10
SHL A, X
IOO  X, [0x0002] 
Wait3:
FI
JNI INPUT3 
JMP Wait3

Test4:

DISPTXT A, <<EOB, [0x0004]

Test 4: Shift Right (10)
Result should be 0x0005
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 10
SHR A, X
IOO  X, [0x0002] 
Wait4:
FI
JNI INPUT4
JMP Wait4

Test5:

DISPTXT A, <<EOB, [0x0004]

Test 5: AND (100 AND 150)
Result should be 0x0004
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 100
LDI B, 150
AND A, B, X
IOO  X, [0x0002] 
Wait5:
FI
JNI INPUT5
JMP Wait5

Test6:

DISPTXT A, <<EOB, [0x0004]

Test 6: OR (100 OR 150)
Result should be 0x00F6
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 100
LDI B, 150
OR A, B, X
IOO  X, [0x0002] 
Wait6:
FI
JNI INPUT6
JMP Wait6


Test7:

DISPTXT A, <<EOB, [0x0004]

Test 7: XOR (100 XOR 150)
Result should be 0x00F2
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 100
LDI B, 150
XOR A, B, X
IOO  X, [0x0002] 
Wait7:
FI
JNI INPUT7
JMP Wait7


Test8:

DISPTXT A, <<EOB, [0x0004]

Test 8: Increment A (100 +1)
Result should be 0x0065
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 100
INCA
IOO  A, [0x0002] 
Wait8:
FI
JNI INPUT8
JMP Wait8


Test9:

DISPTXT A, <<EOB, [0x0004]

Test 9: Decrement B (4000-1)
Result should be 0x0F9F
Check the Hex Output 
Press Enter to Continue

EOB

LDI B, 4000
DECB
IOO  B, [0x0002] 
Wait9:
FI
JNI INPUT9
JMP Wait9


Test10:

DISPTXT A, <<EOB, [0x0004]

Test 10: Mov (1337 -> B -> Y)
Result should be 0x0539
Check the Hex Output 
Press Enter to Continue

EOB

LDI B, 1337
MOV Y, B
IOO  Y, [0x0002] 
Wait10:
FI
JNI INPUT10
JMP Wait10


Test11:

DISPTXT A, <<EOB, [0x0004]

Test 11: FPUSH & FPOP
Result should be 0x0014
Check the Hex Output 
Press Enter to Continue

EOB

LDI A, 60000
LDI B, 20000
ADD A, B, X
FPUSH
LDI A, 10
LDI B, 10
ADD A, B, Y
FPOP
JC JCTest

Wait11:
FI
JNI INPUT11
JMP Wait11

JCTest:
IOO  Y, [0x0002] 
JMP Wait11


Test12:

DISPTXT A, <<EOB, [0x0004]

Test 12: BSRO and BSRA
Result should be 0x0605
Check the Hex Output 
Press Enter to Continue

EOB

BSRA 0x1000
Back_to_rom:
IOO  A, [0x0002] 
Wait12:
FI
JNI INPUT12
JMP Wait12

Test13:

DISPTXT A, <<EOB, [0x0004]

Test 13: JSR and RET
Result should be 0x098C
Check the Hex Output 
Press Enter to Continue

EOB

JSR test_subroutine13
LDI X, 1222
ADD X, B, A

IOO  A, [0x0002] 
Wait13:
FI
JNI INPUT13
JMP Wait13

test_subroutine13:
LDI B, 1222
RET

INPUT1:

    IOI  Y, [0x0008]    
    JMP Test2

INPUT2:

    IOI  Y, [0x0008]    
    JMP Test3

INPUT3:

    IOI  Y, [0x0008]  
    JMP Test4

INPUT4:

    IOI  Y, [0x0008]  
    JMP Test5

INPUT5:

    IOI  Y, [0x0008]  
    JMP Test6

INPUT6:

    IOI  Y, [0x0008]  
    JMP Test7

INPUT7:

    IOI  Y, [0x0008]  
    JMP Test8

INPUT8:

    IOI  Y, [0x0008]  
    JMP Test9

INPUT9:

    IOI  Y, [0x0008]  
    JMP Test10

INPUT10:

    IOI  Y, [0x0008]  
    JMP Test11

INPUT11:

    IOI  Y, [0x0008]  
    JMP Test12

INPUT12:

    IOI  Y, [0x0008]  
    JMP Test13

INPUT13:

    IOI  Y, [0x0008]  
    JMP Finish

Finish:
HLT


.section RAM
.org 0x1000         ; Start of RAM data section

LDI A, 1541
BSRO Back_to_rom