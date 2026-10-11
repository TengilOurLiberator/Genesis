scoreboard players set #phase gen 1
scoreboard players set #t gen 0
scoreboard players set #count gen -1
scoreboard players set #sunless gen 1
time of genesis:day set 6000
time of genesis:day pause
time of genesis:cut set 0
time of genesis:cut rate 1
time of genesis:cut resume
tag @a[tag=gen.lobby] add gen.viewer
tag @a remove gen.lobby
gamemode spectator @a[tag=gen.viewer]
title @a clear
stopsound @a
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -120.5 66.0 0.5
tp @a[tag=gen.viewer] -120.5 66.0 0.5 -90 0
