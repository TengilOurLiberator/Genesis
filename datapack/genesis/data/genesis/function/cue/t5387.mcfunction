particle minecraft:end_rod -60.50 130.00 -1.50 0.12 8 0.12 0.002 22 force
particle minecraft:glow -60.50 130.00 -1.50 0.2 8 0.2 0 6 force
particle minecraft:end_rod -60.50 130.00 2.50 0.12 8 0.12 0.002 22 force
particle minecraft:glow -60.50 130.00 2.50 0.2 8 0.2 0 6 force
execute as @a at @s run playsound minecraft:block.beacon.activate ambient @s ~ ~ ~ 0.9 0.5 0.9
execute as @a at @s run playsound genesis:sfx.heartbeat ambient @s ~ ~ ~ 0.9 1.0 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -77.537 72.494 0.500
