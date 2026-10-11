function genesis:awake
execute as @a at @s run playsound minecraft:entity.player.breath ambient @s ~ ~ ~ 1.0 0.8 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -61.500 69.000 0.500
