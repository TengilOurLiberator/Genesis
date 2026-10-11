setblock 24 84 -7 minecraft:air
place feature minecraft:oak 24 84 -7
particle minecraft:happy_villager 24 87 -7 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -98.699 80.132 0.500
