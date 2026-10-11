particle minecraft:flash{color:[1.0,1.0,0.9,1.0]} -50.00 82.00 0.50 0 0 0 0 1 force
particle minecraft:end_rod -50.00 82.00 0.50 3 3 3 1.6 2200 force
particle minecraft:glow -50.00 82.00 0.50 8 8 8 0.5 500 force
particle minecraft:firework -50.00 82.00 0.50 2 2 2 0.9 400 force
data merge entity @e[tag=gen.orb,limit=1] {start_interpolation:0,interpolation_duration:70,transformation:{translation:[-0.025f,0f,-0.035f],left_rotation:[0.3827f,0f,0f,0.9239f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
execute as @a at @s run playsound genesis:sfx.light ambient @s ~ ~ ~ 1.0 1.0 1.0
execute as @a at @s run playsound minecraft:block.beacon.activate ambient @s ~ ~ ~ 0.9 0.7 0.9
