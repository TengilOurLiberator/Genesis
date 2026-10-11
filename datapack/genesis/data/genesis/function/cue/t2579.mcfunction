setblock 43 87 32 minecraft:air
place feature minecraft:mega_jungle_tree 43 87 32
particle minecraft:happy_villager 43 90 32 1.5 2.5 1.5 0 30 force
particle minecraft:composter 43 88 32 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.829 98.128 0.500
