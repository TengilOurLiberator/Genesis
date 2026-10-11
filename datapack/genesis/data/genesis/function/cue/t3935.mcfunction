setblock 8 73 8 minecraft:air
place feature minecraft:oak 8 73 8
particle minecraft:happy_villager 8 76 8 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
