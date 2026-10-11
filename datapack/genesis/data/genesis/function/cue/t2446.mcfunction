setblock -36 83 -157 minecraft:air
place feature minecraft:pale_oak -36 83 -157
setblock -41 82 -158 minecraft:air
place feature minecraft:pale_oak -41 82 -158
setblock -45 83 -159 minecraft:air
place feature minecraft:pale_oak -45 83 -159
setblock -50 64 171 minecraft:air
place feature minecraft:swamp_oak -50 64 171
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -313.730 122.021 0.500
