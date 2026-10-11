setblock 24 101 -180 minecraft:air
place feature minecraft:oak 24 101 -180
setblock 20 101 -182 minecraft:air
place feature minecraft:oak 20 101 -182
setblock 20 82 185 minecraft:air
place feature minecraft:jungle_tree_no_vine 20 82 185
setblock 17 101 -187 minecraft:air
place feature minecraft:oak 17 101 -187
setblock 11 81 203 minecraft:air
place feature minecraft:jungle_bush 11 81 203
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -317.164 114.867 0.500
