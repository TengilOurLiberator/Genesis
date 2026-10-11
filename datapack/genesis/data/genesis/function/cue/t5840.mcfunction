summon minecraft:mannequin -30.50 69.00 -1.50 {Tags:["gen.figure","gen.m_adam"],CustomName:"Adam",Invulnerable:1b,PersistenceRequired:1b,Glowing:1b,Rotation:[-90f,0f],profile:{texture:"genesis:entity/adam"}}
particle minecraft:flash{color:[1.0,1.0,0.95,1.0]} -30.50 69.00 -1.50 0 0 0 0 1 force
execute positioned -30.50 69.00 -1.50 run particle minecraft:end_rod ~ ~1 ~ 0.3 0.8 0.3 0.25 120 force
execute as @a at @s run playsound minecraft:block.amethyst_block.resonate ambient @s ~ ~ ~ 1.0 0.8 1.0
