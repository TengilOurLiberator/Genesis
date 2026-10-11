setblock 33 68 35 minecraft:air
place feature minecraft:oak_bees_005 33 68 35
particle minecraft:happy_villager 33 71 35 1.5 2.5 1.5 0 30 force
particle minecraft:composter 33 69 35 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -106.894 84.141 0.500
