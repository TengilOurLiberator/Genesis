summon minecraft:mannequin -222.50 69.00 2.50 {Tags:["gen.figure","gen.m_eve"],CustomName:"Eve",Invulnerable:1b,PersistenceRequired:1b,Glowing:1b,Rotation:[-90f,0f],profile:{texture:"genesis:entity/eve"}}
particle minecraft:flash{color:[1.0,1.0,0.95,1.0]} -222.50 69.00 2.50 0 0 0 0 1 force
execute positioned -222.50 69.00 2.50 run particle minecraft:end_rod ~ ~1 ~ 0.3 0.8 0.3 0.25 120 force
execute as @a at @s run playsound minecraft:block.amethyst_block.resonate ambient @s ~ ~ ~ 1.0 1.1 1.0
