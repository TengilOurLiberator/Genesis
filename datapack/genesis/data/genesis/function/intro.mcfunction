scoreboard players add #t gen 1
function genesis:timeline
execute at @e[type=minecraft:marker,tag=gen.cam,limit=1] run tp @a[tag=gen.viewer] ~ ~ ~
