setblock -61 68 -48 minecraft:air
place feature minecraft:birch -61 68 -48
particle minecraft:happy_villager -61 71 -48 1.5 2.5 1.5 0 30 force
particle minecraft:composter -61 69 -48 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock -61 66 56 minecraft:air
place feature minecraft:birch -61 66 56
particle minecraft:happy_villager -61 69 56 1.5 2.5 1.5 0 30 force
particle minecraft:composter -61 67 56 1 2 1 0 16 force
execute as @a at @s run playsound genesis:sfx.growth ambient @s ~ ~ ~ 0.9 0.9 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -145.616 101.545 0.500
