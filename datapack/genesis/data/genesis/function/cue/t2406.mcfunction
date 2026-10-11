setblock -74 84 -169 minecraft:air
place feature minecraft:pale_oak -74 84 -169
setblock -75 87 -163 minecraft:air
place feature minecraft:pale_oak -75 87 -163
setblock -80 64 171 minecraft:air
place feature minecraft:tall_mangrove -80 64 171
setblock -80 83 -166 minecraft:air
place feature minecraft:pale_oak -80 83 -166
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -312.507 124.568 0.500
