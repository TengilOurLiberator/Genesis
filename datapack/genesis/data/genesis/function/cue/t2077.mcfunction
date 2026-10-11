execute as @a at @s run playsound genesis:sfx.growth ambient @s ~ ~ ~ 0.9 1.0 0.9
fill -89 65 -2 -89 65 2 minecraft:grass_block replace minecraft:dirt
fill -90 65 1 -90 65 3 minecraft:grass_block replace minecraft:dirt
execute as @a at @s run playsound minecraft:block.grass.place ambient @s ~ ~ ~ 0.7 0.7 0.7
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -171.703 111.690 0.500
