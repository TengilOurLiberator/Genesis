setblock 0 71 -46 minecraft:air
place feature minecraft:oak 0 71 -46
particle minecraft:happy_villager 0 74 -46 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -100.456 81.304 0.500
