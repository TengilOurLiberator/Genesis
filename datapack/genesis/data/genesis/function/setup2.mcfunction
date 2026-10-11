fill 993 99 993 1010 105 1007 minecraft:barrier hollow
fill 994 99 994 1009 99 1006 minecraft:black_concrete
setblock 1003 99 997 minecraft:gold_block
setblock 1003 99 1003 minecraft:diamond_block
setblock 1003 102 997 minecraft:light[level=15]
setblock 1003 102 1003 minecraft:light[level=15]
setblock 998 102 1000 minecraft:light[level=11]
kill @e[tag=gen.lobbytext]
kill @e[tag=gen.cam]
summon minecraft:text_display 1003.5 101.9 997.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"ADAM",color:"gold"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.6f,1.6f,1.6f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1003.5 101.9 1003.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"EVE",color:"aqua"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.6f,1.6f,1.6f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1008.5 103.4 1000.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"GENESIS",color:"white"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[3.2f,3.2f,3.2f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1008.5 102.3 1000.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"Stand on a stone to choose who you will be",color:"white"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.1f,1.1f,1.1f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:marker -150.50 66.00 0.50 {Tags:["gen.cam"]}
