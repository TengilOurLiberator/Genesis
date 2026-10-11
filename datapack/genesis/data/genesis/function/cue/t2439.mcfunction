setblock -46 70 -38 minecraft:air
place feature minecraft:cherry -46 70 -38
particle minecraft:happy_villager -46 73 -38 1.5 2.5 1.5 0 30 force
particle minecraft:composter -46 71 -38 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -144.038 100.931 0.500
