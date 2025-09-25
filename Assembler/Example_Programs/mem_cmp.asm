; load value to be place din RAM
LDI X, 1337
; load value to be compared with RAM value
LDI A, 1338

; Store value from X to RAM locations
ST X, [0x0004]
; Compare A register with value stored in ram at 0x0004
CMPMEMA [0x0004]
; JMP to match label if a match
JZ Match
; Jump to Less label A is less than mem
JC Less
; Jump to More label if A is more than mem (not safe way to do it)
JNZ More

Match:
DISPTXT A, <<EOB, [0x0004]

Memory location Matches Value in A Register
EOB
JMP Finish

More:
DISPTXT A, <<EOB, [0x0004]

Memory location is less than Value in A Register
EOB
JMP Finish

Less:
DISPTXT A, <<EOB, [0x0004]

Memory location is greater than Value in A Register
EOB
JMP Finish

Finish:
HLT