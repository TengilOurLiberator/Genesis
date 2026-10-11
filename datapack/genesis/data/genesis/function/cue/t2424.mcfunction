setblock -57 68 -60 minecraft:air
place feature minecraft:cherry -57 68 -60
particle minecraft:happy_villager -57 71 -60 1.5 2.5 1.5 0 30 force
particle minecraft:composter -57 69 -60 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -145.213 101.388 0.500
