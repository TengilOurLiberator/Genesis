setblock 28 67 -51 minecraft:air
place feature minecraft:fancy_oak 28 67 -51
particle minecraft:happy_villager 28 70 -51 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -102.847 82.898 0.500
