; Basic Adder - enter a number between 0-9 and then enter a 2nd number between 0-9 (don't press enter), result is pushed to the output.  Seems super basic (and it is) but it has to translate numbers to and from ASCII

LDI B, 48

DISPTXT A, <<EOB1, [0x0004]
Enter first number to add 0-9

EOB1

Wait1:
FI
JNI Num1
JMP Wait1

Num1:
IOI Y, [0x0008]
SUB Y, B, Y

DISPTXT A, <<EOB2, [0x0004]
Enter second number to add 0-9

EOB2

Wait2:
FI
JNI Num2
JMP Wait2

Num2:
IOI X, [0x0008]
SUB X, B, X

ADD X, Y, A
MOV X, A
LDI Y, 0
LDI B, 100

HundLoop:
CMP X, B
JC Tens
SUB X, B, X
INCY
JMP HundLoop

Tens:
MOV A, X
LDI X, 0
LDI B, 10

TensLoop:
CMP A, B
JC Units
SUB A, B, A
INCX
JMP TensLoop

Units:
MOV B, A
LDI A, 48
ADD Y, A, Y
ADD X, A, X
ADD B, A, B

DISPTXT A, <<EOB2, [0x0004]

Result:
EOB2

CMP Y, A
JNZ ShowHundreds
CMP X, A
JNZ ShowTens
JMP ShowUnits

ShowHundreds:
IOO Y, [0x0004]

ShowTens:
IOO X, [0x0004]

ShowUnits:
IOO B, [0x0004]
HLT