setblock 2 75 -55 minecraft:air
place feature minecraft:cherry 2 75 -55
particle minecraft:happy_villager 2 78 -55 1.5 2.5 1.5 0 30 force
particle minecraft:composter 2 76 -55 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock 2 75 -65 minecraft:air
place feature minecraft:oak_bees_005 2 75 -65
particle minecraft:happy_villager 2 78 -65 1.5 2.5 1.5 0 30 force
particle minecraft:composter 2 76 -65 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -139.278 99.080 0.500
