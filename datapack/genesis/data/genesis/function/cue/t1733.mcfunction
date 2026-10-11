fill 79 108 1 79 108 4 minecraft:stone
fill 78 108 0 78 108 7 minecraft:stone
fill 77 108 -1 77 108 8 minecraft:stone
fill 76 108 -2 76 108 10 minecraft:stone
fill 75 108 -4 75 108 12 minecraft:stone
fill 74 108 -8 74 108 14 minecraft:stone
fill 73 108 -12 73 108 15 minecraft:stone
fill 72 108 -15 72 108 16 minecraft:stone
fill 71 108 -17 71 108 16 minecraft:stone
fill 70 108 -18 70 108 17 minecraft:stone
fill 69 108 -19 69 108 17 minecraft:stone
fill 68 108 -19 68 108 18 minecraft:stone
fill 67 108 -20 67 108 18 minecraft:stone
fill 66 108 -21 66 108 19 minecraft:stone
fill 65 108 -23 65 108 20 minecraft:stone
fill 64 108 -25 64 108 21 minecraft:stone
fill 63 108 -27 63 108 22 minecraft:stone
fill 62 108 -29 62 108 23 minecraft:stone
fill 61 108 -30 61 108 23 minecraft:stone
fill 60 108 -31 60 108 24 minecraft:stone
fill 58 108 -32 59 108 24 minecraft:stone
fill 57 108 -32 57 108 25 minecraft:stone
fill 56 108 -33 56 108 25 minecraft:stone
fill 55 108 -33 55 108 26 minecraft:stone
fill 51 108 -32 54 108 27 minecraft:stone
fill 50 108 -31 50 108 26 minecraft:stone
fill 49 108 -31 49 108 25 minecraft:stone
fill 48 108 -30 48 108 24 minecraft:stone
fill 47 108 -30 47 108 21 minecraft:stone
fill 46 108 -29 46 108 17 minecraft:stone
fill 45 108 -28 45 108 11 minecraft:stone
fill 44 108 -28 44 108 -17 minecraft:stone
fill 43 108 -27 43 108 -19 minecraft:stone
fill 42 108 -25 42 108 -21 minecraft:stone
particle minecraft:splash 0 63.2 0 68 0.4 68 0.3 500 force
particle minecraft:cloud 0 108 0 45 0.5 45 0.02 80 force
particle minecraft:dust_plume 0 108 0 40 0.4 40 0.02 60 force
execute as @a at @s run playsound minecraft:entity.generic.splash ambient @s ~ ~ ~ 0.6 0.5 0.6
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -154.269 80.510 0.500
