setblock 16 80 11 minecraft:air
place feature minecraft:oak 16 80 11
particle minecraft:happy_villager 16 83 11 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -98.552 80.034 0.500
