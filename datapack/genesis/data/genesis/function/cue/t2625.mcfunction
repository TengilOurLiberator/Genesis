setblock 64 66 -30 minecraft:air
place feature minecraft:fancy_oak 64 66 -30
particle minecraft:happy_villager 64 69 -30 1.5 2.5 1.5 0 30 force
particle minecraft:composter 64 67 -30 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
