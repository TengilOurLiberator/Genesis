setblock 13 75 -11 minecraft:air
place feature minecraft:oak 13 75 -11
particle minecraft:happy_villager 13 78 -11 1.5 2.5 1.5 0 30 force
particle minecraft:composter 13 76 -11 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -108.492 84.712 0.500
