setblock -48 67 -71 minecraft:air
place feature minecraft:birch -48 67 -71
particle minecraft:happy_villager -48 70 -71 1.5 2.5 1.5 0 30 force
particle minecraft:composter -48 68 -71 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -144.423 101.081 0.500
