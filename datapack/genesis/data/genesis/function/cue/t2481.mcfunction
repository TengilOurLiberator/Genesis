setblock -17 77 59 minecraft:air
place feature minecraft:birch -17 77 59
particle minecraft:happy_villager -17 80 59 1.5 2.5 1.5 0 30 force
particle minecraft:composter -17 78 59 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock -16 73 -38 minecraft:air
place feature minecraft:birch -16 73 -38
particle minecraft:happy_villager -16 76 -38 1.5 2.5 1.5 0 30 force
particle minecraft:composter -16 74 -38 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -141.079 99.781 0.500
