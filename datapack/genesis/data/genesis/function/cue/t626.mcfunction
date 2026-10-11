particle minecraft:end_rod -70.00 76.00 0.50 3 3 3 1.4 1800 force
particle minecraft:glow -70.00 76.00 0.50 6 6 6 0.5 400 force
particle minecraft:flash{color:[1.0,1.0,0.9,1.0]} -70.00 76.00 0.50 0 0 0 0 1 force
execute as @a at @s run playsound minecraft:block.beacon.activate ambient @s ~ ~ ~ 1.0 0.7 1.0
