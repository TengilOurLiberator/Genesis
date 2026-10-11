fill 81 103 1 81 103 4 minecraft:stone
fill 80 103 -1 80 103 7 minecraft:stone
fill 79 103 -2 79 103 9 minecraft:stone
fill 78 103 -3 78 103 11 minecraft:stone
fill 77 103 -5 77 103 13 minecraft:stone
fill 76 103 -8 76 103 15 minecraft:stone
fill 75 103 -11 75 103 17 minecraft:stone
fill 74 103 -14 74 103 18 minecraft:stone
fill 73 103 -16 73 103 18 minecraft:stone
fill 72 103 -18 72 103 19 minecraft:stone
fill 71 103 -19 71 103 19 minecraft:stone
fill 70 103 -20 70 103 19 minecraft:stone
fill 69 103 -21 69 103 20 minecraft:stone
fill 68 103 -22 68 103 20 minecraft:stone
fill 67 103 -23 67 103 21 minecraft:stone
fill 66 103 -25 66 103 23 minecraft:stone
fill 65 103 -28 65 103 24 minecraft:stone
fill 64 103 -30 64 103 25 minecraft:stone
fill 63 103 -31 63 103 25 minecraft:stone
fill 62 103 -32 62 103 26 minecraft:stone
fill 61 103 -33 61 103 26 minecraft:stone
fill 59 103 -34 60 103 27 minecraft:stone
fill 58 103 -35 58 103 27 minecraft:stone
fill 56 103 -35 57 103 28 minecraft:stone
fill 55 103 -35 55 103 29 minecraft:stone
fill 52 103 -35 54 103 30 minecraft:stone
fill 51 103 -34 51 103 30 minecraft:stone
fill 50 103 -34 50 103 29 minecraft:stone
fill 49 103 -34 49 103 28 minecraft:stone
fill 48 103 -34 48 103 27 minecraft:stone
fill 47 103 -33 47 103 25 minecraft:stone
fill 46 103 -32 46 103 23 minecraft:stone
fill 45 103 -31 45 103 20 minecraft:stone
fill 44 103 -30 44 103 16 minecraft:stone
fill 43 103 -29 43 103 11 minecraft:stone
fill 42 103 -2 42 103 8 minecraft:stone
fill 42 103 -28 42 103 -17 minecraft:stone
fill 41 103 0 41 103 5 minecraft:stone
fill 41 103 -27 41 103 -19 minecraft:stone
fill 40 103 -26 40 103 -20 minecraft:stone
fill 39 103 -24 39 103 -23 minecraft:stone
particle minecraft:splash 0 63.2 0 68 0.4 68 0.3 500 force
particle minecraft:cloud 0 103 0 45 0.5 45 0.02 80 force
particle minecraft:dust_plume 0 103 0 40 0.4 40 0.02 60 force
execute as @a at @s run playsound minecraft:entity.generic.splash ambient @s ~ ~ ~ 0.6 0.5 0.6
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -153.548 79.265 0.500
