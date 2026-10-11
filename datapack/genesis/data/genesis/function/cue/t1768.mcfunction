fill 47 88 -1 47 88 5 minecraft:stone
fill 46 88 -3 46 88 6 minecraft:stone
fill 45 88 -5 45 88 7 minecraft:stone
fill 44 88 -6 44 88 7 minecraft:stone
fill 43 88 -7 43 88 8 minecraft:stone
fill 42 88 -8 42 88 8 minecraft:stone
fill 40 88 -8 41 88 9 minecraft:stone
fill 39 88 -9 39 88 9 minecraft:stone
fill 36 88 -9 38 88 10 minecraft:stone
fill 34 88 -8 35 88 10 minecraft:stone
fill 33 88 -8 33 88 9 minecraft:stone
fill 32 88 -7 32 88 9 minecraft:stone
fill 31 88 -6 31 88 9 minecraft:stone
fill 30 88 -5 30 88 8 minecraft:stone
fill 29 88 -4 29 88 7 minecraft:stone
fill 28 88 -2 28 88 6 minecraft:stone
fill 27 88 0 27 88 4 minecraft:stone
particle minecraft:splash 0 63.2 0 46 0.4 46 0.3 300 force
particle minecraft:cloud 0 88 0 30 0.5 30 0.02 50 force
particle minecraft:dust_plume 0 88 0 26 0.4 26 0.02 40 force
execute as @a at @s run playsound minecraft:entity.generic.splash ambient @s ~ ~ ~ 0.6 0.5 0.6
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -126.137 80.062 0.500
