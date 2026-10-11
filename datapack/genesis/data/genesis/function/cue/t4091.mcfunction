setblock 60 72 21 minecraft:air
place feature minecraft:birch 60 72 21
particle minecraft:happy_villager 60 75 21 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -103.272 83.181 0.500
