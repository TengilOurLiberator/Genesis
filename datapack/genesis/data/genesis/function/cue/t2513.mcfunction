setblock 5 72 52 minecraft:air
place feature minecraft:cherry 5 72 52
particle minecraft:happy_villager 5 75 52 1.5 2.5 1.5 0 30 force
particle minecraft:composter 5 73 52 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -109.213 84.969 0.500
