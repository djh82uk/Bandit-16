
.org 0x03E8

Test1:

DISPTXT A, <<EOB, [0x0004]

Test 1: Addition
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

Test 2: Subtraction
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

Test 3: Shift Left
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

Test 4: Shift Right
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

Test 4: AND
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

Test 4: OR
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

Test 4: XOR
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

Test 4: Increment A
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
    JMP Finish

Finish:
HLT


