setblock 18 70 57 minecraft:air
place feature minecraft:jungle_bush 18 70 57
particle minecraft:happy_villager 18 73 57 1.5 2.5 1.5 0 30 force
particle minecraft:composter 18 71 57 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock 18 66 99 minecraft:air
place feature minecraft:jungle_bush 18 66 99
particle minecraft:happy_villager 18 69 99 1.5 2.5 1.5 0 30 force
particle minecraft:composter 18 67 99 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -138.072 98.611 0.500
