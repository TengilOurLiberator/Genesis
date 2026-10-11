setblock -255 65 18 minecraft:air
place feature minecraft:oak -255 65 18
setblock -257 65 -15 minecraft:air
place feature minecraft:oak -257 65 -15
setblock -245 69 17 minecraft:air
place feature minecraft:fancy_oak -245 69 17
setblock -246 69 -15 minecraft:air
place feature minecraft:oak -246 69 -15
setblock -246 68 -24 minecraft:air
place feature minecraft:oak -246 68 -24
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -308.444 133.034 0.500
