setblock -37 69 -79 minecraft:air
place feature minecraft:cherry -37 69 -79
particle minecraft:happy_villager -37 72 -79 1.5 2.5 1.5 0 30 force
particle minecraft:composter -37 70 -79 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock -36 71 -51 minecraft:air
place feature minecraft:oak_bees_005 -36 71 -51
particle minecraft:happy_villager -36 74 -51 1.5 2.5 1.5 0 30 force
particle minecraft:composter -36 72 -51 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -143.212 100.610 0.500
