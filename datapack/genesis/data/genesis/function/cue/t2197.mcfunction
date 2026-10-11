function genesis:god/spark
execute as @a at @s run playsound genesis:sfx.growth ambient @s ~ ~ ~ 0.9 1.0 0.9
execute as @a at @s run playsound minecraft:block.grass.place ambient @s ~ ~ ~ 0.7 0.7 0.7
fill -261 63 -6 -261 63 6 grass_block
fill -259 64 -3 -259 64 3 grass_block
fill -260 64 -5 -260 64 5 grass_block
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -307.766 134.446 0.500
