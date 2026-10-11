summon minecraft:parrot -77.62 80.84 -14.92 {PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -77.62 81.44 -14.92 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -77.62 81.64 -14.92 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound minecraft:entity.parrot.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -122.500 70.254 0.500
