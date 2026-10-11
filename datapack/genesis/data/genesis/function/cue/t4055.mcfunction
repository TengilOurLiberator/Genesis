setblock 11 69 53 minecraft:air
place feature minecraft:oak 11 69 53
particle minecraft:happy_villager 11 72 53 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -101.908 82.272 0.500
