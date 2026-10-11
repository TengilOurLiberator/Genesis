summon minecraft:dolphin -281.00 54.00 -13.00 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made","gen.whale"],attributes:[{id:"minecraft:scale",base:9.0}]}
summon minecraft:dolphin -279.00 53.00 15.00 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made","gen.whale"],attributes:[{id:"minecraft:scale",base:7.0}]}
particle minecraft:bubble -280.00 54.00 0.50 10 3 4 0.1 200 force
execute as @a at @s run playsound genesis:sfx.whale ambient @s ~ ~ ~ 1.0 1.0 1.0
execute as @a at @s run playsound minecraft:entity.elder_guardian.ambient ambient @s ~ ~ ~ 0.8 0.5 0.8
