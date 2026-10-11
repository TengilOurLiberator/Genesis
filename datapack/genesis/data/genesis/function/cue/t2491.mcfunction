setblock -11 75 -45 minecraft:air
place feature minecraft:cherry -11 75 -45
particle minecraft:happy_villager -11 78 -45 1.5 2.5 1.5 0 30 force
particle minecraft:composter -11 76 -45 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -140.458 99.539 0.500
