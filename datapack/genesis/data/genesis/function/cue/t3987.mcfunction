summon minecraft:parrot -98.54 71.82 20.90 {PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -98.54 72.42 20.90 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -98.54 72.62 20.90 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound genesis:sfx.birds ambient @s ~ ~ ~ 0.9 1.0 0.9
execute as @a at @s run playsound minecraft:entity.parrot.fly ambient @s ~ ~ ~ 1.0 1.0 1.0
