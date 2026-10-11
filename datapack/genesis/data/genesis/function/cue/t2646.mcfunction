setblock 67 78 218 minecraft:air
place feature minecraft:jungle_tree 67 78 218
setblock 66 76 211 minecraft:air
place feature minecraft:jungle_tree_no_vine 66 76 211
setblock 62 80 217 minecraft:air
place feature minecraft:mega_jungle_tree 62 80 217
setblock 60 68 225 minecraft:air
place feature minecraft:jungle_tree_no_vine 60 68 225
setblock 59 69 229 minecraft:air
place feature minecraft:mega_jungle_tree 59 69 229
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -318.803 111.453 0.500
