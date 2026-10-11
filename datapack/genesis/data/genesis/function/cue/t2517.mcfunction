setblock 4 69 31 minecraft:air
place feature minecraft:jungle_bush 4 69 31
particle minecraft:happy_villager 4 72 31 1.5 2.5 1.5 0 30 force
particle minecraft:composter 4 70 31 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -139.024 98.981 0.500
