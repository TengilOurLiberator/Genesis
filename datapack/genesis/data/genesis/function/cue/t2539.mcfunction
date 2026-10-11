function genesis:god/spark
setblock -68 64 242 minecraft:air
place feature minecraft:mangrove -68 64 242
setblock -70 64 246 minecraft:air
place feature minecraft:tall_mangrove -70 64 246
setblock -75 64 250 minecraft:air
place feature minecraft:mangrove -75 64 250
setblock -79 64 250 minecraft:air
place feature minecraft:mangrove -79 64 250
setblock -83 64 255 minecraft:air
place feature minecraft:mangrove -83 64 255
execute as @a at @s run playsound genesis:sfx.growth ambient @s ~ ~ ~ 0.9 0.9 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -316.461 116.331 0.500
