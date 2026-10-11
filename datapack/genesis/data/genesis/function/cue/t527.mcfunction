particle minecraft:flash{color:[1.0,1.0,0.9,1.0]} -40.00 185.00 -125.00 0 0 0 0 1 force
particle minecraft:end_rod -40.00 185.00 -125.00 3 3 3 1.6 2200 force
particle minecraft:glow -40.00 185.00 -125.00 8 8 8 0.5 500 force
particle minecraft:firework -40.00 185.00 -125.00 2 2 2 0.9 400 force
execute as @a at @s run playsound genesis:sfx.light ambient @s ~ ~ ~ 1.0 1.0 1.0
execute as @a at @s run playsound minecraft:block.beacon.activate ambient @s ~ ~ ~ 0.9 0.7 0.9
