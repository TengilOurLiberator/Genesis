setblock 50 79 -49 minecraft:air
place feature minecraft:acacia 50 79 -49
particle minecraft:happy_villager 50 82 -49 1.5 2.5 1.5 0 30 force
particle minecraft:composter 50 80 -49 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.661 98.063 0.500
