setblock 73 92 26 minecraft:air
place feature minecraft:pine 73 92 26
particle minecraft:happy_villager 73 95 26 1.5 2.5 1.5 0 30 force
particle minecraft:composter 73 93 26 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.515 98.006 0.500
