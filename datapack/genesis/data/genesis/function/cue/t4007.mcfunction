setblock 19 70 -39 minecraft:air
place feature minecraft:cherry 19 70 -39
particle minecraft:happy_villager 19 73 -39 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -100.007 81.005 0.500
