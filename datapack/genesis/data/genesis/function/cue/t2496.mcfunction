setblock -7 74 -39 minecraft:air
place feature minecraft:oak_bees_005 -7 74 -39
particle minecraft:happy_villager -7 77 -39 1.5 2.5 1.5 0 30 force
particle minecraft:composter -7 75 -39 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -140.162 99.424 0.500
