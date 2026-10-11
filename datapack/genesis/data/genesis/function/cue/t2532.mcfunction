setblock 14 71 -59 minecraft:air
place feature minecraft:acacia 14 71 -59
particle minecraft:happy_villager 14 74 -59 1.5 2.5 1.5 0 30 force
particle minecraft:composter 14 72 -59 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -138.324 98.709 0.500
