function genesis:god/spark
execute as @a at @s run playsound genesis:sfx.wind ambient @s ~ ~ ~ 0.8 1.2 0.8
execute as @a at @s run playsound minecraft:item.elytra.flying ambient @s ~ ~ ~ 0.4 0.8 0.4
execute at @e[type=minecraft:marker,tag=gen.cam,limit=1] run particle minecraft:cloud ~ ~4 ~ 14 2 14 0.25 40 force
