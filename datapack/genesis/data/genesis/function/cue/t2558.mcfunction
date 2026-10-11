setblock 32 67 63 minecraft:air
place feature minecraft:mega_jungle_tree 32 67 63
particle minecraft:happy_villager 32 70 63 1.5 2.5 1.5 0 30 force
particle minecraft:composter 32 68 63 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -137.358 98.334 0.500
