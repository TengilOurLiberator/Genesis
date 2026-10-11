summon minecraft:parrot -284.89 72.53 -2.05 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -284.89 73.13 -2.05 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -284.89 73.33 -2.05 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound genesis:sfx.birds ambient @s ~ ~ ~ 0.9 1.0 0.9
execute as @a at @s run playsound minecraft:entity.parrot.fly ambient @s ~ ~ ~ 1.0 1.0 1.0
