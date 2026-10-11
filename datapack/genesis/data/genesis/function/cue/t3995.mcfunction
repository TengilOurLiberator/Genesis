setblock 21 71 -32 minecraft:air
place feature minecraft:fancy_oak 21 71 -32
particle minecraft:happy_villager 21 74 -32 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -99.595 80.730 0.500
