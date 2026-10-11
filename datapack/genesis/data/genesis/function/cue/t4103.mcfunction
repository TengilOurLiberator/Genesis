setblock 67 67 21 minecraft:air
place feature minecraft:oak_bees_005 67 67 21
particle minecraft:happy_villager 67 70 21 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -103.653 83.435 0.500
