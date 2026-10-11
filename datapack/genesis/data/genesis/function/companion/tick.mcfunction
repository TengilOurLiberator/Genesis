execute unless entity @a[tag=gen.human,distance=..96] run return 0
execute if score #cmode gen matches 1 unless entity @a[tag=gen.human,distance=..40] at @p[tag=gen.human] positioned ~1.5 ~ ~1.5 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~
execute if score #cmode gen matches 1 unless entity @a[tag=gen.human,distance=..3.6] facing entity @p[tag=gen.human] feet rotated ~ 0 positioned ^ ^ ^0.2 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~ ~ ~
execute if score #cmode gen matches 1 if entity @a[tag=gen.human,distance=..3.6] run rotate @s facing entity @p[tag=gen.human] eyes
execute if score #cmode gen matches 2 unless entity @e[type=minecraft:marker,tag=gen.target,distance=..1.7] facing entity @e[type=minecraft:marker,tag=gen.target,limit=1] feet rotated ~ 0 positioned ^ ^ ^0.2 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~ ~ ~
execute if score #cmode gen matches 2 if entity @e[type=minecraft:marker,tag=gen.target,distance=..1.7] run function genesis:companion/arrive
execute if score #cmode gen matches 0 if entity @a[tag=gen.human,distance=..12] run rotate @s facing entity @p[tag=gen.human] eyes
