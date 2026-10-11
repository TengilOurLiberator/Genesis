setblock -26 67 -51 minecraft:air
place feature minecraft:oak_bees_005 -26 67 -51
particle minecraft:happy_villager -26 70 -51 1.5 2.5 1.5 0 30 force
particle minecraft:composter -26 68 -51 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -112.482 86.136 0.500
