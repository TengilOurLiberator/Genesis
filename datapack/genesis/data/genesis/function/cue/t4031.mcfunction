setblock 12 68 -47 minecraft:air
place feature minecraft:cherry 12 68 -47
particle minecraft:happy_villager 12 71 -47 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -100.930 81.620 0.500
