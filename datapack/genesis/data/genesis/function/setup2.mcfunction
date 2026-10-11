fill 993 99 993 1007 104 1007 minecraft:barrier hollow
fill 994 99 994 1006 99 1006 minecraft:black_concrete
setblock 997 99 996 minecraft:gold_block
setblock 1003 99 996 minecraft:diamond_block
setblock 997 102 996 minecraft:light[level=15]
setblock 1003 102 996 minecraft:light[level=15]
setblock 1000 102 1002 minecraft:light[level=12]
kill @e[tag=gen.lobbytext]
kill @e[tag=gen.cam]
summon minecraft:text_display 997.5 101.9 996.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"ADAM",color:"gold"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.6f,1.6f,1.6f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1003.5 101.9 996.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"EVE",color:"aqua"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.6f,1.6f,1.6f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1000.5 103.2 994.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"GENESIS",color:"white"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[3.0f,3.0f,3.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:text_display 1000.5 102.3 994.5 {Tags:["gen.lobbytext"],billboard:"center",background:0,brightness:{sky:15,block:15},text:{text:"Stand on a stone to choose who you will be",color:"white"},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.1f,1.1f,1.1f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:marker -120.5 66.0 0.5 {Tags:["gen.cam"]}
