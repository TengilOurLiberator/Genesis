summon minecraft:block_display -50.00 82.00 0.50 {Tags:["gen.orb"],block_state:"minecraft:pearlescent_froglight",brightness:{sky:15,block:15},view_range:40f,transformation:{translation:[-0.025f,0f,-0.035f],left_rotation:[0.3827f,0f,0f,0.9239f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:end_rod -50.00 82.00 0.50 0.30 0.30 0.30 0.002 30 force
execute as @a at @s run playsound minecraft:block.amethyst_block.resonate ambient @s ~ ~ ~ 0.9 0.5 0.9
