setblock -101 65 156 minecraft:air
place feature minecraft:swamp_oak -101 65 156
setblock -101 86 -162 minecraft:air
place feature minecraft:pale_oak -101 86 -162
setblock -102 89 -158 minecraft:air
place feature minecraft:pale_oak -102 89 -158
setblock -104 90 -155 minecraft:air
place feature minecraft:pale_oak -104 90 -155
setblock -105 65 160 minecraft:air
place feature minecraft:swamp_oak -105 65 160
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -311.322 127.037 0.500
