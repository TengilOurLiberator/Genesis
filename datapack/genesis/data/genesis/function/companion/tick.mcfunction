execute unless entity @a[tag=gen.human,distance=..64] run return 0
execute unless entity @a[tag=gen.human,distance=..40] at @p[tag=gen.human] positioned ~1.5 ~ ~1.5 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~
execute unless entity @a[tag=gen.human,distance=..4.5] facing entity @p[tag=gen.human] feet rotated ~ 0 positioned ^ ^ ^0.19 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~
rotate @s facing entity @p[tag=gen.human] eyes
