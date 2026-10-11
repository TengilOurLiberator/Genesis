setblock -27 73 -44 minecraft:air
place feature minecraft:oak_bees_005 -27 73 -44
particle minecraft:happy_villager -27 76 -44 1.5 2.5 1.5 0 30 force
particle minecraft:composter -27 74 -44 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -142.142 100.194 0.500
