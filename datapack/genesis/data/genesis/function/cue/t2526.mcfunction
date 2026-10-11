setblock -88 65 248 minecraft:air
place feature minecraft:tall_mangrove -88 65 248
setblock -89 64 252 minecraft:air
place feature minecraft:tall_mangrove -89 64 252
setblock -91 64 256 minecraft:air
place feature minecraft:tall_mangrove -91 64 256
setblock -95 64 259 minecraft:air
place feature minecraft:mangrove -95 64 259
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -316.104 117.076 0.500
