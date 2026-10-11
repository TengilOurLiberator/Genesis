summon minecraft:cod 9.50 60.50 -3.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:splash 9.50 63.20 -3.50 0.3 0.1 0.3 0.1 10 force
execute as @a at @s run playsound minecraft:entity.dolphin.jump ambient @s ~ ~ ~ 0.9 1.0 0.9
