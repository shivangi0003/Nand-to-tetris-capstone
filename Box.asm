// Box.asm   (K = 8)
// While any key is pressed, draw a black box. When no key is pressed, clear it.
// Box: starts at row 8, 20 rows tall, 16 pixels wide (1 word) at the left edge.
// Row r starts at SCREEN + 32*r, so the first box word is 16384 + 32*8 = 16640.
//
// Variables:  fill  = value to write (-1 = black, 0 = white)
//             addr  = address of the screen word being written
//             count = rows still to draw

(LOOP)
    @KBD
    D=M             // D = keyboard value (0 means no key)
    @BLACK
    D;JNE           // key pressed -> use black
    @fill
    M=0             // no key -> fill = 0 (white)
    @DRAW
    0;JMP
(BLACK)
    @fill
    M=-1            // fill = -1 (all 16 bits black)

(DRAW)
    @16640          // SCREEN + 32*8 = first word of row 8
    D=A
    @addr
    M=D             // addr = 16640
    @20
    D=A
    @count
    M=D             // count = 20 rows

(ROW)
    @fill
    D=M             // D = fill value
    @addr
    A=M             // A = address of this row's word
    M=D             // write fill to the screen
    @32
    D=A
    @addr
    M=D+M           // addr = addr + 32  (next row)
    @count
    MD=M-1          // count = count - 1
    @ROW
    D;JGT           // more rows left -> repeat
    @LOOP
    0;JMP           // start again: check the keyboard
