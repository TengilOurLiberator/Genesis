summon minecraft:parrot -69.55 75.68 -0.44 {PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -69.55 76.28 -0.44 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -69.55 76.48 -0.44 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound genesis:sfx.birds ambient @s ~ ~ ~ 0.9 1.0 0.9
execute as @a at @s run playsound minecraft:entity.parrot.fly ambient @s ~ ~ ~ 1.0 1.0 1.0
