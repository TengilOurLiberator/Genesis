setblock -37 67 30 minecraft:air
place feature minecraft:fancy_oak -37 67 30
particle minecraft:happy_villager -37 70 30 1.5 2.5 1.5 0 30 force
particle minecraft:composter -37 68 30 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
execute as @a at @s run playsound genesis:sfx.growth ambient @s ~ ~ ~ 0.9 0.9 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -113.590 86.532 0.500
