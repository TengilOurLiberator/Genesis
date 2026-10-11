setblock -42 69 50 minecraft:air
place feature minecraft:oak -42 69 50
particle minecraft:happy_villager -42 72 50 1.5 2.5 1.5 0 30 force
particle minecraft:composter -42 70 50 1 2 1 0 16 force
setblock -42 71 -31 minecraft:air
place feature minecraft:cherry -42 71 -31
particle minecraft:happy_villager -42 74 -31 1.5 2.5 1.5 0 30 force
particle minecraft:composter -42 72 -31 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -143.658 100.784 0.500
