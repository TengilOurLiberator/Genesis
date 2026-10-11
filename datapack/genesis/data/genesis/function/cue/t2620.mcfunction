setblock 88 89 -2 minecraft:air
place feature minecraft:pine 88 89 -2
particle minecraft:happy_villager 88 92 -2 1.5 2.5 1.5 0 30 force
particle minecraft:composter 88 90 -2 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
