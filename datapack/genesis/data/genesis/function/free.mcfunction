scoreboard players set #phase gen 2
scoreboard players set #cmode gen 1
kill @e[type=minecraft:item_display,tag=gen.god]
execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base reset
execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base reset
time of genesis:day rate 1
time of genesis:day resume
forceload remove all
forceload add -262 -40 -182 40
title @a times 30 80 40
title @a subtitle {text:"The world is yours to name",color:"gray"}
title @a title {text:"The seventh day",color:"white"}
